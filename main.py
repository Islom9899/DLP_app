"""
DLP6500 + DCS Controller Desktop Application
Entry point for the GUI application.

Usage:
    python main.py

Build .exe:
    pyinstaller dlp_app.spec
"""

import sys
import os

# Ensure the project root is on the Python path
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))

if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from gui.app import DLPApp


def main():
    app = DLPApp()
    app.mainloop()


if __name__ == "__main__":
    main()
