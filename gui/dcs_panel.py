"""
DCS-100E/103E Controller panel.
Matches the DCS control application layout with connection bar,
profile management, and 3-channel control (slider, mode, pulse, trigger).
"""

import threading
import customtkinter as ctk

from gui.i18n import t, add_listener


class _ChannelColumn(ctk.CTkFrame):
    """Single channel control column with slider, mode, pulse, and trigger settings."""

    MAX_CURRENT_MA = 400

    def __init__(self, master, channel_index: int, app_controller, **kwargs):
        super().__init__(master, **kwargs)

        self._app = app_controller
        self._ch_index = channel_index
        self._ch_name = f"CHANNEL{channel_index + 1}"

        self.configure(corner_radius=6, border_width=1, border_color="#555555")

        # --- Channel label ---
        self._ch_label = ctk.CTkLabel(
            self, text=t("dcs_channel_n").format(channel_index + 1),
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self._ch_label.pack(pady=(8, 4))

        # --- Slider (vertical) ---
        slider_frame = ctk.CTkFrame(self, fg_color="transparent")
        slider_frame.pack(fill="x", padx=8, pady=(2, 2))

        self.current_slider = ctk.CTkSlider(
            slider_frame, from_=0, to=self.MAX_CURRENT_MA,
            orientation="vertical", height=120,
            number_of_steps=self.MAX_CURRENT_MA,
            command=self._on_slider_changed
        )
        self.current_slider.set(0)
        self.current_slider.pack(pady=(2, 2))

        # --- mA value label ---
        self.ma_label = ctk.CTkLabel(
            self, text="0 mA",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.ma_label.pack(pady=(0, 6))

        # --- Mode dropdown ---
        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.pack(fill="x", padx=8, pady=2)

        self._mode_lbl = ctk.CTkLabel(mode_frame, text=t("mode"),
                                       font=ctk.CTkFont(size=11))
        self._mode_lbl.pack(side="left", padx=(0, 4))

        self.mode_var = ctk.StringVar(value="Off")
        self.mode_menu = ctk.CTkOptionMenu(
            mode_frame, values=["Off", "Continuous", "Pulsed", "Gated"],
            variable=self.mode_var, width=110, height=26,
            font=ctk.CTkFont(size=11),
            command=self._on_mode_changed
        )
        self.mode_menu.pack(side="left", fill="x", expand=True)

        # --- Pulse Width ---
        pw_frame = ctk.CTkFrame(self, fg_color="transparent")
        pw_frame.pack(fill="x", padx=8, pady=2)

        self._pw_lbl = ctk.CTkLabel(pw_frame, text=t("dcs_pulse_width"),
                                     font=ctk.CTkFont(size=11))
        self._pw_lbl.pack(side="left", padx=(0, 4))

        self.pulse_width_entry = ctk.CTkEntry(pw_frame, width=70, height=26,
                                               font=ctk.CTkFont(size=11),
                                               placeholder_text="0")
        self.pulse_width_entry.pack(side="right")
        self.pulse_width_entry.insert(0, "0")

        # --- Pulse Delay ---
        pd_frame = ctk.CTkFrame(self, fg_color="transparent")
        pd_frame.pack(fill="x", padx=8, pady=2)

        self._pd_lbl = ctk.CTkLabel(pd_frame, text=t("dcs_pulse_delay"),
                                     font=ctk.CTkFont(size=11))
        self._pd_lbl.pack(side="left", padx=(0, 4))

        self.pulse_delay_entry = ctk.CTkEntry(pd_frame, width=70, height=26,
                                               font=ctk.CTkFont(size=11),
                                               placeholder_text="0")
        self.pulse_delay_entry.pack(side="right")
        self.pulse_delay_entry.insert(0, "0")

        # --- Trigger edge (Rising / Falling) ---
        trigger_frame = ctk.CTkFrame(self, fg_color="transparent")
        trigger_frame.pack(fill="x", padx=8, pady=(4, 2))

        self.trigger_edge_var = ctk.StringVar(value="Rising")

        self.rising_rb = ctk.CTkRadioButton(
            trigger_frame, text=t("dcs_rising"), variable=self.trigger_edge_var,
            value="Rising", font=ctk.CTkFont(size=11),
            radiobutton_width=16, radiobutton_height=16
        )
        self.rising_rb.pack(side="left", padx=(0, 8))

        self.falling_rb = ctk.CTkRadioButton(
            trigger_frame, text=t("dcs_falling"), variable=self.trigger_edge_var,
            value="Falling", font=ctk.CTkFont(size=11),
            radiobutton_width=16, radiobutton_height=16
        )
        self.falling_rb.pack(side="left")

        # --- Trigger Input ---
        ti_frame = ctk.CTkFrame(self, fg_color="transparent")
        ti_frame.pack(fill="x", padx=8, pady=2)

        self._ti_lbl = ctk.CTkLabel(ti_frame, text=t("dcs_trigger_input"),
                                     font=ctk.CTkFont(size=11))
        self._ti_lbl.pack(side="left", padx=(0, 4))

        self.trigger_input_entry = ctk.CTkEntry(ti_frame, width=50, height=26,
                                                 font=ctk.CTkFont(size=11),
                                                 placeholder_text="0")
        self.trigger_input_entry.pack(side="right")
        self.trigger_input_entry.insert(0, "0")

        # --- Frequency display ---
        self.freq_label = ctk.CTkLabel(
            self, text="2000.0 Hz Max",
            font=ctk.CTkFont(size=11), text_color="gray"
        )
        self.freq_label.pack(pady=(4, 4))

        # --- Pulse button ---
        self.pulse_btn = ctk.CTkButton(
            self, text=t("dcs_pulse"), width=90, height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2d6a4f", hover_color="#1b4332",
            command=self._on_pulse
        )
        self.pulse_btn.pack(pady=(2, 8))

    # -----------------------------------------------------------------
    def _on_slider_changed(self, value: float):
        """Update mA label and send level to controller."""
        ma = int(value)
        self.ma_label.configure(text=f"{ma} mA")
        if self._app.dcs_connected:
            try:
                self._app.dcs.set_level(ma, self._ch_name)
            except Exception as e:
                self._app.log(t("dcs_error_generic").format(e))

    def _on_mode_changed(self, value: str):
        """Send mode change to controller."""
        if self._app.dcs_connected:
            try:
                self._app.dcs.set_mode_by_name(value, self._ch_name)
                self._app.log(t("dcs_mode_set").format(self._ch_index + 1, value))
            except Exception as e:
                self._app.log(t("dcs_error_generic").format(e))

    def _on_pulse(self):
        """Send pulse command and apply pulse settings."""
        if not self._app.dcs_connected:
            self._app.log(t("err_dcs_not_connected"))
            return
        try:
            # Apply pulse width
            pw = int(self.pulse_width_entry.get())
            self._app.dcs.set_pulse_width(pw, self._ch_name)

            # Apply pulse delay
            pd = int(self.pulse_delay_entry.get())
            self._app.dcs.set_pulse_delay(pd, self._ch_name)

            # Apply trigger edge
            rising = self.trigger_edge_var.get() == "Rising"
            self._app.dcs.set_trigger_edge(rising, self._ch_name)

            # Apply trigger input
            ti = int(self.trigger_input_entry.get())
            self._app.dcs.set_trigger_input(ti, self._ch_name)

            # Fire pulse
            self._app.dcs.pulse(self._ch_name)
            self._app.log(t("dcs_pulse_sent").format(self._ch_index + 1))
        except ValueError:
            self._app.log(t("dcs_err_pulse_values"))
        except Exception as e:
            self._app.log(t("dcs_error_generic").format(e))

    def get_current_ma(self) -> int:
        """Return slider value in mA."""
        return int(self.current_slider.get())

    def get_mode_name(self) -> str:
        """Return selected mode name."""
        return self.mode_var.get()

    def refresh_language(self):
        """Update translatable text."""
        self._ch_label.configure(text=t("dcs_channel_n").format(self._ch_index + 1))
        self._mode_lbl.configure(text=t("mode"))
        self._pw_lbl.configure(text=t("dcs_pulse_width"))
        self._pd_lbl.configure(text=t("dcs_pulse_delay"))
        self.rising_rb.configure(text=t("dcs_rising"))
        self.falling_rb.configure(text=t("dcs_falling"))
        self._ti_lbl.configure(text=t("dcs_trigger_input"))
        self.pulse_btn.configure(text=t("dcs_pulse"))


class DCSPanel(ctk.CTkFrame):
    """DCS-100E/103E controller panel with connection, profile, and 3-channel control."""

    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, **kwargs)

        self._app = app_controller

        self.configure(corner_radius=8)

        # =====================================================================
        # Title
        # =====================================================================
        self._title = ctk.CTkLabel(
            self, text=t("dcs_panel_title"),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self._title.pack(anchor="w", padx=10, pady=(8, 4))

        # =====================================================================
        # Connection bar
        # =====================================================================
        conn_frame = ctk.CTkFrame(self, fg_color="transparent")
        conn_frame.pack(fill="x", padx=10, pady=(2, 6))

        # Devices label + dropdown
        self._dev_label = ctk.CTkLabel(conn_frame, text=t("dcs_devices"),
                                        font=ctk.CTkFont(size=11))
        self._dev_label.pack(side="left", padx=(0, 4))

        self.device_var = ctk.StringVar(value="192.168.0.1")
        self.device_menu = ctk.CTkOptionMenu(
            conn_frame, values=["192.168.0.1"],
            variable=self.device_var, width=140, height=28,
            font=ctk.CTkFont(size=11)
        )
        self.device_menu.pack(side="left", padx=(0, 6))

        # Connect button
        self.connect_btn = ctk.CTkButton(
            conn_frame, text=t("connect"), width=80, height=28,
            font=ctk.CTkFont(size=11),
            command=self._connect_dcs
        )
        self.connect_btn.pack(side="left", padx=(0, 6))

        # Status label
        self.conn_status_label = ctk.CTkLabel(
            conn_frame, text=t("disconnected"),
            font=ctk.CTkFont(size=11), text_color="gray"
        )
        self.conn_status_label.pack(side="left", padx=(0, 12))

        # Separator
        sep = ctk.CTkFrame(conn_frame, width=2, height=22, fg_color="gray40")
        sep.pack(side="left", padx=(0, 12))

        # Profile label + dropdown
        self._profile_label = ctk.CTkLabel(conn_frame, text=t("dcs_profile"),
                                            font=ctk.CTkFont(size=11))
        self._profile_label.pack(side="left", padx=(0, 4))

        self.profile_var = ctk.StringVar(value="0")
        self.profile_menu = ctk.CTkOptionMenu(
            conn_frame, values=["0", "1", "2", "3", "4"],
            variable=self.profile_var, width=60, height=28,
            font=ctk.CTkFont(size=11)
        )
        self.profile_menu.pack(side="left", padx=(0, 6))

        # Save button
        self.save_btn = ctk.CTkButton(
            conn_frame, text=t("dcs_save"), width=60, height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#2d6a4f", hover_color="#1b4332",
            command=self._save_profile
        )
        self.save_btn.pack(side="left", padx=(0, 4))

        # Load button
        self.load_btn = ctk.CTkButton(
            conn_frame, text=t("dcs_load"), width=60, height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#2d6a4f", hover_color="#1b4332",
            command=self._load_profile
        )
        self.load_btn.pack(side="left")

        # =====================================================================
        # Channel Control title
        # =====================================================================
        self._ch_ctrl_title = ctk.CTkLabel(
            self, text=t("dcs_channel_control"),
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self._ch_ctrl_title.pack(anchor="w", padx=10, pady=(4, 4))

        # =====================================================================
        # 3 Channel columns
        # =====================================================================
        channels_frame = ctk.CTkFrame(self, fg_color="transparent")
        channels_frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        self.channel_cols = []
        for i in range(3):
            col = _ChannelColumn(channels_frame, channel_index=i,
                                 app_controller=app_controller)
            col.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 4, 0))
            self.channel_cols.append(col)

        channels_frame.grid_columnconfigure(0, weight=1)
        channels_frame.grid_columnconfigure(1, weight=1)
        channels_frame.grid_columnconfigure(2, weight=1)
        channels_frame.grid_rowconfigure(0, weight=1)

        # Track connection state
        self._dcs_is_connected = False

        # Register for language changes
        add_listener(self._refresh_language)

    # =====================================================================
    # Language refresh
    # =====================================================================
    def _refresh_language(self):
        """Update all translatable text."""
        self._title.configure(text=t("dcs_panel_title"))
        self._dev_label.configure(text=t("dcs_devices"))
        self.connect_btn.configure(
            text=t("disconnect") if self._dcs_is_connected else t("connect")
        )
        if self._dcs_is_connected:
            self.conn_status_label.configure(text=t("dcs_success"))
        else:
            self.conn_status_label.configure(text=t("disconnected"))
        self._profile_label.configure(text=t("dcs_profile"))
        self.save_btn.configure(text=t("dcs_save"))
        self.load_btn.configure(text=t("dcs_load"))
        self._ch_ctrl_title.configure(text=t("dcs_channel_control"))
        for col in self.channel_cols:
            col.refresh_language()

    # =====================================================================
    # Connection
    # =====================================================================
    def _connect_dcs(self):
        """Connect or disconnect from DCS controller."""
        if self._dcs_is_connected:
            self._disconnect_dcs()
            return

        ip = self.device_var.get().strip()
        if not ip:
            self._app.log(t("err_no_ip"))
            return

        self.connect_btn.configure(state="disabled", text=t("connecting"))
        self._app.log(t("dcs_connecting").format(ip, 7777))

        def task():
            try:
                self._app.connect_dcs(ip, 7777)
                self.after(0, self._on_connected)
            except Exception as e:
                msg = str(e)
                self.after(0, lambda: self._on_error(msg))

        threading.Thread(target=task, daemon=True).start()

    def _on_connected(self):
        self._dcs_is_connected = True
        self.conn_status_label.configure(text=t("dcs_success"), text_color="#00CC00")
        self.connect_btn.configure(state="normal", text=t("disconnect"))
        self._app.log(t("dcs_connected"))

    def _on_error(self, error_msg: str):
        self._dcs_is_connected = False
        self.conn_status_label.configure(text=t("error"), text_color="#CC0000")
        self.connect_btn.configure(state="normal", text=t("connect"))
        self._app.log(t("dcs_error").format(error_msg))

    def _disconnect_dcs(self):
        try:
            self._app.disconnect_dcs()
        except Exception:
            pass
        self._dcs_is_connected = False
        self.conn_status_label.configure(text=t("disconnected"), text_color="gray")
        self.connect_btn.configure(state="normal", text=t("connect"))
        self._app.log(t("dcs_disconnected"))

    # =====================================================================
    # Profile
    # =====================================================================
    def _save_profile(self):
        if not self._app.dcs_connected:
            self._app.log(t("err_dcs_not_connected"))
            return
        try:
            pid = int(self.profile_var.get())
            self._app.dcs.save_profile(pid)
            self._app.log(t("dcs_profile_saved").format(pid))
        except Exception as e:
            self._app.log(t("dcs_error_generic").format(e))

    def _load_profile(self):
        if not self._app.dcs_connected:
            self._app.log(t("err_dcs_not_connected"))
            return
        try:
            pid = int(self.profile_var.get())
            self._app.dcs.load_profile(pid)
            self._app.log(t("dcs_profile_loaded").format(pid))
        except Exception as e:
            self._app.log(t("dcs_error_generic").format(e))

    # =====================================================================
    # Public helpers (used by project_panel)
    # =====================================================================
    def get_channel_settings(self, channel_index: int = 0):
        """Return (mode_name, current_ma) for given channel column."""
        col = self.channel_cols[channel_index]
        return col.get_mode_name(), col.get_current_ma()
