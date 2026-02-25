"""
DCS Controller panel.
Intensity slider, mode selector (Off/Continuous/Strobe), channel selection.
"""

import customtkinter as ctk

from gui.i18n import t, add_listener


class DCSPanel(ctk.CTkFrame):
    """DCS light controller panel."""

    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, **kwargs)

        self._app = app_controller

        self.configure(corner_radius=8)

        # Title
        self._title = ctk.CTkLabel(self, text=t("dcs_light_control"),
                              font=ctk.CTkFont(size=14, weight="bold"))
        self._title.grid(row=0, column=0, columnspan=2, padx=10, pady=(8, 4), sticky="w")

        # =====================================================================
        # Channel selector
        # =====================================================================
        self._ch_label = ctk.CTkLabel(self, text=t("channel"))
        self._ch_label.grid(row=1, column=0, padx=(10, 5), pady=4, sticky="w")

        self.channel_var = ctk.StringVar(value="CHANNEL1")
        self.channel_menu = ctk.CTkOptionMenu(
            self, values=["CHANNEL1", "CHANNEL2", "CHANNEL3"],
            variable=self.channel_var, width=140,
            command=self._on_channel_changed
        )
        self.channel_menu.grid(row=1, column=1, padx=(5, 10), pady=4, sticky="w")

        # =====================================================================
        # Mode selector
        # =====================================================================
        self._mode_label = ctk.CTkLabel(self, text=t("mode"))
        self._mode_label.grid(row=2, column=0, padx=(10, 5), pady=4, sticky="w")

        self.mode_var = ctk.StringVar(value="Off")
        self.mode_selector = ctk.CTkSegmentedButton(
            self, values=["Off", "Continuous", "Strobe"],
            variable=self.mode_var,
            command=self._on_mode_changed
        )
        self.mode_selector.grid(row=2, column=1, padx=(5, 10), pady=4, sticky="ew")

        # =====================================================================
        # Intensity slider
        # =====================================================================
        self._intensity_label = ctk.CTkLabel(self, text=t("intensity"))
        self._intensity_label.grid(row=3, column=0, padx=(10, 5), pady=4, sticky="w")

        slider_frame = ctk.CTkFrame(self, fg_color="transparent")
        slider_frame.grid(row=3, column=1, padx=(5, 10), pady=4, sticky="ew")

        self.intensity_slider = ctk.CTkSlider(
            slider_frame, from_=0, to=100,
            number_of_steps=100,
            command=self._on_slider_changed
        )
        self.intensity_slider.set(0)
        self.intensity_slider.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.intensity_value_label = ctk.CTkLabel(slider_frame, text="0%", width=45,
                                             font=ctk.CTkFont(size=13, weight="bold"))
        self.intensity_value_label.pack(side="right")

        # =====================================================================
        # Intensity entry (exact value)
        # =====================================================================
        self._exact_label = ctk.CTkLabel(self, text=t("exact_value"))
        self._exact_label.grid(row=4, column=0, padx=(10, 5), pady=4, sticky="w")

        exact_frame = ctk.CTkFrame(self, fg_color="transparent")
        exact_frame.grid(row=4, column=1, padx=(5, 10), pady=4, sticky="w")

        self.intensity_entry = ctk.CTkEntry(exact_frame, width=70, placeholder_text="0")
        self.intensity_entry.pack(side="left", padx=(0, 5))
        self.intensity_entry.insert(0, "0")

        self._set_btn = ctk.CTkButton(exact_frame, text=t("set_value"), width=80,
                                 command=self._set_exact_intensity)
        self._set_btn.pack(side="left")

        # =====================================================================
        # Apply button
        # =====================================================================
        self.apply_btn = ctk.CTkButton(self, text=t("apply_settings"),
                                        fg_color="#2d6a4f",
                                        command=self._apply_settings)
        self.apply_btn.grid(row=5, column=0, columnspan=2,
                             padx=10, pady=(8, 4), sticky="ew")

        # Quick buttons
        quick_frame = ctk.CTkFrame(self, fg_color="transparent")
        quick_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=(4, 8), sticky="ew")

        self.on_btn = ctk.CTkButton(quick_frame, text=t("turn_on"),
                                     fg_color="#1b4332", width=100,
                                     command=self._quick_on)
        self.on_btn.pack(side="left", padx=(0, 5), expand=True, fill="x")

        self.off_btn = ctk.CTkButton(quick_frame, text=t("turn_off"),
                                      fg_color="#6c1010", width=100,
                                      command=self._quick_off)
        self.off_btn.pack(side="left", padx=(5, 0), expand=True, fill="x")

        # Status
        self.status_label = ctk.CTkLabel(self, text="", text_color="gray",
                                          font=ctk.CTkFont(size=10))
        self.status_label.grid(row=7, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="w")

        # Configure grid weights
        self.grid_columnconfigure(1, weight=1)

        # Register for language changes
        add_listener(self._refresh_language)

    def _refresh_language(self):
        """Update all translatable text."""
        self._title.configure(text=t("dcs_light_control"))
        self._ch_label.configure(text=t("channel"))
        self._mode_label.configure(text=t("mode"))
        self._intensity_label.configure(text=t("intensity"))
        self._exact_label.configure(text=t("exact_value"))
        self._set_btn.configure(text=t("set_value"))
        self.apply_btn.configure(text=t("apply_settings"))
        self.on_btn.configure(text=t("turn_on"))
        self.off_btn.configure(text=t("turn_off"))

    def _on_channel_changed(self, value: str):
        """Update DCS controller channel."""
        if self._app.dcs is not None:
            self._app.dcs.channel = value
            self._app.log(t("dcs_channel_changed").format(value))

    def _on_mode_changed(self, value: str):
        """Handle mode change from segmented button."""
        pass  # Applied only when "Apply" button pressed

    def _on_slider_changed(self, value: float):
        """Update intensity label when slider moves."""
        self.intensity_value_label.configure(text=f"{int(value)}%")
        self.intensity_entry.delete(0, "end")
        self.intensity_entry.insert(0, str(int(value)))

    def _set_exact_intensity(self):
        """Set intensity from entry field."""
        try:
            val = float(self.intensity_entry.get())
            val = max(0, min(100, val))
            self.intensity_slider.set(val)
            self.intensity_value_label.configure(text=f"{int(val)}%")

            if self._app.dcs_connected:
                self._app.dcs.set_intensity_percent(val)
                self._app.log(t("dcs_intensity").format(val))
        except ValueError:
            self._app.log(t("err_intensity_number"))

    def _apply_settings(self):
        """Apply all DCS settings."""
        if not self._app.dcs_connected:
            self._app.log(t("err_dcs_not_connected"))
            return

        try:
            # Set mode
            mode_name = self.mode_var.get()
            self._app.dcs.set_mode_by_name(mode_name)

            # Set intensity
            intensity = self.intensity_slider.get()
            self._app.dcs.set_intensity_percent(intensity)

            self.status_label.configure(
                text=t("applied_settings").format(mode_name, int(intensity)),
                text_color="#00CC00"
            )
            self._app.log(t("dcs_settings_applied").format(mode_name, int(intensity)))
        except Exception as e:
            self.status_label.configure(text=f"{t('error')}: {e}", text_color="#CC0000")
            self._app.log(t("dcs_error_generic").format(e))

    def _quick_on(self):
        """Quick turn on at 100%."""
        if not self._app.dcs_connected:
            self._app.log(t("err_dcs_not_connected"))
            return

        try:
            self._app.dcs.set_intensity_percent(100)
            self._app.dcs.set_mode(self._app.dcs.MODE_CONTINUOUS)
            self.intensity_slider.set(100)
            self.intensity_value_label.configure(text="100%")
            self.intensity_entry.delete(0, "end")
            self.intensity_entry.insert(0, "100")
            self.mode_var.set("Continuous")
            self.status_label.configure(text=t("turned_on"), text_color="#00CC00")
            self._app.log(t("dcs_light_on"))
        except Exception as e:
            self._app.log(t("dcs_error_generic").format(e))

    def _quick_off(self):
        """Quick turn off."""
        if not self._app.dcs_connected:
            self._app.log(t("err_dcs_not_connected"))
            return

        try:
            self._app.dcs.turn_off()
            self.mode_var.set("Off")
            self.status_label.configure(text=t("turned_off"), text_color="gray")
            self._app.log(t("dcs_light_off"))
        except Exception as e:
            self._app.log(t("dcs_error_generic").format(e))
