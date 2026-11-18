import tkinter as tk
import sys
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from manager import ManagerWindow

if __name__ == "__main__":
    root = tk.Tk()
    app = ManagerWindow(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
