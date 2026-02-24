"""
Main application window.
Composes all GUI panels and manages device connections.
"""

import customtkinter as ctk

from drivers.dlp_driver import dlp6500, dlp9000, dlpc900_dmd
from drivers.dcs_controller import DCSController
from gui.connection_panel import ConnectionPanel
from gui.dlp_panel import DLPPanel
from gui.dcs_panel import DCSPanel
from gui.project_panel import ProjectPanel
from gui.status_bar import StatusBar


class DLPApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("DLP + DCS Controller")
        self.geometry("950x750")
        self.minsize(800, 600)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Device instances
        self.dlp = None
        self.dcs = None

        # =====================================================================
        # GUI Layout
        # =====================================================================

        # Connection panel (top)
        self.connection_panel = ConnectionPanel(self, app_controller=self)
        self.connection_panel.pack(fill="x", padx=10, pady=(10, 5))

        # Middle: two-column device controls
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.dlp_panel = DLPPanel(controls_frame, app_controller=self)
        self.dlp_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=0)

        self.dcs_panel = DCSPanel(controls_frame, app_controller=self)
        self.dcs_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)

        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(1, weight=1)
        controls_frame.grid_rowconfigure(0, weight=1)

        # Project panel (bottom)
        self.project_panel = ProjectPanel(self, app_controller=self)
        self.project_panel.pack(fill="x", padx=10, pady=(5, 5))

        # Status bar (very bottom)
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill="x", padx=10, pady=(0, 10))

        # Welcome message
        self.log("Ilova ishga tushdi. Qurilmalarni ulang.")

        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # =========================================================================
    # Properties
    # =========================================================================
    @property
    def dlp_connected(self) -> bool:
        return self.dlp is not None and self.dlp.initialized

    @property
    def dcs_connected(self) -> bool:
        return self.dcs is not None and self.dcs.connected

    # =========================================================================
    # Logging
    # =========================================================================
    def log(self, message: str):
        """Log message to status bar (thread-safe)."""
        self.after(0, lambda: self.status_bar.log(message))

    # =========================================================================
    # DLP connection
    # =========================================================================
    def connect_dlp(self):
        """Connect to DLP6500 via USB HID. Called from background thread."""
        # First detect DMD type
        temp_dmd = dlpc900_dmd(debug=False, initialize=True)
        dmd_type_info = temp_dmd.get_firmware_type()
        dmd_type = dmd_type_info.get('dmd type', 'unknown')
        del temp_dmd

        if dmd_type == "DLP6500":
            self.dlp = dlp6500(debug=False, initialize=True)
        elif dmd_type == "DLP9000":
            self.dlp = dlp9000(debug=False, initialize=True)
        else:
            self.dlp = dlp6500(debug=False, initialize=True)

        # Get firmware version for display
        fw = self.dlp.get_firmware_version()
        self.log(f"DMD turi: {dmd_type}, Firmware: {fw.get('app version', 'N/A')}")

    def disconnect_dlp(self):
        """Disconnect DLP6500."""
        if self.dlp is not None:
            try:
                self.dlp.start_stop_sequence('stop')
            except Exception:
                pass
            del self.dlp
            self.dlp = None

    # =========================================================================
    # DCS connection
    # =========================================================================
    def connect_dcs(self, ip: str, port: int):
        """Connect to DCS Controller via TCP. Called from background thread."""
        self.dcs = DCSController(ip_address=ip, port=port)
        success = self.dcs.connect()
        if not success:
            self.dcs = None
            raise ConnectionError(f"DCS ga ulanib bo'lmadi ({ip}:{port})")

    def disconnect_dcs(self):
        """Disconnect DCS Controller."""
        if self.dcs is not None:
            try:
                self.dcs.turn_off()
            except Exception:
                pass
            self.dcs.disconnect()
            self.dcs = None

    # =========================================================================
    # Cleanup
    # =========================================================================
    def _on_close(self):
        """Clean up resources before closing."""
        try:
            self.disconnect_dlp()
        except Exception:
            pass
        try:
            self.disconnect_dcs()
        except Exception:
            pass
        self.destroy()
