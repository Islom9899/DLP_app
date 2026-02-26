"""
Main application window.
Composes all GUI panels and manages device connections.
"""

import time
import customtkinter as ctk

from drivers.dlp_driver import dlp6500, dlp9000, dlpc900_dmd
from drivers.dcs_controller import DCSController
from gui.i18n import t, set_lang, get_lang, add_listener, LANGUAGES
from gui.connection_panel import ConnectionPanel
from gui.dlp_panel import DLPPanel
from gui.dcs_panel import DCSPanel
from gui.status_bar import StatusBar


class DLPApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title(t("app_title"))
        self.geometry("1100x850")
        self.minsize(900, 700)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Dark charcoal background
        self.configure(fg_color="#F0F8FF")

        # Device instances
        self.dlp = None
        self.dcs = None

        # =====================================================================
        # Language selector (top-right)
        # =====================================================================
        lang_frame = ctk.CTkFrame(self, fg_color="transparent")
        lang_frame.pack(fill="x", padx=10, pady=(6, 0))

        self._lang_label = ctk.CTkLabel(lang_frame, text=t("language") + ":",
                                         font=ctk.CTkFont(size=12))
        self._lang_label.pack(side="right", padx=(5, 0))

        # Determine current display name
        current_display = "English"
        for name, code in LANGUAGES.items():
            if code == get_lang():
                current_display = name
                break

        self._lang_var = ctk.StringVar(value=current_display)
        self._lang_menu = ctk.CTkOptionMenu(
            lang_frame,
            values=list(LANGUAGES.keys()),
            variable=self._lang_var,
            width=100,
            command=self._on_language_changed
        )
        self._lang_menu.pack(side="right", padx=(0, 5))

        # =====================================================================
        # Scrollable main content area
        # =====================================================================
        main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_scroll.pack(fill="both", expand=True, padx=10, pady=5)

        # Connection panel (DLP only, top)
        self.connection_panel = ConnectionPanel(main_scroll, app_controller=self)
        self.connection_panel.pack(fill="x", pady=(0, 5))

        # DLP panel (full width)
        self.dlp_panel = DLPPanel(main_scroll, app_controller=self)
        self.dlp_panel.pack(fill="x", pady=(0, 5))

        # DCS panel (full width — 3-channel layout with embedded connection)
        self.dcs_panel = DCSPanel(main_scroll, app_controller=self)
        self.dcs_panel.pack(fill="x", pady=(0, 5))

        # Status bar (very bottom, outside scroll)
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill="x", padx=10, pady=(0, 10))

        # Welcome message
        self.log(t("app_started"))

        # Register language change listener for this window
        add_listener(self._refresh_language)

        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # =========================================================================
    # Language
    # =========================================================================
    def _on_language_changed(self, display_name: str):
        """Handle language selection change."""
        lang_code = LANGUAGES.get(display_name, "en")
        set_lang(lang_code)

    def _refresh_language(self):
        """Update this window's own translatable widgets."""
        self.title(t("app_title"))
        self._lang_label.configure(text=t("language") + ":")

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
    # DLP connection (FIXED: single connection, no double-open)
    # =========================================================================
    def connect_dlp(self):
        """Connect to DLP6500/DLP9000 via USB HID. Called from background thread."""
        # Create base class instance to detect DMD type
        base_dmd = dlpc900_dmd(debug=False, initialize=True)

        try:
            dmd_type_info = base_dmd.get_firmware_type()
            dmd_type = dmd_type_info.get('dmd type', 'unknown')
            fw = base_dmd.get_firmware_version()
            fw_version = fw.get('app version', 'N/A')
        except Exception:
            dmd_type = 'unknown'
            fw_version = 'N/A'

        # Save the HID path so we can reopen the correct device
        hid_path = base_dmd._hid_path

        # Explicitly close the base connection before reopening
        if base_dmd._dmd is not None:
            base_dmd._dmd.close()
            base_dmd._dmd = None
        base_dmd.initialized = False
        del base_dmd

        # Brief pause to ensure USB device is fully released
        time.sleep(0.3)

        # Now open the correct subclass using the saved HID path
        if dmd_type == "DLP9000":
            self.dlp = dlp9000(debug=False, initialize=True, hid_path=hid_path)
        else:
            # Default to DLP6500 for unknown types
            self.dlp = dlp6500(debug=False, initialize=True, hid_path=hid_path)

        self.log(t("dmd_type_firmware").format(dmd_type, fw_version))

    def disconnect_dlp(self):
        """Disconnect DLP6500."""
        if self.dlp is not None:
            try:
                self.dlp.start_stop_sequence('stop')
            except Exception:
                pass
            try:
                if self.dlp._dmd is not None:
                    self.dlp._dmd.close()
                    self.dlp._dmd = None
            except Exception:
                pass
            self.dlp.initialized = False
            self.dlp = None

    # =========================================================================
    # DCS connection
    # =========================================================================
    def connect_dcs(self, ip: str, port: int):
        """Connect to DCS Controller via UDP. Called from background thread."""
        self.dcs = DCSController(ip_address=ip, port=port)
        success = self.dcs.connect()
        if not success:
            self.dcs = None
            raise ConnectionError(t("dcs_connect_failed").format(ip, port))

    def disconnect_dcs(self):
        """Disconnect DCS Controller."""
        if self.dcs is not None:
            try:
                self.dcs.turn_off_all()
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
