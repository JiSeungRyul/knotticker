import tkinter as tk
from tkinter import font
from config import STICKER_COLORS, TEXT_COLORS, FONTS, MENU_FADE_TIME
from storage import update_sticker, save_stickers

class StickerWindow:
    def __init__(self, parent, sticker_data, on_update_callback, on_close_callback):
        self.parent = parent
        self.sticker_data = sticker_data
        self.on_update_callback = on_update_callback
        self.on_close_callback = on_close_callback

        self.window = tk.Toplevel(parent)
        self.window.title("")
        self.window.geometry(f"{sticker_data['width']}x{sticker_data['height']}+{sticker_data['x']}+{sticker_data['y']}")
        self.window.configure(bg=sticker_data['bg_color'], highlightthickness=0)
        self.window.overrideredirect(True)  # 타이틀 바 제거

        # 드래그 위치 추적
        self.drag_data = {"x": 0, "y": 0}

        # Always on top 옵션
        if sticker_data.get('always_on_top', False):
            self.window.attributes('-topmost', True)

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 타이틀 입력창
        self.title_entry = tk.Entry(
            self.window,
            border=0,
            font=("Segoe UI", 10, "bold"),
            fg=sticker_data['text_color'],
            bg=sticker_data['bg_color'],
            highlightthickness=0
        )
        self.title_entry.pack(fill=tk.X, padx=10, pady=(8, 2))
        self.title_entry.insert(0, sticker_data.get('title', 'Untitled'))
        self.title_entry.bind("<KeyRelease>", self.on_title_change)
        self.title_entry.bind("<Return>", lambda e: self.text_widget.focus())

        # 구분선
        separator = tk.Frame(self.window, height=1, bg=sticker_data['text_color'], highlightthickness=0)
        separator.pack(fill=tk.X, padx=10, pady=(0, 5))

        # 텍스트 에디터
        self.text_widget = tk.Text(
            self.window,
            wrap=tk.WORD,
            padx=10,
            pady=10,
            border=0,
            highlightthickness=0
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        self.text_widget.insert("1.0", sticker_data['text'])
        self.text_widget.bind("<KeyRelease>", self.on_text_change)
        self.text_widget.bind("<Motion>", self.on_mouse_move)
        self.text_widget.bind("<Leave>", self.on_mouse_leave)
        self.text_widget.bind("<Button-3>", self.show_context_menu)
        self.text_widget.bind("<Button-1>", self.on_text_press)
        self.text_widget.bind("<B1-Motion>", self.on_text_drag)

        # 텍스트 태그 설정
        self.text_widget.tag_configure("strikethrough", overstrike=True)

        # 호버 메뉴
        self.menu_frame = tk.Frame(self.window, bg="#2C3E50", highlightthickness=0)
        self.menu_visible = False
        self.menu_fade_id = None
        self.separator = separator

        self.create_menu_buttons()
        self.update_text_widget_format()
        self.auto_save_id = None

    def create_menu_buttons(self):
        # 행 1: 배경색
        color_frame = tk.Frame(self.menu_frame, bg="#2C3E50")
        color_frame.pack(fill=tk.X, padx=5, pady=3)

        tk.Label(color_frame, text="Bg:", bg="#2C3E50", fg="white", font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        for color in STICKER_COLORS:
            btn = tk.Button(
                color_frame,
                bg=color,
                width=2,
                height=1,
                relief=tk.FLAT,
                command=lambda c=color: self.change_bg_color(c)
            )
            btn.pack(side=tk.LEFT, padx=1)

        # 행 2: 글자색
        text_frame = tk.Frame(self.menu_frame, bg="#2C3E50")
        text_frame.pack(fill=tk.X, padx=5, pady=3)

        tk.Label(text_frame, text="Text:", bg="#2C3E50", fg="white", font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        for color in TEXT_COLORS:
            btn = tk.Button(
                text_frame,
                bg=color,
                fg="white",
                text="A",
                width=2,
                height=1,
                relief=tk.FLAT,
                font=("Arial", 7, "bold"),
                command=lambda c=color: self.change_text_color(c)
            )
            btn.pack(side=tk.LEFT, padx=1)

        # 행 3: 폰트 및 스타일
        style_frame = tk.Frame(self.menu_frame, bg="#2C3E50")
        style_frame.pack(fill=tk.X, padx=5, pady=3)

        self.font_var = tk.StringVar(value=f"{self.sticker_data['font_family']} {self.sticker_data['font_size']}")
        font_menu = tk.OptionMenu(style_frame, self.font_var, *[f"{f[0]} {f[1]}" for f in FONTS], command=self.change_font)
        font_menu.config(bg="#34495E", fg="white", highlightthickness=0, width=12)
        font_menu["menu"].config(bg="#34495E", fg="white")
        font_menu.pack(side=tk.LEFT, padx=2)

        # 스타일 버튼
        self.bold_btn = tk.Button(style_frame, text="B", width=2, relief=tk.FLAT,
                                  bg="#34495E", fg="white", command=self.toggle_bold, font=("Arial", 8, "bold"))
        self.bold_btn.pack(side=tk.LEFT, padx=1)

        self.italic_btn = tk.Button(style_frame, text="I", width=2, relief=tk.FLAT,
                                   bg="#34495E", fg="white", command=self.toggle_italic, font=("Arial", 8, "italic"))
        self.italic_btn.pack(side=tk.LEFT, padx=1)

        self.underline_btn = tk.Button(style_frame, text="U", width=2, relief=tk.FLAT,
                                      bg="#34495E", fg="white", command=self.toggle_underline, font=("Arial", 8, "underline"))
        self.underline_btn.pack(side=tk.LEFT, padx=1)

        self.strikethrough_btn = tk.Button(style_frame, text="S", width=2, relief=tk.FLAT,
                                          bg="#34495E", fg="white", command=self.toggle_strikethrough, font=("Arial", 8))
        self.strikethrough_btn.pack(side=tk.LEFT, padx=1)

        self.ontop_btn = tk.Button(style_frame, text="📌", width=2, relief=tk.FLAT,
                                  bg="#34495E", fg="white", command=self.toggle_always_on_top, font=("Arial", 8))
        self.ontop_btn.pack(side=tk.LEFT, padx=1)

        self.update_button_styles()

    def update_button_styles(self):
        self.bold_btn.config(relief=tk.SUNKEN if self.sticker_data['bold'] else tk.FLAT)
        self.italic_btn.config(relief=tk.SUNKEN if self.sticker_data['italic'] else tk.FLAT)
        self.underline_btn.config(relief=tk.SUNKEN if self.sticker_data['underline'] else tk.FLAT)
        self.strikethrough_btn.config(relief=tk.SUNKEN if self.sticker_data.get('strikethrough', False) else tk.FLAT)
        self.ontop_btn.config(relief=tk.SUNKEN if self.sticker_data.get('always_on_top', False) else tk.FLAT)

    def on_mouse_move(self, event):
        if not self.menu_visible:
            self.show_menu()

    def on_mouse_leave(self, event):
        if self.menu_fade_id:
            self.window.after_cancel(self.menu_fade_id)
        self.menu_fade_id = self.window.after(MENU_FADE_TIME, self.hide_menu)

    def show_menu(self):
        if not self.menu_visible:
            self.menu_frame.pack(side=tk.TOP, fill=tk.X)
            self.menu_visible = True

    def hide_menu(self):
        if self.menu_visible:
            self.menu_frame.pack_forget()
            self.menu_visible = False
        self.menu_fade_id = None

    def change_bg_color(self, color):
        self.sticker_data['bg_color'] = color
        self.window.configure(bg=color)
        self.title_entry.config(bg=color)
        self.text_widget.configure(bg=color)
        self.on_text_change(None)

    def change_text_color(self, color):
        self.sticker_data['text_color'] = color
        self.title_entry.config(fg=color)
        self.separator.config(bg=color)
        self.update_text_widget_format()
        self.on_text_change(None)

    def change_font(self, font_str):
        parts = font_str.rsplit(' ', 1)
        font_name = parts[0]
        font_size = int(parts[1])
        self.sticker_data['font_family'] = font_name
        self.sticker_data['font_size'] = font_size
        self.update_text_widget_format()
        self.on_text_change(None)

    def toggle_bold(self):
        self.sticker_data['bold'] = not self.sticker_data['bold']
        self.update_button_styles()
        self.update_text_widget_format()
        self.on_text_change(None)

    def toggle_italic(self):
        self.sticker_data['italic'] = not self.sticker_data['italic']
        self.update_button_styles()
        self.update_text_widget_format()
        self.on_text_change(None)

    def toggle_underline(self):
        self.sticker_data['underline'] = not self.sticker_data['underline']
        self.update_button_styles()
        self.update_text_widget_format()
        self.on_text_change(None)

    def toggle_strikethrough(self):
        self.sticker_data['strikethrough'] = not self.sticker_data.get('strikethrough', False)
        self.update_button_styles()
        self.update_text_widget_format()
        self.on_text_change(None)

    def toggle_always_on_top(self):
        self.sticker_data['always_on_top'] = not self.sticker_data.get('always_on_top', False)
        self.window.attributes('-topmost', self.sticker_data['always_on_top'])
        self.update_button_styles()
        self.on_text_change(None)

    def update_text_widget_format(self):
        font_style = "normal"
        if self.sticker_data['bold'] and self.sticker_data['italic']:
            font_style = "bold italic"
        elif self.sticker_data['bold']:
            font_style = "bold"
        elif self.sticker_data['italic']:
            font_style = "italic"

        new_font = font.Font(
            family=self.sticker_data['font_family'],
            size=self.sticker_data['font_size'],
            slant="italic" if self.sticker_data['italic'] else "roman",
            weight="bold" if self.sticker_data['bold'] else "normal"
        )
        self.text_widget.configure(font=new_font, fg=self.sticker_data['text_color'], bg=self.sticker_data['bg_color'])

    def on_title_change(self, event):
        self.sticker_data['title'] = self.title_entry.get() or 'Untitled'
        self.on_text_change(None)

    def on_text_change(self, event):
        self.sticker_data['text'] = self.text_widget.get("1.0", tk.END).rstrip('\n')

        if self.auto_save_id:
            self.window.after_cancel(self.auto_save_id)
        self.auto_save_id = self.window.after(1000, self.save_to_file)

    def save_to_file(self):
        self.on_update_callback(self.sticker_data)
        self.auto_save_id = None

    def on_text_press(self, event):
        # Ctrl 누르고 클릭하면 드래그 시작
        if event.state & 0x4:  # Ctrl 키 체크
            self.drag_data["x"] = event.x_root - self.window.winfo_x()
            self.drag_data["y"] = event.y_root - self.window.winfo_y()

    def on_text_drag(self, event):
        # Ctrl 누르고 드래그하면 창 이동
        if event.state & 0x4:  # Ctrl 키 체크
            x = event.x_root - self.drag_data["x"]
            y = event.y_root - self.drag_data["y"]
            self.window.geometry(f"+{x}+{y}")

    def show_context_menu(self, event):
        menu = tk.Menu(self.window, tearoff=0)
        menu.add_command(label="Cut", command=lambda: self.text_widget.event_generate("<<Cut>>"))
        menu.add_command(label="Copy", command=lambda: self.text_widget.event_generate("<<Copy>>"))
        menu.add_command(label="Paste", command=lambda: self.text_widget.event_generate("<<Paste>>"))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def on_closing(self):
        if self.auto_save_id:
            self.window.after_cancel(self.auto_save_id)
        self.save_to_file()
        self.sticker_data['x'] = self.window.winfo_x()
        self.sticker_data['y'] = self.window.winfo_y()
        self.sticker_data['width'] = self.window.winfo_width()
        self.sticker_data['height'] = self.window.winfo_height()
        self.on_close_callback(self.sticker_data['id'])
        self.window.destroy()
