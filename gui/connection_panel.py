"""
Connection panel for DLP6500 (USB).
Shows connection status indicator and connect/disconnect buttons.
DCS connection is handled by the DCS panel directly.
"""

import threading
import customtkinter as ctk

from gui.i18n import t, add_listener


class ConnectionPanel(ctk.CTkFrame):
    """Top panel showing connection status for DLP device."""

    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, **kwargs)

        self._app = app_controller

        self.configure(corner_radius=8)

        # Track connection state for language refresh
        self._dlp_is_connected = False

        # Title
        self._title = ctk.CTkLabel(self, text=t("device_connections"),
                              font=ctk.CTkFont(size=14, weight="bold"))
        self._title.grid(row=0, column=0, columnspan=6, padx=10, pady=(8, 4), sticky="w")

        # =====================================================================
        # DLP6500 (USB) section
        # =====================================================================
        self._dlp_label = ctk.CTkLabel(self, text=t("dlp_usb"),
                                  font=ctk.CTkFont(size=12, weight="bold"))
        self._dlp_label.grid(row=1, column=0, padx=(10, 5), pady=4, sticky="w")

        self.dlp_indicator = ctk.CTkLabel(self, text="  ", width=18, height=18,
                                           corner_radius=9, fg_color="#AA0000")
        self.dlp_indicator.grid(row=1, column=1, padx=2, pady=4)

        self.dlp_status_label = ctk.CTkLabel(self, text=t("disconnected"), text_color="gray")
        self.dlp_status_label.grid(row=1, column=2, padx=(2, 10), pady=4, sticky="w")

        self.dlp_connect_btn = ctk.CTkButton(self, text=t("connect"), width=80,
                                              command=self._connect_dlp)
        self.dlp_connect_btn.grid(row=1, column=3, padx=2, pady=4)

        self.dlp_disconnect_btn = ctk.CTkButton(self, text=t("disconnect"), width=80,
                                                 fg_color="#555555",
                                                 command=self._disconnect_dlp,
                                                 state="disabled")
        self.dlp_disconnect_btn.grid(row=1, column=4, padx=(2, 10), pady=4)

        # Register for language changes
        add_listener(self._refresh_language)

    def _refresh_language(self):
        """Update all translatable text."""
        self._title.configure(text=t("device_connections"))
        self._dlp_label.configure(text=t("dlp_usb"))

        if self._dlp_is_connected:
            self.dlp_status_label.configure(text=t("connected"))
        else:
            self.dlp_status_label.configure(text=t("disconnected"))

        self.dlp_connect_btn.configure(text=t("connect"))
        self.dlp_disconnect_btn.configure(text=t("disconnect"))

    # =========================================================================
    # DLP connection
    # =========================================================================
    def _connect_dlp(self):
        self.dlp_connect_btn.configure(state="disabled", text=t("connecting"))
        self._app.log(t("dlp_connecting"))

        def task():
            try:
                self._app.connect_dlp()
                self.after(0, self._on_dlp_connected)
            except Exception as e:
                msg = str(e)
                self.after(0, lambda: self._on_dlp_error(msg))

        threading.Thread(target=task, daemon=True).start()

    def _on_dlp_connected(self):
        self._dlp_is_connected = True
        self.dlp_indicator.configure(fg_color="#00AA00")
        self.dlp_status_label.configure(text=t("connected"), text_color="#00CC00")
        self.dlp_connect_btn.configure(state="disabled", text=t("connect"))
        self.dlp_disconnect_btn.configure(state="normal")
        self._app.log(t("dlp_connected"))

    def _on_dlp_error(self, error_msg: str):
        self._dlp_is_connected = False
        self.dlp_indicator.configure(fg_color="#AA0000")
        self.dlp_status_label.configure(text=t("error"), text_color="#CC0000")
        self.dlp_connect_btn.configure(state="normal", text=t("connect"))
        self._app.log(t("dlp_error").format(error_msg))

    def _disconnect_dlp(self):
        try:
            self._app.disconnect_dlp()
        except Exception:
            pass
        self._dlp_is_connected = False
        self.dlp_indicator.configure(fg_color="#AA0000")
        self.dlp_status_label.configure(text=t("disconnected"), text_color="gray")
        self.dlp_connect_btn.configure(state="normal", text=t("connect"))
        self.dlp_disconnect_btn.configure(state="disabled")
        self._app.log(t("dlp_disconnected"))
