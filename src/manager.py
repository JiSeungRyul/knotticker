import tkinter as tk
from tkinter import ttk
from storage import load_stickers, save_stickers, create_sticker, delete_sticker
from sticker import StickerWindow
from config import STICKER_COLORS

class ManagerWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Knotticker - Sticker Manager")
        self.root.geometry("600x400")
        self.root.iconbitmap(default='')  # 아이콘 설정 안 함

        self.stickers = load_stickers()
        self.open_windows = {}

        self.create_ui()
        self.refresh_list()
        self.setup_autosave()

    def create_ui(self):
        # 상단: 버튼 패널
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(btn_frame, text="+ New Sticker", command=self.create_new_sticker).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete Selected", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Open Selected", command=self.open_selected).pack(side=tk.LEFT, padx=5)

        # 중간: 리스트 뷰
        list_frame = tk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 스크롤바
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, selectmode=tk.EXTENDED)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        self.listbox.bind("<Double-Button-1>", lambda e: self.open_selected())

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for sticker in self.stickers:
            # 타이틀과 미리보기
            title = sticker.get('title', 'Untitled')
            preview_text = sticker['text'][:40].replace('\n', ' ')
            if len(sticker['text']) > 40:
                preview_text += "..."

            # 미리보기가 있으면 표시, 없으면 타이틀만
            if preview_text.strip():
                display_text = f"📝 {title}  -  {preview_text}"
            else:
                display_text = f"📝 {title}"

            self.listbox.insert(tk.END, display_text)

    def create_new_sticker(self):
        new_sticker = create_sticker()
        self.stickers.append(new_sticker)
        save_stickers(self.stickers)
        self.refresh_list()
        self.open_sticker(new_sticker)

    def delete_selected(self):
        selected = self.listbox.curselection()
        for idx in reversed(selected):
            sticker_id = self.stickers[idx]['id']
            if sticker_id in self.open_windows:
                self.open_windows[sticker_id].window.destroy()
            self.stickers = delete_sticker(self.stickers, sticker_id)
        save_stickers(self.stickers)
        self.refresh_list()

    def open_selected(self):
        selected = self.listbox.curselection()
        for idx in selected:
            self.open_sticker(self.stickers[idx])

    def open_sticker(self, sticker_data):
        sticker_id = sticker_data['id']
        if sticker_id in self.open_windows:
            self.open_windows[sticker_id].window.lift()
        else:
            window = StickerWindow(
                self.root,
                sticker_data,
                on_update_callback=self.on_sticker_update,
                on_close_callback=self.on_sticker_close
            )
            self.open_windows[sticker_id] = window

    def on_sticker_update(self, sticker_data):
        # 스티커 데이터 업데이트
        for i, sticker in enumerate(self.stickers):
            if sticker['id'] == sticker_data['id']:
                self.stickers[i] = sticker_data
                break
        save_stickers(self.stickers)
        self.refresh_list()

    def on_sticker_close(self, sticker_id):
        if sticker_id in self.open_windows:
            del self.open_windows[sticker_id]

    def setup_autosave(self):
        # 주기적으로 모든 열린 스티커 저장
        def autosave():
            for sticker_id, window in list(self.open_windows.items()):
                try:
                    # 창 위치 저장
                    sticker = window.sticker_data
                    sticker['x'] = window.window.winfo_x()
                    sticker['y'] = window.window.winfo_y()
                    self.on_sticker_update(sticker)
                except:
                    pass
            self.root.after(5000, autosave)  # 5초마다 체크

        self.root.after(5000, autosave)

    def on_closing(self):
        # 모든 열린 스티커 창 닫기
        for window in list(self.open_windows.values()):
            window.window.destroy()
        save_stickers(self.stickers)
        self.root.destroy()
