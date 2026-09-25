"""packaging/run_gui.py — PyInstaller için doğrudan Qt6 GUI giriş noktası."""
import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.gui import launch_gui

if __name__ == "__main__":
    sys.exit(launch_gui())
