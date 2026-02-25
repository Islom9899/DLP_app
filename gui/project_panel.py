"""
Project control panel with synchronization logic.
Start Project: DCS light ON -> DLP projection START
Stop Project:  DLP projection STOP -> DCS light OFF
"""

import time
import threading
import customtkinter as ctk

from gui.i18n import t, add_listener


class ProjectPanel(ctk.CTkFrame):
    """Synchronization control panel."""

    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, **kwargs)

        self._app = app_controller
        self._running = False
        self._thread = None

        self.configure(corner_radius=8)

        # Title
        self._title = ctk.CTkLabel(self, text=t("project_control"),
                              font=ctk.CTkFont(size=14, weight="bold"))
        self._title.grid(row=0, column=0, columnspan=3, padx=10, pady=(8, 4), sticky="w")

        # Description
        self._desc = ctk.CTkLabel(
            self,
            text=t("project_desc"),
            text_color="gray", font=ctk.CTkFont(size=11),
            wraplength=500
        )
        self._desc.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 4), sticky="w")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=(4, 4), sticky="ew")

        self.start_btn = ctk.CTkButton(
            btn_frame, text=t("start_project"),
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2d8a4e", hover_color="#1b6b37",
            height=45,
            command=self._start_project
        )
        self.start_btn.pack(side="left", padx=(0, 10), expand=True, fill="x")

        self.stop_btn = ctk.CTkButton(
            btn_frame, text=t("stop_project"),
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#8a2d2d", hover_color="#6b1b1b",
            height=45,
            state="disabled",
            command=self._stop_project
        )
        self.stop_btn.pack(side="left", expand=True, fill="x")

        # Status
        self.status_label = ctk.CTkLabel(
            self, text=t("ready"),
            font=ctk.CTkFont(size=12), text_color="gray"
        )
        self.status_label.grid(row=3, column=0, columnspan=3, padx=10, pady=(4, 8), sticky="w")

        # Register for language changes
        add_listener(self._refresh_language)

    def _refresh_language(self):
        """Update all translatable text."""
        self._title.configure(text=t("project_control"))
        self._desc.configure(text=t("project_desc"))
        self.start_btn.configure(text=t("start_project"))
        self.stop_btn.configure(text=t("stop_project"))
        if not self._running:
            self.status_label.configure(text=t("ready"))

    def _update_status(self, text: str, color: str = "gray"):
        """Thread-safe status update."""
        self.after(0, lambda: self.status_label.configure(text=text, text_color=color))

    def _start_project(self):
        """Start synchronized project sequence."""
        if self._running:
            return

        # Check connections
        if not self._app.dlp_connected and not self._app.dcs_connected:
            self._app.log(t("err_no_device"))
            return

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        self._thread = threading.Thread(target=self._run_sequence, daemon=True)
        self._thread.start()

    def _run_sequence(self):
        """Execute the start sequence in background thread."""
        self._running = True

        try:
            # Step 1: Activate DCS light source
            if self._app.dcs_connected:
                self._update_status(t("dcs_turning_on"), "#CCCC00")
                self._app.log(t("project_dcs_on"))

                mode_name = "Continuous"
                # Get current settings from DCS panel if available
                try:
                    dcs_panel = self._app.dcs_panel
                    mode_name = dcs_panel.mode_var.get()
                    intensity = dcs_panel.intensity_slider.get()
                    if mode_name == "Off":
                        mode_name = "Continuous"
                    self._app.dcs.set_intensity_percent(intensity)
                except Exception:
                    self._app.dcs.set_intensity_percent(100)

                self._app.dcs.set_mode_by_name(mode_name)

                # Wait for light to stabilize
                time.sleep(0.1)
                self._app.log(t("dcs_light_activated").format(mode_name))

            # Step 2: Start DLP pattern sequence
            if self._app.dlp_connected:
                self._update_status(t("dlp_starting"), "#CCCC00")
                self._app.log(t("project_dlp_start"))

                self._app.dlp.start_stop_sequence('start')
                self._app.log(t("dlp_projection_started"))

            self._update_status(t("project_running"), "#00CC00")
            self._app.log(t("project_started"))

        except Exception as e:
            self._update_status(f"{t('error')}: {e}", "#CC0000")
            self._app.log(t("project_error").format(e))
            self._running = False
            self.after(0, lambda: self.start_btn.configure(state="normal"))
            self.after(0, lambda: self.stop_btn.configure(state="disabled"))

    def _stop_project(self):
        """Stop synchronized project sequence."""
        if not self._running:
            return

        self._update_status(t("stopping"), "#CCCC00")
        self._app.log(t("project_stopping"))

        try:
            # Step 1: Stop DLP first
            if self._app.dlp_connected:
                self._app.dlp.start_stop_sequence('stop')
                self._app.log(t("dlp_projection_stopped"))

            # Step 2: Turn off DCS
            if self._app.dcs_connected:
                self._app.dcs.turn_off()
                self._app.log(t("dcs_light_turned_off"))

            self._running = False
            self._update_status(t("stopped"), "gray")
            self._app.log(t("project_stopped"))

        except Exception as e:
            self._app.log(t("stop_error").format(e))

        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
