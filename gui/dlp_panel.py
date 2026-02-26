"""
DLP6500 control panel — Interactive Click-to-Project (Live) mode.
Left:  image library loaded from a folder.
Right: exposure / dark settings, stop button, and status display.
"""

import os
import threading
import tkinter.filedialog as fd
import numpy as np
import customtkinter as ctk
from PIL import Image

from gui.i18n import t, add_listener


# Default DMD resolution (used when no device is connected)
_DEFAULT_DMD_WIDTH = 1920
_DEFAULT_DMD_HEIGHT = 1080


class DLPPanel(ctk.CTkFrame):
    """DLP6500 interactive click-to-project panel."""

    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, **kwargs)

        self._app = app_controller

        # State
        self._image_files: list[str] = []
        self._image_buttons: list[ctk.CTkButton] = []
        self._projecting = False
        self._projecting_lock = threading.Lock()

        self.configure(corner_radius=8)

        # =====================================================================
        # Row 0 — Title
        # =====================================================================
        self._title = ctk.CTkLabel(
            self, text=t("dlp_pattern_control"),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self._title.grid(row=0, column=0, columnspan=2,
                         padx=10, pady=(8, 4), sticky="w")

        # =====================================================================
        # Row 1 — Two-column body
        # =====================================================================
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, columnspan=2,
                  padx=10, pady=(4, 8), sticky="nsew")
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # ----- Left column: Image Library -----
        left = ctk.CTkFrame(body, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self._lib_title = ctk.CTkLabel(
            left, text=t("dlp_image_library"),
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self._lib_title.pack(anchor="w", pady=(0, 2))

        self._load_btn = ctk.CTkButton(
            left, text=t("dlp_load_folder"),
            fg_color="#2d6a4f", hover_color="#1b4332",
            height=30, command=self._load_folder
        )
        self._load_btn.pack(fill="x", pady=(0, 4))

        self._image_scroll = ctk.CTkScrollableFrame(
            left, height=220, corner_radius=6
        )
        self._image_scroll.pack(fill="both", expand=True)

        # ----- Right column: Control & Status -----
        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self._ctrl_title = ctk.CTkLabel(
            right, text=t("dlp_control_status"),
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self._ctrl_title.pack(anchor="w", pady=(0, 6))

        # Exposure time
        exp_frame = ctk.CTkFrame(right, fg_color="transparent")
        exp_frame.pack(fill="x", pady=(0, 2))

        self._exp_label = ctk.CTkLabel(exp_frame, text=t("exposure_time"))
        self._exp_label.pack(anchor="w")

        self.exp_entry = ctk.CTkEntry(exp_frame, width=120,
                                       placeholder_text="105")
        self.exp_entry.pack(fill="x")
        self.exp_entry.insert(0, "105")

        self._exp_hint = ctk.CTkLabel(
            exp_frame, text=t("min_exposure"),
            text_color="gray", font=ctk.CTkFont(size=10)
        )
        self._exp_hint.pack(anchor="w")

        # Dark time
        dark_frame = ctk.CTkFrame(right, fg_color="transparent")
        dark_frame.pack(fill="x", pady=(4, 6))

        self._dark_label = ctk.CTkLabel(dark_frame, text=t("dark_time"))
        self._dark_label.pack(anchor="w")

        self.dark_entry = ctk.CTkEntry(dark_frame, width=120,
                                        placeholder_text="0")
        self.dark_entry.pack(fill="x")
        self.dark_entry.insert(0, "0")

        # STOP / RESET button
        self._stop_btn = ctk.CTkButton(
            right, text=t("dlp_stop_reset"),
            fg_color="#6c1010", hover_color="#4a0b0b",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=50,
            command=self._stop_reset
        )
        self._stop_btn.pack(fill="x", pady=(6, 6))

        # Status label
        self._status_label = ctk.CTkLabel(
            right, text=t("dlp_idle"),
            font=ctk.CTkFont(size=11), text_color="gray",
            wraplength=200
        )
        self._status_label.pack(anchor="w", pady=(4, 0))

        # =====================================================================
        # Main-frame grid weights
        # =====================================================================
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Register for language changes
        add_listener(self._refresh_language)

    # =====================================================================
    # Language
    # =====================================================================
    def _refresh_language(self):
        """Update all translatable text."""
        self._title.configure(text=t("dlp_pattern_control"))
        self._lib_title.configure(text=t("dlp_image_library"))
        self._load_btn.configure(text=t("dlp_load_folder"))
        self._ctrl_title.configure(text=t("dlp_control_status"))
        self._exp_label.configure(text=t("exposure_time"))
        self._exp_hint.configure(text=t("min_exposure"))
        self._dark_label.configure(text=t("dark_time"))
        self._stop_btn.configure(text=t("dlp_stop_reset"))
        if not self._projecting:
            self._status_label.configure(text=t("dlp_idle"))

    # =====================================================================
    # Folder loading
    # =====================================================================
    def _load_folder(self):
        """Open a folder dialog, scan for .bmp / .png files, populate buttons."""
        folder = fd.askdirectory(title=t("dlp_load_folder"))
        if not folder:
            return

        extensions = {".bmp", ".png"}
        files = sorted([
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in extensions
        ])

        if not files:
            self._app.log(t("dlp_no_images_in_folder"))
            return

        # Clear previous buttons
        self._clear_image_buttons()

        self._image_files = files

        for index,filepath in enumerate(files, start=1):
            filename = os.path.basename(filepath)

            display_text = f"{index:03d} - {filename}"
            btn = ctk.CTkButton(
                self._image_scroll,
                text=display_text,
                height=28,
                anchor="w",
                fg_color="#555555",
                hover_color="#444444",
                font=ctk.CTkFont(size=11),
                command=lambda fp=filepath, fn=filename: self._on_image_click(fp, fn)
            )
            btn.pack(fill="x", pady=1, padx=2)
            self._image_buttons.append(btn)

        self._app.log(t("dlp_folder_loaded").format(len(files)))

    def _clear_image_buttons(self):
        """Destroy all image buttons in the scrollable frame."""
        for btn in self._image_buttons:
            btn.destroy()
        self._image_buttons.clear()
        self._image_files.clear()

    # =====================================================================
    # Click-to-project
    # =====================================================================
    def _on_image_click(self, filepath: str, filename: str):
        """Handle image button click — project a single image in a thread."""
        with self._projecting_lock:
            if self._projecting:
                self._app.log(t("dlp_busy_projecting"))
                return
            self._projecting = True

        # Read UI entry values on the main thread (tkinter is not thread-safe)
        exp_val = self._get_exposure_time()
        dark_val = self._get_dark_time()

        self._status_label.configure(
            text=t("dlp_projecting").format(filename),
            text_color="#00CC00"
        )
        self._set_buttons_state("disabled")

        def task():
            try:
                if not self._app.dlp_connected:
                    raise ConnectionError(t("err_dlp_not_connected"))

                # Resolve DMD resolution from connected device
                dmd_w = getattr(self._app.dlp, "width", _DEFAULT_DMD_WIDTH)
                dmd_h = getattr(self._app.dlp, "height", _DEFAULT_DMD_HEIGHT)

                img_array = self._prepare_image(filepath, dmd_w, dmd_h)

                self._app.log(
                    t("dlp_projecting_log").format(filename, exp_val, dark_val)
                )

                self._app.dlp.upload_pattern_sequence(
                    patterns=img_array,
                    exp_times=exp_val,
                    dark_times=dark_val,
                    num_repeats=0
                )

                self.after(0, lambda: self._on_project_done(filename))

            except Exception as e:
                msg = str(e)
                self.after(0, lambda: self._on_project_error(msg))

        threading.Thread(target=task, daemon=True).start()

    def _on_project_done(self, filename: str):
        """Called on the UI thread after a successful projection."""
        with self._projecting_lock:
            self._projecting = False
        self._set_buttons_state("normal")
        self._app.log(t("dlp_projection_done").format(filename))
        self._status_label.configure(text=t("dlp_idle"), text_color="gray")

    def _on_project_error(self, error_msg: str):
        """Called on the UI thread after a projection failure."""
        with self._projecting_lock:
            self._projecting = False
        self._set_buttons_state("normal")
        self._app.log(t("dlp_projection_error").format(error_msg))
        self._status_label.configure(
            text=f"{t('error')}: {error_msg}", text_color="#CC0000"
        )

    # =====================================================================
    # Image processing
    # =====================================================================
    @staticmethod
    def _prepare_image(filepath: str, dmd_w: int, dmd_h: int) -> np.ndarray:
        """Load an image, center/pad onto a DMD-sized black canvas.

        Returns a (1, dmd_h, dmd_w) uint8 binary array (0 or 1).
        """
        img = Image.open(filepath).convert("L")
        iw, ih = img.size  # PIL uses (width, height)

        # Resize proportionally if larger than the DMD in either dimension
        if iw > dmd_w or ih > dmd_h:
            ratio = min(dmd_w / iw, dmd_h / ih)
            img = img.resize((int(iw * ratio), int(ih * ratio)), Image.LANCZOS)
            iw, ih = img.size

        # Black canvas at DMD resolution
        canvas = np.zeros((dmd_h, dmd_w), dtype=np.uint8)

        # Paste centred
        arr = np.array(img, dtype=np.uint8)
        x_off = (dmd_w - iw) // 2
        y_off = (dmd_h - ih) // 2
        canvas[y_off:y_off + ih, x_off:x_off + iw] = arr

        # Threshold to binary (values > 128 → 1, else 0)
        binary = (canvas > 128).astype(np.uint8)

        return binary.reshape(1, dmd_h, dmd_w)

    # =====================================================================
    # Settings helpers
    # =====================================================================
    def _get_exposure_time(self) -> int:
        try:
            val = int(self.exp_entry.get())
            if val < 105:
                self._app.log(t("warn_min_exposure"))
                return 105
            return val
        except ValueError:
            self._app.log(t("err_exposure_integer"))
            return 105

    def _get_dark_time(self) -> int:
        try:
            val = int(self.dark_entry.get())
            return max(0, val)
        except ValueError:
            return 0

    # =====================================================================
    # Stop / Reset
    # =====================================================================
    def _stop_reset(self):
        """Emergency stop — halt any running DLP sequence."""
        if not self._app.dlp_connected:
            self._app.log(t("err_dlp_not_connected"))
            return
        try:
            self._app.dlp.start_stop_sequence("stop")
            self._app.log(t("dlp_stopped_reset"))
            self._status_label.configure(text=t("dlp_idle"), text_color="gray")
            # Clear busy flag in case a thread is stuck
            with self._projecting_lock:
                self._projecting = False
            self._set_buttons_state("normal")
        except Exception as e:
            self._app.log(t("dlp_stop_error").format(e))

    # =====================================================================
    # Helpers
    # =====================================================================
    def _set_buttons_state(self, state: str):
        """Enable or disable all image buttons."""
        for btn in self._image_buttons:
            btn.configure(state=state)
