import ctypes
import tkinter as tk
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from manager import ManagerWindow

APP_ID = "Knotticker.StickyNotes"

if __name__ == "__main__":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    root = tk.Tk()
    app = ManagerWindow(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
