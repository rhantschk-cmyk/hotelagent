"""HotelAgent — GUI Launcher (Einstiegspunkt fuer EXE)."""

import sys
import os

# Sicherstellen dass das Projektverzeichnis im Path ist
if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
    os.chdir(os.path.dirname(sys.executable))
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_path)

# .env laden falls vorhanden
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from gui import launch_gui

if __name__ == "__main__":
    launch_gui()
