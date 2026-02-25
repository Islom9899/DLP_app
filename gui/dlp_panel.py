"""
DLP6500 control panel — Dual Listbox sequence editor.
Left: available images loaded from disk.
Right: ordered sequence to upload to the DMD.
Middle: add / remove transfer buttons.
"""

import os
import threading
import tkinter.filedialog as fd
import numpy as np
import customtkinter as ctk
from PIL import Image

from gui.i18n import t, add_listener


# =========================================================================
# Selectable list-item widget
# =========================================================================
class _ListItem(ctk.CTkFrame):
    """Single selectable row inside a scrollable list."""

    COLOR_NORMAL = "transparent"
    COLOR_SELECTED = "#2a4d6e"

    def __init__(self, master, label: str, on_click=None, **kwargs):
        super().__init__(master, height=28, corner_radius=4, **kwargs)

        self._selected = False
        self._on_click = on_click

        self._label = ctk.CTkLabel(
            self, text=label, anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self._label.pack(fill="x", padx=6, pady=2)

        self.configure(fg_color=self.COLOR_NORMAL, cursor="hand2")
        self._label.bind("<Button-1>", self._handle_click)
        self.bind("<Button-1>", self._handle_click)

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, value: bool):
        self._selected = value
        self.configure(
            fg_color=self.COLOR_SELECTED if value else self.COLOR_NORMAL
        )

    def set_text(self, text: str):
        self._label.configure(text=text)

    def _handle_click(self, _event=None):
        self.selected = not self._selected
        if self._on_click:
            self._on_click(self)


