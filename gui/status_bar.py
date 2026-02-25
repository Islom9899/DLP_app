"""
Status bar with scrollable log messages.
"""

import datetime
import customtkinter as ctk

from gui.i18n import t, add_listener


class StatusBar(ctk.CTkFrame):
    """Bottom status bar showing timestamped log messages."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(corner_radius=8)

        # Title
        self._title = ctk.CTkLabel(self, text=t("log"),
                              font=ctk.CTkFont(size=12, weight="bold"))
        self._title.pack(anchor="w", padx=10, pady=(4, 0))

        # Textbox for log messages
        self.textbox = ctk.CTkTextbox(self, height=100,
                                       font=ctk.CTkFont(family="Consolas", size=11),
                                       state="disabled",
                                       wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=8, pady=(2, 6))

        # Clear button
        self._clear_btn = ctk.CTkButton(self, text=t("clear"), width=70, height=24,
                                   font=ctk.CTkFont(size=10),
                                   fg_color="#555555",
                                   command=self.clear)
        self._clear_btn.place(relx=1.0, rely=0.0, x=-14, y=4, anchor="ne")

        # Register for language changes
        add_listener(self._refresh_language)

    def _refresh_language(self):
        """Update all translatable text."""
        self._title.configure(text=t("log"))
        self._clear_btn.configure(text=t("clear"))

    def log(self, message: str):
        """Add timestamped message to log."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"

        self.textbox.configure(state="normal")
        self.textbox.insert("end", line)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self):
        """Clear all log messages."""
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
