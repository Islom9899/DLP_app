"""
DLP6500 control panel.
Pattern mode selection, image loading, exposure/dark time settings.
"""

import threading
import tkinter.filedialog as fd
import numpy as np
import customtkinter as ctk
from PIL import Image


class DLPPanel(ctk.CTkFrame):
    """DLP6500 pattern control panel."""

    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, **kwargs)

        self._app = app_controller
        self._pattern_file = None
        self._patterns = None

        self.configure(corner_radius=8)

        # Title
        title = ctk.CTkLabel(self, text="DLP6500 Pattern Boshqaruvi",
                              font=ctk.CTkFont(size=14, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, padx=10, pady=(8, 4), sticky="w")

        # =====================================================================
        # Pattern mode
        # =====================================================================
        mode_label = ctk.CTkLabel(self, text="Pattern Rejimi:")
        mode_label.grid(row=1, column=0, padx=(10, 5), pady=4, sticky="w")

        self.mode_var = ctk.StringVar(value="on-the-fly")
        self.mode_menu = ctk.CTkOptionMenu(
            self, values=["video", "pre-stored", "video-pattern", "on-the-fly"],
            variable=self.mode_var, width=160
        )
        self.mode_menu.grid(row=1, column=1, padx=(5, 10), pady=4, sticky="w")

        # =====================================================================
        # Pattern file picker
        # =====================================================================
        file_label = ctk.CTkLabel(self, text="Pattern Fayl:")
        file_label.grid(row=2, column=0, padx=(10, 5), pady=4, sticky="w")

        file_frame = ctk.CTkFrame(self, fg_color="transparent")
        file_frame.grid(row=2, column=1, padx=(5, 10), pady=4, sticky="ew")

        self.file_btn = ctk.CTkButton(file_frame, text="Tanlash...", width=90,
                                       command=self._select_pattern_file)
        self.file_btn.pack(side="left", padx=(0, 5))

        self.file_path_label = ctk.CTkLabel(file_frame, text="Tanlanmagan",
                                             text_color="gray", wraplength=200,
                                             anchor="w")
        self.file_path_label.pack(side="left", fill="x", expand=True)

        # =====================================================================
        # Exposure time
        # =====================================================================
        exp_label = ctk.CTkLabel(self, text="Exposure Vaqti (µs):")
        exp_label.grid(row=3, column=0, padx=(10, 5), pady=4, sticky="w")

        self.exp_entry = ctk.CTkEntry(self, width=100, placeholder_text="105")
        self.exp_entry.grid(row=3, column=1, padx=(5, 10), pady=4, sticky="w")
        self.exp_entry.insert(0, "105")

        exp_hint = ctk.CTkLabel(self, text="(min: 105 µs)",
                                 text_color="gray", font=ctk.CTkFont(size=10))
        exp_hint.grid(row=3, column=1, padx=(110, 10), pady=4, sticky="w")

        # =====================================================================
        # Dark time
        # =====================================================================
        dark_label = ctk.CTkLabel(self, text="Dark Vaqti (µs):")
        dark_label.grid(row=4, column=0, padx=(10, 5), pady=4, sticky="w")

        self.dark_entry = ctk.CTkEntry(self, width=100, placeholder_text="0")
        self.dark_entry.grid(row=4, column=1, padx=(5, 10), pady=4, sticky="w")
        self.dark_entry.insert(0, "0")

        # =====================================================================
        # Triggered mode
        # =====================================================================
        self.triggered_var = ctk.BooleanVar(value=False)
        self.triggered_switch = ctk.CTkSwitch(self, text="Trigger Kutish",
                                               variable=self.triggered_var)
        self.triggered_switch.grid(row=5, column=0, columnspan=2,
                                    padx=10, pady=4, sticky="w")

        # =====================================================================
        # Action buttons
        # =====================================================================
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=(8, 4), sticky="ew")

        self.upload_btn = ctk.CTkButton(btn_frame, text="Pattern Yuklash",
                                         fg_color="#2d6a4f",
                                         command=self._upload_patterns)
        self.upload_btn.pack(side="left", padx=(0, 5), expand=True, fill="x")

        self.start_btn = ctk.CTkButton(btn_frame, text="Boshlash",
                                        fg_color="#1b4332",
                                        command=self._start_sequence)
        self.start_btn.pack(side="left", padx=2, expand=True, fill="x")

        self.stop_btn = ctk.CTkButton(btn_frame, text="To'xtatish",
                                       fg_color="#6c1010",
                                       command=self._stop_sequence)
        self.stop_btn.pack(side="left", padx=(5, 0), expand=True, fill="x")

        # Pattern info
        self.info_label = ctk.CTkLabel(self, text="", text_color="gray",
                                        font=ctk.CTkFont(size=10))
        self.info_label.grid(row=7, column=0, columnspan=2, padx=10, pady=(2, 8), sticky="w")

        # Configure grid weights
        self.grid_columnconfigure(1, weight=1)

    def _select_pattern_file(self):
        """Open file dialog to select pattern file."""
        filetypes = [
            ("NumPy fayllari", "*.npy"),
            ("TIFF rasmlar", "*.tif *.tiff"),
            ("PNG rasmlar", "*.png"),
            ("BMP rasmlar", "*.bmp"),
            ("Barcha fayllar", "*.*")
        ]
        filepath = fd.askopenfilename(title="Pattern faylini tanlang",
                                       filetypes=filetypes)
        if filepath:
            self._pattern_file = filepath
            # Show just filename
            name = filepath.split("/")[-1].split("\\")[-1]
            self.file_path_label.configure(text=name, text_color="white")
            self._load_pattern_preview(filepath)

    def _load_pattern_preview(self, filepath: str):
        """Load and validate pattern file."""
        try:
            if filepath.endswith('.npy'):
                patterns = np.load(filepath)
            elif filepath.endswith(('.tif', '.tiff', '.png', '.bmp')):
                img = Image.open(filepath).convert('L')
                pattern = np.array(img, dtype=np.uint8)
                # Binarize: threshold at 128
                pattern = (pattern > 128).astype(np.uint8)
                patterns = pattern[np.newaxis, :, :]
            else:
                self._app.log(f"Noma'lum fayl formati: {filepath}")
                return

            if patterns.ndim == 2:
                patterns = patterns[np.newaxis, :, :]

            self._patterns = patterns
            n, h, w = patterns.shape
            self.info_label.configure(
                text=f"Yuklangan: {n} pattern, {w}x{h} px",
                text_color="#00CC00"
            )
            self._app.log(f"Pattern yuklandi: {n} ta, o'lchami {w}x{h}")
        except Exception as e:
            self.info_label.configure(text=f"Xato: {e}", text_color="#CC0000")
            self._app.log(f"Pattern yuklash xatosi: {e}")

    def _get_exposure_time(self) -> int:
        """Parse and validate exposure time."""
        try:
            val = int(self.exp_entry.get())
            if val < 105:
                self._app.log("Ogohlantirish: Exposure vaqti 105 µs dan kam bo'lmasligi kerak")
                return 105
            return val
        except ValueError:
            self._app.log("Xato: Exposure vaqti butun son bo'lishi kerak")
            return 105

    def _get_dark_time(self) -> int:
        """Parse and validate dark time."""
        try:
            val = int(self.dark_entry.get())
            return max(0, val)
        except ValueError:
            return 0

    def _upload_patterns(self):
        """Upload patterns to DMD in background thread."""
        if self._patterns is None:
            self._app.log("Xato: Avval pattern faylini tanlang")
            return

        if not self._app.dlp_connected:
            self._app.log("Xato: DLP6500 ulanmagan")
            return

        exp_time = self._get_exposure_time()
        dark_time = self._get_dark_time()
        triggered = self.triggered_var.get()

        self.upload_btn.configure(state="disabled", text="Yuklanmoqda...")
        self._app.log(f"Pattern yuklanmoqda... (exp={exp_time}µs, dark={dark_time}µs)")

        def task():
            try:
                self._app.dlp.upload_pattern_sequence(
                    self._patterns,
                    exp_times=exp_time,
                    dark_times=dark_time,
                    triggered=triggered
                )
                self.after(0, lambda: self._on_upload_done(True))
            except Exception as e:
                self.after(0, lambda: self._on_upload_done(False, str(e)))

        threading.Thread(target=task, daemon=True).start()

    def _on_upload_done(self, success: bool, error_msg: str = ""):
        self.upload_btn.configure(state="normal", text="Pattern Yuklash")
        if success:
            self._app.log("Pattern muvaffaqiyatli yuklandi")
            self.info_label.configure(text="Pattern DMD ga yuklandi", text_color="#00CC00")
        else:
            self._app.log(f"Pattern yuklash xatosi: {error_msg}")
            self.info_label.configure(text=f"Xato: {error_msg}", text_color="#CC0000")

    def _start_sequence(self):
        """Start DMD pattern sequence."""
        if not self._app.dlp_connected:
            self._app.log("Xato: DLP6500 ulanmagan")
            return

        try:
            mode = self.mode_var.get()
            self._app.dlp.set_pattern_mode(mode)
            self._app.dlp.start_stop_sequence('start')
            self._app.log("DLP pattern ketma-ketligi boshlandi")
        except Exception as e:
            self._app.log(f"DLP boshlash xatosi: {e}")

    def _stop_sequence(self):
        """Stop DMD pattern sequence."""
        if not self._app.dlp_connected:
            return

        try:
            self._app.dlp.start_stop_sequence('stop')
            self._app.log("DLP pattern ketma-ketligi to'xtatildi")
        except Exception as e:
            self._app.log(f"DLP to'xtatish xatosi: {e}")
