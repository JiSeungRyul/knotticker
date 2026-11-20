import queue

import pystray
from PIL import Image

from config import ICON_PATH


class Tray:
    def __init__(self, commands: queue.Queue):
        image = Image.open(ICON_PATH).convert("RGBA")
        menu = pystray.Menu(
            pystray.MenuItem("메모 목록", lambda: commands.put("list"), default=True),
            pystray.MenuItem("새 메모", lambda: commands.put("new")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("모든 메모 표시", lambda: commands.put("show_all")),
            pystray.MenuItem("모든 메모 숨기기", lambda: commands.put("hide_all")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("종료", lambda: commands.put("quit")),
        )
        self.icon = pystray.Icon("knotticker", image, "Knotticker", menu)

    def start(self):
        self.icon.run_detached()

    def stop(self):
        self.icon.stop()
