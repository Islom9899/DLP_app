"""
Connection panel for DLP6500 (USB) and DCS Controller (Ethernet).
Shows connection status indicators and connect/disconnect buttons.
"""

import threading
import customtkinter as ctk


class ConnectionPanel(ctk.CTkFrame):
    """Top panel showing connection status for both devices."""

    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, **kwargs)

        self._app = app_controller

        self.configure(corner_radius=8)

        # Title
        title = ctk.CTkLabel(self, text="Qurilma Ulanishlari",
                              font=ctk.CTkFont(size=14, weight="bold"))
        title.grid(row=0, column=0, columnspan=6, padx=10, pady=(8, 4), sticky="w")

        # =====================================================================
        # DLP6500 (USB) section
        # =====================================================================
        dlp_label = ctk.CTkLabel(self, text="DLP6500 (USB):",
                                  font=ctk.CTkFont(size=12, weight="bold"))
        dlp_label.grid(row=1, column=0, padx=(10, 5), pady=4, sticky="w")

        self.dlp_indicator = ctk.CTkLabel(self, text="  ", width=18, height=18,
                                           corner_radius=9, fg_color="#AA0000")
        self.dlp_indicator.grid(row=1, column=1, padx=2, pady=4)

        self.dlp_status_label = ctk.CTkLabel(self, text="Ulanmagan", text_color="gray")
        self.dlp_status_label.grid(row=1, column=2, padx=(2, 10), pady=4, sticky="w")

        self.dlp_connect_btn = ctk.CTkButton(self, text="Ulash", width=80,
                                              command=self._connect_dlp)
        self.dlp_connect_btn.grid(row=1, column=3, padx=2, pady=4)

        self.dlp_disconnect_btn = ctk.CTkButton(self, text="Uzish", width=80,
                                                 fg_color="#555555",
                                                 command=self._disconnect_dlp,
                                                 state="disabled")
        self.dlp_disconnect_btn.grid(row=1, column=4, padx=(2, 20), pady=4)

        # Separator
        separator = ctk.CTkFrame(self, width=2, height=30, fg_color="gray40")
        separator.grid(row=1, column=5, padx=5, pady=4)

        # =====================================================================
        # DCS Controller (Ethernet) section
        # =====================================================================
        dcs_label = ctk.CTkLabel(self, text="DCS Controller (Ethernet):",
                                  font=ctk.CTkFont(size=12, weight="bold"))
        dcs_label.grid(row=1, column=6, padx=(10, 5), pady=4, sticky="w")

        self.dcs_indicator = ctk.CTkLabel(self, text="  ", width=18, height=18,
                                           corner_radius=9, fg_color="#AA0000")
        self.dcs_indicator.grid(row=1, column=7, padx=2, pady=4)

        self.dcs_status_label = ctk.CTkLabel(self, text="Ulanmagan", text_color="gray")
        self.dcs_status_label.grid(row=1, column=8, padx=(2, 5), pady=4, sticky="w")

        # IP and Port inputs
        ip_label = ctk.CTkLabel(self, text="IP:")
        ip_label.grid(row=2, column=6, padx=(10, 2), pady=2, sticky="e")

        self.ip_entry = ctk.CTkEntry(self, width=130, placeholder_text="192.168.1.100")
        self.ip_entry.grid(row=2, column=7, columnspan=2, padx=2, pady=2, sticky="w")
        self.ip_entry.insert(0, "192.168.1.100")

        port_label = ctk.CTkLabel(self, text="Port:")
        port_label.grid(row=2, column=9, padx=(5, 2), pady=2, sticky="e")

        self.port_entry = ctk.CTkEntry(self, width=70, placeholder_text="30303")
        self.port_entry.grid(row=2, column=10, padx=2, pady=2, sticky="w")
        self.port_entry.insert(0, "30303")

        self.dcs_connect_btn = ctk.CTkButton(self, text="Ulash", width=80,
                                              command=self._connect_dcs)
        self.dcs_connect_btn.grid(row=2, column=11, padx=2, pady=2)

        self.dcs_disconnect_btn = ctk.CTkButton(self, text="Uzish", width=80,
                                                 fg_color="#555555",
                                                 command=self._disconnect_dcs,
                                                 state="disabled")
        self.dcs_disconnect_btn.grid(row=2, column=12, padx=(2, 10), pady=2)

    # =========================================================================
    # DLP connection
    # =========================================================================
    def _connect_dlp(self):
        self.dlp_connect_btn.configure(state="disabled", text="Ulanmoqda...")
        self._app.log("DLP6500 ga ulanmoqda...")

        def task():
            try:
                self._app.connect_dlp()
                self.after(0, self._on_dlp_connected)
            except Exception as e:
                self.after(0, lambda: self._on_dlp_error(str(e)))

        threading.Thread(target=task, daemon=True).start()

    def _on_dlp_connected(self):
        self.dlp_indicator.configure(fg_color="#00AA00")
        self.dlp_status_label.configure(text="Ulangan", text_color="#00CC00")
        self.dlp_connect_btn.configure(state="disabled", text="Ulash")
        self.dlp_disconnect_btn.configure(state="normal")
        self._app.log("DLP6500 muvaffaqiyatli ulandi")

    def _on_dlp_error(self, error_msg: str):
        self.dlp_indicator.configure(fg_color="#AA0000")
        self.dlp_status_label.configure(text="Xato", text_color="#CC0000")
        self.dlp_connect_btn.configure(state="normal", text="Ulash")
        self._app.log(f"DLP6500 xato: {error_msg}")

    def _disconnect_dlp(self):
        try:
            self._app.disconnect_dlp()
        except Exception:
            pass
        self.dlp_indicator.configure(fg_color="#AA0000")
        self.dlp_status_label.configure(text="Ulanmagan", text_color="gray")
        self.dlp_connect_btn.configure(state="normal", text="Ulash")
        self.dlp_disconnect_btn.configure(state="disabled")
        self._app.log("DLP6500 uzildi")

    # =========================================================================
    # DCS connection
    # =========================================================================
    def _connect_dcs(self):
        ip = self.ip_entry.get().strip()
        port_str = self.port_entry.get().strip()

        if not ip:
            self._app.log("Xato: IP manzil kiritilmagan")
            return
        try:
            port = int(port_str)
        except ValueError:
            self._app.log("Xato: Port raqam bo'lishi kerak")
            return

        self.dcs_connect_btn.configure(state="disabled", text="Ulanmoqda...")
        self._app.log(f"DCS Controller ga ulanmoqda ({ip}:{port})...")

        def task():
            try:
                self._app.connect_dcs(ip, port)
                self.after(0, self._on_dcs_connected)
            except Exception as e:
                self.after(0, lambda: self._on_dcs_error(str(e)))

        threading.Thread(target=task, daemon=True).start()

    def _on_dcs_connected(self):
        self.dcs_indicator.configure(fg_color="#00AA00")
        self.dcs_status_label.configure(text="Ulangan", text_color="#00CC00")
        self.dcs_connect_btn.configure(state="disabled", text="Ulash")
        self.dcs_disconnect_btn.configure(state="normal")
        self._app.log("DCS Controller muvaffaqiyatli ulandi")

    def _on_dcs_error(self, error_msg: str):
        self.dcs_indicator.configure(fg_color="#AA0000")
        self.dcs_status_label.configure(text="Xato", text_color="#CC0000")
        self.dcs_connect_btn.configure(state="normal", text="Ulash")
        self._app.log(f"DCS Controller xato: {error_msg}")

    def _disconnect_dcs(self):
        try:
            self._app.disconnect_dcs()
        except Exception:
            pass
        self.dcs_indicator.configure(fg_color="#AA0000")
        self.dcs_status_label.configure(text="Ulanmagan", text_color="gray")
        self.dcs_connect_btn.configure(state="normal", text="Ulash")
        self.dcs_disconnect_btn.configure(state="disabled")
        self._app.log("DCS Controller uzildi")
