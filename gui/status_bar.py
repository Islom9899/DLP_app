"""
Status bar with scrollable log messages.
"""

import datetime
import customtkinter as ctk


class StatusBar(ctk.CTkFrame):
    """Bottom status bar showing timestamped log messages."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(corner_radius=8)

        # Title
        title = ctk.CTkLabel(self, text="Jurnal",
                              font=ctk.CTkFont(size=12, weight="bold"))
        title.pack(anchor="w", padx=10, pady=(4, 0))

        # Textbox for log messages
        self.textbox = ctk.CTkTextbox(self, height=100,
                                       font=ctk.CTkFont(family="Consolas", size=11),
                                       state="disabled",
                                       wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=8, pady=(2, 6))

        # Clear button
        clear_btn = ctk.CTkButton(self, text="Tozalash", width=70, height=24,
                                   font=ctk.CTkFont(size=10),
                                   fg_color="#555555",
                                   command=self.clear)
        clear_btn.place(relx=1.0, rely=0.0, x=-14, y=4, anchor="ne")

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