# =========================================================================
# Main panel
# =========================================================================
class DLPPanel(ctk.CTkFrame):
    """DLP6500 pattern control panel with dual-listbox sequence editor."""

    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, **kwargs)

        self._app = app_controller
        self._patterns = None  # final (N,H,W) array built from sequence

        # Internal data: parallel to the widget children
        # Each entry: {"path": str, "name": str, "array": np.ndarray}
        self._available_data: list[dict] = []
        self._sequence_data: list[dict] = []

        self.configure(corner_radius=8)

        # Title
        self._title = ctk.CTkLabel(
            self, text=t("dlp_pattern_control"),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self._title.grid(row=0, column=0, columnspan=5, padx=10,
                         pady=(8, 4), sticky="w")

        # =================================================================
        # Row 1 — three-column dual listbox
        # =================================================================
        list_frame = ctk.CTkFrame(self, fg_color="transparent")
        list_frame.grid(row=1, column=0, columnspan=5, padx=10,
                        pady=(4, 4), sticky="nsew")

        # --- Left column: Available Images ---
        left_col = ctk.CTkFrame(list_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 4))

        self._avail_title = ctk.CTkLabel(
            left_col, text=t("dlp_available_images"),
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self._avail_title.pack(anchor="w", pady=(0, 2))

        self._avail_scroll = ctk.CTkScrollableFrame(
            left_col, height=200, corner_radius=6
        )
        self._avail_scroll.pack(fill="both", expand=True)

        self._select_btn = ctk.CTkButton(
            left_col, text=t("dlp_select_images"), width=140,
            command=self._select_images
        )
        self._select_btn.pack(pady=(4, 0))

        # --- Middle column: transfer buttons ---
        mid_col = ctk.CTkFrame(list_frame, fg_color="transparent", width=90)
        mid_col.pack(side="left", fill="y", padx=4)
        mid_col.pack_propagate(False)

        spacer_top = ctk.CTkFrame(mid_col, fg_color="transparent")
        spacer_top.pack(expand=True)

        self._add_btn = ctk.CTkButton(
            mid_col, text=t("dlp_add_to_seq"), width=80, height=32,
            fg_color="#2d6a4f", hover_color="#1b4332",
            command=self._add_to_sequence
        )
        self._add_btn.pack(pady=(0, 6))

        self._remove_btn = ctk.CTkButton(
            mid_col, text=t("dlp_remove_from_seq"), width=80, height=32,
            fg_color="#6c1010", hover_color="#4a0b0b",
            command=self._remove_from_sequence
        )
        self._remove_btn.pack()

        spacer_bot = ctk.CTkFrame(mid_col, fg_color="transparent")
        spacer_bot.pack(expand=True)

        # --- Right column: Sequence Order ---
        right_col = ctk.CTkFrame(list_frame, fg_color="transparent")
        right_col.pack(side="left", fill="both", expand=True, padx=(4, 0))

        self._seq_title = ctk.CTkLabel(
            right_col, text=t("dlp_sequence_order"),
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self._seq_title.pack(anchor="w", pady=(0, 2))

        self._seq_scroll = ctk.CTkScrollableFrame(
            right_col, height=200, corner_radius=6
        )
        self._seq_scroll.pack(fill="both", expand=True)

        # Move Up / Move Down buttons
        move_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        move_frame.pack(fill="x", pady=(4, 0))

        self._move_up_btn = ctk.CTkButton(
            move_frame, text=t("dlp_move_up"), width=90, height=28,
            command=self._move_up
        )
        self._move_up_btn.pack(side="left", padx=(0, 4))

        self._move_down_btn = ctk.CTkButton(
            move_frame, text=t("dlp_move_down"), width=90, height=28,
            command=self._move_down
        )
        self._move_down_btn.pack(side="left")

        # =================================================================
        # Row 2 — Settings (pattern mode, exposure, dark, trigger)
        # =================================================================
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.grid(row=2, column=0, columnspan=5, padx=10,
                            pady=(6, 4), sticky="ew")

        # Pattern mode
        self._mode_label = ctk.CTkLabel(settings_frame, text=t("pattern_mode"))
        self._mode_label.grid(row=0, column=0, padx=(0, 5), pady=2, sticky="w")

        self.mode_var = ctk.StringVar(value="on-the-fly")
        self.mode_menu = ctk.CTkOptionMenu(
            settings_frame,
            values=["video", "pre-stored", "video-pattern", "on-the-fly"],
            variable=self.mode_var, width=140
        )
        self.mode_menu.grid(row=0, column=1, padx=(0, 20), pady=2, sticky="w")

        # Exposure time
        self._exp_label = ctk.CTkLabel(settings_frame, text=t("exposure_time"))
        self._exp_label.grid(row=0, column=2, padx=(0, 5), pady=2, sticky="w")

        self.exp_entry = ctk.CTkEntry(settings_frame, width=80,
                                       placeholder_text="105")
        self.exp_entry.grid(row=0, column=3, padx=(0, 5), pady=2, sticky="w")
        self.exp_entry.insert(0, "105")

        self._exp_hint = ctk.CTkLabel(
            settings_frame, text=t("min_exposure"),
            text_color="gray", font=ctk.CTkFont(size=10)
        )
        self._exp_hint.grid(row=0, column=4, padx=(0, 20), pady=2, sticky="w")

        # Dark time
        self._dark_label = ctk.CTkLabel(settings_frame, text=t("dark_time"))
        self._dark_label.grid(row=0, column=5, padx=(0, 5), pady=2, sticky="w")

        self.dark_entry = ctk.CTkEntry(settings_frame, width=80,
                                        placeholder_text="0")
        self.dark_entry.grid(row=0, column=6, padx=(0, 10), pady=2, sticky="w")
        self.dark_entry.insert(0, "0")

        # Trigger switch
        self.triggered_var = ctk.BooleanVar(value=False)
        self.triggered_switch = ctk.CTkSwitch(
            settings_frame, text=t("wait_trigger"),
            variable=self.triggered_var
        )
        self.triggered_switch.grid(row=0, column=7, padx=(0, 0), pady=2,
                                    sticky="w")

        # =================================================================
        # Row 3 — Action buttons
        # =================================================================
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=5, padx=10,
                       pady=(4, 4), sticky="ew")

        self.upload_btn = ctk.CTkButton(
            btn_frame, text=t("upload_patterns"),
            fg_color="#2d6a4f", hover_color="#1b4332",
            command=self._upload_patterns
        )
        self.upload_btn.pack(side="left", padx=(0, 5), expand=True, fill="x")

        self.start_btn = ctk.CTkButton(
            btn_frame, text=t("start"),
            fg_color="#1b4332", hover_color="#143826",
            command=self._start_sequence
        )
        self.start_btn.pack(side="left", padx=2, expand=True, fill="x")

        self.stop_btn = ctk.CTkButton(
            btn_frame, text=t("stop"),
            fg_color="#6c1010", hover_color="#4a0b0b",
            command=self._stop_sequence
        )
        self.stop_btn.pack(side="left", padx=(5, 0), expand=True, fill="x")

        # =================================================================
        # Row 4 — Info / status label
        # =================================================================
        self.info_label = ctk.CTkLabel(
            self, text="", text_color="gray",
            font=ctk.CTkFont(size=11)
        )
        self.info_label.grid(row=4, column=0, columnspan=5, padx=10,
                             pady=(0, 8), sticky="w")

        # Grid weights
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
        self._avail_title.configure(text=t("dlp_available_images"))
        self._select_btn.configure(text=t("dlp_select_images"))
        self._add_btn.configure(text=t("dlp_add_to_seq"))
        self._remove_btn.configure(text=t("dlp_remove_from_seq"))
        self._seq_title.configure(text=t("dlp_sequence_order"))
        self._move_up_btn.configure(text=t("dlp_move_up"))
        self._move_down_btn.configure(text=t("dlp_move_down"))
        self._mode_label.configure(text=t("pattern_mode"))
        self._exp_label.configure(text=t("exposure_time"))
        self._exp_hint.configure(text=t("min_exposure"))
        self._dark_label.configure(text=t("dark_time"))
        self.triggered_switch.configure(text=t("wait_trigger"))
        self.upload_btn.configure(text=t("upload_patterns"))
        self.start_btn.configure(text=t("start"))
        self.stop_btn.configure(text=t("stop"))

    # =====================================================================
    # Image loading
    # =====================================================================
    @staticmethod
    def _load_image_as_binary(filepath: str) -> np.ndarray:
        """Load an image file and return a binary (H, W) uint8 array."""
        if filepath.endswith('.npy'):
            arr = np.load(filepath)
            if arr.ndim == 3:
                # already (N, H, W) — return as-is
                return (arr > 128).astype(np.uint8) if arr.max() > 1 else arr.astype(np.uint8)
            if arr.ndim == 2:
                return (arr > 128).astype(np.uint8) if arr.max() > 1 else arr.astype(np.uint8)
            raise ValueError(f"Unsupported .npy shape: {arr.shape}")
        else:
            img = Image.open(filepath).convert('L')
            arr = np.array(img, dtype=np.uint8)
            return (arr > 128).astype(np.uint8)

    def _select_images(self):
        """Open file dialog for multi-select, load images into available list."""
        filetypes = [
            (t("bmp_images"), "*.bmp"),
            (t("png_images"), "*.png"),
            (t("numpy_files"), "*.npy"),
            (t("all_files"), "*.*"),
        ]
        paths = fd.askopenfilenames(
            title=t("select_pattern_title"),
            filetypes=filetypes
        )
        if not paths:
            return

        added = 0
        for p in paths:
            # Skip duplicates
            if any(d["path"] == p for d in self._available_data):
                continue
            try:
                arr = self._load_image_as_binary(p)
                name = os.path.basename(p)
                entry = {"path": p, "name": name, "array": arr}
                self._available_data.append(entry)
                self._create_avail_widget(entry)
                added += 1
            except Exception as e:
                self._app.log(t("pattern_load_error").format(e))

        if added > 0:
            self._app.log(t("dlp_images_added").format(added))

    def _create_avail_widget(self, entry: dict):
        """Create a selectable list item in the available panel."""
        item = _ListItem(self._avail_scroll, label=entry["name"])
        item.pack(fill="x", pady=1)
        entry["widget"] = item

    # =====================================================================
    # Transfer: available <-> sequence
    # =====================================================================
    def _add_to_sequence(self):
        """Move selected items from available list to sequence."""
        selected = [d for d in self._available_data
                    if d.get("widget") and d["widget"].selected]
        if not selected:
            self._app.log(t("dlp_no_selection"))
            return

        for d in selected:
            seq_entry = {
                "path": d["path"],
                "name": d["name"],
                "array": d["array"],
            }
            self._sequence_data.append(seq_entry)
            d["widget"].selected = False

        self._rebuild_sequence_widgets()
        self._update_info_label()

    def _remove_from_sequence(self):
        """Remove selected items from sequence list."""
        to_keep = []
        for i, d in enumerate(self._sequence_data):
            w = d.get("widget")
            if w and w.selected:
                w.destroy()
            else:
                to_keep.append(d)

        self._sequence_data = to_keep
        self._rebuild_sequence_widgets()
        self._update_info_label()

    # =====================================================================
    # Move up / down
    # =====================================================================
    def _move_up(self):
        """Move the first selected item in the sequence one position up."""
        for i, d in enumerate(self._sequence_data):
            if d.get("widget") and d["widget"].selected and i > 0:
                self._sequence_data[i - 1], self._sequence_data[i] = (
                    self._sequence_data[i], self._sequence_data[i - 1]
                )
                self._rebuild_sequence_widgets()
                # Re-select the moved item
                self._sequence_data[i - 1]["widget"].selected = True
                return

    def _move_down(self):
        """Move the first selected item in the sequence one position down."""
        n = len(self._sequence_data)
        for i in range(n - 2, -1, -1):
            d = self._sequence_data[i]
            if d.get("widget") and d["widget"].selected and i < n - 1:
                self._sequence_data[i], self._sequence_data[i + 1] = (
                    self._sequence_data[i + 1], self._sequence_data[i]
                )
                self._rebuild_sequence_widgets()
                # Re-select the moved item
                self._sequence_data[i + 1]["widget"].selected = True
                return

    # =====================================================================
    # Widget rebuilding
    # =====================================================================
    def _rebuild_sequence_widgets(self):
        """Destroy and re-create all sequence list-item widgets."""
        for d in self._sequence_data:
            w = d.get("widget")
            if w:
                w.destroy()

        for idx, d in enumerate(self._sequence_data):
            label = f"{idx + 1}. {d['name']}"
            item = _ListItem(self._seq_scroll, label=label)
            item.pack(fill="x", pady=1)
            d["widget"] = item

    def _update_info_label(self):
        """Show pattern count in info label."""
        n = len(self._sequence_data)
        if n > 0:
            self.info_label.configure(
                text=t("dlp_seq_count").format(n),
                text_color="#00CC00"
            )
        else:
            self.info_label.configure(text="", text_color="gray")

    # =====================================================================
    # Build final 3D array from sequence
    # =====================================================================
    def _build_sequence_array(self) -> np.ndarray:
        """Stack sequence items into a single (N, H, W) uint8 array."""
        arrays = []
        for d in self._sequence_data:
            arr = d["array"]
            if arr.ndim == 2:
                arrays.append(arr)
            elif arr.ndim == 3:
                # .npy with multiple patterns — add all frames
                for frame_idx in range(arr.shape[0]):
                    arrays.append(arr[frame_idx])

        if not arrays:
            raise ValueError("Sequence is empty")

        # Verify all frames have the same shape
        h, w = arrays[0].shape
        for i, a in enumerate(arrays):
            if a.shape != (h, w):
                raise ValueError(
                    f"Size mismatch at item {i + 1}: "
                    f"expected {w}x{h}, got {a.shape[1]}x{a.shape[0]}"
                )

        return np.stack(arrays, axis=0).astype(np.uint8)

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
    # Upload
    # =====================================================================
    def _upload_patterns(self):
        """Build 3D array from sequence and upload to DMD in background."""
        if not self._sequence_data:
            self._app.log(t("dlp_seq_empty"))
            return

        if not self._app.dlp_connected:
            self._app.log(t("err_dlp_not_connected"))
            return

        try:
            patterns = self._build_sequence_array()
        except Exception as e:
            self._app.log(t("pattern_load_error").format(e))
            return

        self._patterns = patterns
        exp_time = self._get_exposure_time()
        dark_time = self._get_dark_time()
        triggered = self.triggered_var.get()

        n = patterns.shape[0]
        self.upload_btn.configure(state="disabled", text=t("uploading"))
        self._app.log(t("pattern_uploading").format(exp_time, dark_time))
        self._app.log(t("dlp_seq_count").format(n))

        def task():
            try:
                self._app.dlp.upload_pattern_sequence(
                    patterns,
                    exp_times=exp_time,
                    dark_times=dark_time,
                    triggered=triggered
                )
                self.after(0, lambda: self._on_upload_done(True))
            except Exception as e:
                msg = str(e)
                self.after(0, lambda: self._on_upload_done(False, msg))

        threading.Thread(target=task, daemon=True).start()

    def _on_upload_done(self, success: bool, error_msg: str = ""):
        self.upload_btn.configure(state="normal", text=t("upload_patterns"))
        if success:
            self._app.log(t("pattern_uploaded"))
            self.info_label.configure(
                text=t("pattern_uploaded_dmd"), text_color="#00CC00"
            )
        else:
            self._app.log(t("pattern_upload_error").format(error_msg))
            self.info_label.configure(
                text=f"{t('error')}: {error_msg}", text_color="#CC0000"
            )

    # =====================================================================
    # Start / Stop
    # =====================================================================
    def _start_sequence(self):
        if not self._app.dlp_connected:
            self._app.log(t("err_dlp_not_connected"))
            return
        try:
            mode = self.mode_var.get()
            self._app.dlp.set_pattern_mode(mode)
            self._app.dlp.start_stop_sequence('start')
            self._app.log(t("dlp_sequence_started"))
        except Exception as e:
            self._app.log(t("dlp_start_error").format(e))

    def _stop_sequence(self):
        if not self._app.dlp_connected:
            return
        try:
            self._app.dlp.start_stop_sequence('stop')
            self._app.log(t("dlp_sequence_stopped"))
        except Exception as e:
            self._app.log(t("dlp_stop_error").format(e))
