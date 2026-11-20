import ctypes
import queue
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from storage import load_stickers, save_stickers, create_sticker, delete_sticker
from sticker import StickerWindow
from tray import Tray
from config import ICON_PATH

user32 = ctypes.windll.user32
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
WM_SETICON = 0x0080
LR_LOADFROMFILE = 0x00000010
IMAGE_ICON = 1

BG = "#202020"
CARD = "#2b2b2b"
CARD_SELECTED = "#3a3a3a"
FG = "#f0f0f0"
MUTED = "#8a8a8a"
PLACEHOLDER = "검색..."
WIDTH, HEIGHT = 340, 600


def native_handle(window):
    return user32.GetParent(window.winfo_id())


def format_date(value):
    if not value:
        return ""
    try:
        when = datetime.fromisoformat(value)
    except ValueError:
        return ""
    if when.year == datetime.now().year:
        return f"{when.month}월 {when.day}일"
    return f"{when.year}년 {when.month}월 {when.day}일"


class ManagerWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Knotticker")
        self.root.geometry(f"{WIDTH}x{HEIGHT}+80+80")
        self.root.overrideredirect(True)
        self.root.configure(bg=BG)

        self.stickers = load_stickers()
        self.open_windows = {}
        self.quitting = False
        self.commands = queue.Queue()
        self.selected_id = None
        self.cards = {}
        self.drag_offset = (0, 0)
        self.search_has_placeholder = True

        self.create_ui()
        self.refresh_list()
        self.setup_taskbar()
        self.setup_autosave()
        self.tray = Tray(self.commands)
        self.tray.start()
        self.root.after(150, self.process_commands)

    def setup_taskbar(self):
        self.root.update_idletasks()
        hwnd = native_handle(self.root)
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW)
        self.root.withdraw()
        self.root.deiconify()
        for flag, size in ((0, 16), (1, 32)):
            hicon = user32.LoadImageW(None, ICON_PATH, IMAGE_ICON, size, size, LR_LOADFROMFILE)
            if hicon:
                user32.SendMessageW(hwnd, WM_SETICON, flag, hicon)

    def process_commands(self):
        while True:
            try:
                command = self.commands.get_nowait()
            except queue.Empty:
                break
            self.handle_command(command)
        self.root.after(150, self.process_commands)

    def handle_command(self, command):
        if command == "list":
            self.show_list()
        elif command == "new":
            self.create_new_sticker()
        elif command == "show_all":
            for window in list(self.open_windows.values()):
                window.show()
        elif command == "hide_all":
            for window in list(self.open_windows.values()):
                window.hide()
        elif command == "quit":
            self.quit_app()

    def restore_open_stickers(self):
        restored = [s for s in self.stickers if s.get('open')]
        for sticker in restored:
            self.open_sticker(sticker)
        if restored:
            self.root.withdraw()

    def create_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Vertical.TScrollbar", background=CARD, troughcolor=BG,
                        bordercolor=BG, lightcolor=CARD, darkcolor=CARD, arrowcolor=MUTED)

        header = tk.Frame(self.root, bg=BG, height=44)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        header.bind("<ButtonPress-1>", self.start_drag)
        header.bind("<B1-Motion>", self.drag)

        tk.Button(header, text="+", command=self.create_new_sticker, bg=BG, fg=FG,
                  activebackground=BG, activeforeground=FG, relief=tk.FLAT, bd=0,
                  font=("Segoe UI", 14), cursor="hand2").pack(side=tk.LEFT, padx=12)
        tk.Button(header, text="✕", command=self.on_closing, bg=BG, fg=FG,
                  activebackground=BG, activeforeground=FG, relief=tk.FLAT, bd=0,
                  font=("Segoe UI", 11), cursor="hand2").pack(side=tk.RIGHT, padx=10)

        heading = tk.Label(self.root, text="Knotticker", bg=BG, fg=FG, font=("Segoe UI", 16, "bold"), anchor="w")
        heading.pack(fill=tk.X, padx=16, pady=(0, 10))
        heading.bind("<ButtonPress-1>", self.start_drag)
        heading.bind("<B1-Motion>", self.drag)

        search_wrap = tk.Frame(self.root, bg=BG)
        search_wrap.pack(fill=tk.X, padx=14, pady=(0, 12))
        self.search = tk.Entry(search_wrap, bg=CARD, fg=MUTED, insertbackground=FG, relief=tk.FLAT,
                               bd=0, font=("Segoe UI", 10))
        self.search.pack(fill=tk.X, ipady=7, padx=2)
        self.search.insert(0, PLACEHOLDER)
        self.search.bind("<FocusIn>", self.on_search_focus_in)
        self.search.bind("<FocusOut>", self.on_search_focus_out)
        self.search.bind("<KeyRelease>", lambda e: self.refresh_list())

        list_wrap = tk.Frame(self.root, bg=BG)
        list_wrap.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(list_wrap, bg=BG, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(list_wrap, orient=tk.VERTICAL, command=self.canvas.yview,
                                  style="Dark.Vertical.TScrollbar")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.inner = tk.Frame(self.canvas, bg=BG)
        self.win_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.update_scroll_region())
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.root.bind_all("<MouseWheel>", self.on_wheel)

    def update_scroll_region(self):
        width = self.canvas.winfo_width()
        height = max(self.inner.winfo_reqheight(), self.canvas.winfo_height())
        self.canvas.configure(scrollregion=(0, 0, width, height))

    def on_canvas_resize(self, event):
        self.canvas.itemconfigure(self.win_id, width=event.width)
        self.update_scroll_region()

    def on_wheel(self, event):
        first, last = self.canvas.yview()
        if last - first >= 1.0:
            return
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def on_search_focus_in(self, event):
        if self.search_has_placeholder:
            self.search.delete(0, tk.END)
            self.search.configure(fg=FG)
            self.search_has_placeholder = False

    def on_search_focus_out(self, event):
        if not self.search.get():
            self.search.insert(0, PLACEHOLDER)
            self.search.configure(fg=MUTED)
            self.search_has_placeholder = True

    def search_query(self):
        if self.search_has_placeholder:
            return ""
        return self.search.get().strip().lower()

    def refresh_list(self):
        for child in self.inner.winfo_children():
            child.destroy()
        self.cards = {}
        query = self.search_query()
        items = [s for s in self.stickers
                 if query in s.get('title', '').lower() or query in s.get('text', '').lower()]
        items.sort(key=lambda s: s.get('updated_at', ''), reverse=True)
        for sticker in items:
            self.build_card(sticker)
        if self.selected_id not in self.cards:
            self.selected_id = None
        self.paint_cards()

    def build_card(self, sticker):
        sid = sticker['id']
        card = tk.Frame(self.inner, bg=CARD, cursor="hand2")
        card.pack(fill=tk.X, padx=14, pady=(0, 10))
        accent = tk.Frame(card, bg=sticker['bg_color'], height=3)
        accent.pack(fill=tk.X)
        body = tk.Frame(card, bg=CARD)
        body.pack(fill=tk.X, padx=12, pady=(6, 10))
        date = tk.Label(body, text=format_date(sticker.get('updated_at')), bg=CARD,
                        fg=sticker['bg_color'], font=("Segoe UI", 8), anchor="e")
        date.pack(fill=tk.X)
        title = tk.Label(body, text=sticker.get('title') or 'Untitled', bg=CARD, fg=FG,
                         font=("Segoe UI", 10), anchor="w", justify=tk.LEFT, wraplength=280)
        title.pack(fill=tk.X, pady=(2, 0))
        fold = tk.Label(card, text="◢", bg=CARD, fg="#5a5a5a", font=("Segoe UI", 7), bd=0)
        fold.pack(side=tk.RIGHT, anchor="se", padx=4, pady=(0, 2))

        widgets = [card, body, title, date, fold]
        for widget in widgets:
            widget.bind("<Button-1>", lambda e, i=sid: self.select(i))
            widget.bind("<Double-Button-1>", lambda e, i=sid: self.open_by_id(i))
            widget.bind("<Button-3>", lambda e, i=sid: self.card_menu(e, i))
        self.cards[sid] = widgets

    def paint_cards(self):
        for sid, widgets in self.cards.items():
            color = CARD_SELECTED if sid == self.selected_id else CARD
            for widget in widgets:
                widget.configure(bg=color)

    def select(self, sid):
        self.selected_id = sid
        self.paint_cards()

    def find(self, sid):
        return next((s for s in self.stickers if s['id'] == sid), None)

    def open_by_id(self, sid):
        sticker = self.find(sid)
        if sticker:
            self.open_sticker(sticker)

    def card_menu(self, event, sid):
        self.select(sid)
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="열기", command=lambda: self.open_by_id(sid))
        menu.add_command(label="삭제", command=self.delete_selected)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def create_new_sticker(self):
        new_sticker = create_sticker()
        self.stickers.append(new_sticker)
        save_stickers(self.stickers)
        self.refresh_list()
        self.open_sticker(new_sticker)

    def delete_selected(self):
        if self.selected_id:
            self.delete_note(self.selected_id)

    def delete_note(self, sid):
        sticker = self.find(sid)
        if not sticker:
            return
        title = sticker.get('title') or 'Untitled'
        if not messagebox.askyesno("노트 삭제", f"'{title}' 노트를 삭제할까요?\n삭제하면 되돌릴 수 없습니다.",
                                   parent=self.root):
            return
        if sid in self.open_windows:
            self.open_windows.pop(sid).window.destroy()
        self.stickers = delete_sticker(self.stickers, sid)
        if self.selected_id == sid:
            self.selected_id = None
        save_stickers(self.stickers)
        self.refresh_list()

    def open_sticker(self, sticker_data):
        sticker_id = sticker_data['id']
        if sticker_id in self.open_windows:
            self.open_windows[sticker_id].restore()
        else:
            sticker_data['open'] = True
            save_stickers(self.stickers)
            window = StickerWindow(
                self.root,
                sticker_data,
                on_update_callback=self.on_sticker_update,
                on_close_callback=self.on_sticker_close,
                on_new_callback=self.create_new_sticker,
                on_list_callback=self.show_list,
                on_delete_callback=self.delete_note
            )
            self.open_windows[sticker_id] = window

    def on_sticker_update(self, sticker_data):
        for i, sticker in enumerate(self.stickers):
            if sticker['id'] == sticker_data['id']:
                self.stickers[i] = sticker_data
                break
        save_stickers(self.stickers)
        self.refresh_list()

    def on_sticker_close(self, sticker_id):
        self.open_windows.pop(sticker_id, None)
        if self.quitting:
            return
        for sticker in self.stickers:
            if sticker['id'] == sticker_id:
                sticker['open'] = False
                save_stickers(self.stickers)
                break

    def setup_autosave(self):
        def autosave():
            for sticker_id, window in list(self.open_windows.items()):
                try:
                    sticker = window.sticker_data
                    sticker['x'] = window.window.winfo_x()
                    sticker['y'] = window.window.winfo_y()
                    self.on_sticker_update(sticker)
                except:
                    pass
            self.root.after(5000, autosave)

        self.root.after(5000, autosave)

    def start_drag(self, event):
        self.drag_offset = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())

    def drag(self, event):
        self.root.geometry(f"+{event.x_root - self.drag_offset[0]}+{event.y_root - self.drag_offset[1]}")

    def show_list(self):
        self.root.deiconify()
        self.root.lift()

    def on_closing(self):
        self.root.withdraw()

    def quit_app(self):
        self.quitting = True
        self.tray.stop()
        for window in list(self.open_windows.values()):
            window.on_closing()
        save_stickers(self.stickers)
        self.root.destroy()
