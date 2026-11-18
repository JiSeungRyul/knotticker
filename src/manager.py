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
        self.root.configure(bg="#f8f9fa")

        # 상단: 버튼 패널
        btn_frame = tk.Frame(self.root, bg="#f8f9fa")
        btn_frame.pack(fill=tk.X, padx=15, pady=15)

        tk.Label(btn_frame, text="Knotticker", font=("Segoe UI", 16, "bold"), bg="#f8f9fa", fg="#2C3E50").pack(side=tk.LEFT)

        btn_style = {"font": ("Segoe UI", 10), "bg": "#3498db", "fg": "white", "border": 0, "padx": 12, "pady": 6, "relief": tk.FLAT}
        tk.Button(btn_frame, text="+ New", command=self.create_new_sticker, **btn_style).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Delete", command=self.delete_selected, bg="#e74c3c", **{k: v for k, v in btn_style.items() if k != "bg"}).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Open", command=self.open_selected, **btn_style).pack(side=tk.RIGHT, padx=5)

        # 중간: 리스트 뷰 프레임
        list_frame = tk.Frame(self.root, bg="#f8f9fa")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # 스크롤바
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 커스텀 스타일 설정
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TScrollbar', background='#ecf0f1', troughcolor='#f8f9fa')

        self.listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.EXTENDED,
            font=("Segoe UI", 11),
            bg="white",
            fg="#2C3E50",
            border=1,
            highlightthickness=1,
            highlightcolor="#3498db",
            highlightbackground="#ecf0f1",
            activestyle='none',
            height=15
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        # 호버 효과
        self.listbox.bind("<Motion>", self.on_listbox_hover)
        self.listbox.bind("<Leave>", lambda e: self.listbox.config(bg="white"))
        self.listbox.bind("<Double-Button-1>", lambda e: self.open_selected())
        self.listbox.bind("<Return>", lambda e: self.open_selected())

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for idx, sticker in enumerate(self.stickers):
            # 타이틀과 미리보기
            title = sticker.get('title', 'Untitled')
            preview_text = sticker['text'][:35].replace('\n', ' ').strip()
            if len(sticker['text']) > 35:
                preview_text += "..."

            # 미리보기가 있으면 표시, 없으면 타이틀만
            if preview_text:
                display_text = f"{title}\n{preview_text}"
            else:
                display_text = title

            self.listbox.insert(tk.END, display_text)

            # 색상 태그 추가 (각 항목마다 고유한 태그)
            tag_name = f"bg_color_{idx}"
            bg_color = sticker.get('bg_color', '#FFFACD')
            self.listbox.itemconfig(idx, {'bg': '#f8f9fa', 'selectbackground': '#d5dbeb'})

            # 색상 블록을 위한 커스텀 렌더링은 텍스트 앞에 색상 표시
            # (tkinter 리스트박스 제한으로 별도 처리)

    def on_listbox_hover(self, event):
        idx = self.listbox.nearest(event.y)
        if idx >= 0:
            self.listbox.itemconfig(idx, {'bg': '#ecf0f1'})

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
