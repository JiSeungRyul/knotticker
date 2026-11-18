import tkinter as tk
from tkinter import font
from config import STICKER_COLORS, TEXT_COLORS, FONTS
from storage import update_sticker, save_stickers

class StickerWindow:
    def __init__(self, parent, sticker_data, on_update_callback, on_close_callback):
        self.parent = parent
        self.sticker_data = sticker_data
        self.on_update_callback = on_update_callback
        self.on_close_callback = on_close_callback
        self.selected_text = None

        self.window = tk.Toplevel(parent)
        self.window.title(f"Sticker - {sticker_data['id'][:8]}")
        self.window.geometry(f"{sticker_data['width']}x{sticker_data['height']}+{sticker_data['x']}+{sticker_data['y']}")
        self.window.configure(bg=sticker_data['bg_color'])

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 메뉴 프레임
        self.menu_frame = tk.Frame(self.window, bg="#f0f0f0", height=40)
        self.menu_frame.pack(side=tk.TOP, fill=tk.X)

        # 텍스트 에디터
        font_name = sticker_data['font_family']
        font_size = sticker_data['font_size']
        font_style = "normal"
        if sticker_data['bold'] and sticker_data['italic']:
            font_style = "bold italic"
        elif sticker_data['bold']:
            font_style = "bold"
        elif sticker_data['italic']:
            font_style = "italic"

        self.text_widget = tk.Text(
            self.window,
            font=(font_name, font_size, font_style),
            fg=sticker_data['text_color'],
            bg=sticker_data['bg_color'],
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        self.text_widget.insert("1.0", sticker_data['text'])
        self.text_widget.bind("<KeyRelease>", self.on_text_change)
        self.text_widget.bind("<Button-3>", self.show_context_menu)

        self.create_menu_buttons()
        self.auto_save_id = None

    def create_menu_buttons(self):
        # 색상 버튼
        tk.Label(self.menu_frame, text="Bg:", bg="#f0f0f0").pack(side=tk.LEFT, padx=5, pady=5)
        for color in STICKER_COLORS:
            btn = tk.Button(
                self.menu_frame,
                bg=color,
                width=2,
                height=1,
                command=lambda c=color: self.change_bg_color(c)
            )
            btn.pack(side=tk.LEFT, padx=2)

        tk.Label(self.menu_frame, text="Text:", bg="#f0f0f0").pack(side=tk.LEFT, padx=10, pady=5)
        for color in TEXT_COLORS:
            btn = tk.Button(
                self.menu_frame,
                bg=color,
                fg="white" if color == "#000000" else "black",
                text="A",
                width=2,
                height=1,
                command=lambda c=color: self.change_text_color(c)
            )
            btn.pack(side=tk.LEFT, padx=2)

        # 폰트 선택
        tk.Label(self.menu_frame, text="Font:", bg="#f0f0f0").pack(side=tk.LEFT, padx=10, pady=5)
        self.font_var = tk.StringVar(value=f"{self.sticker_data['font_family']} {self.sticker_data['font_size']}")
        font_menu = tk.OptionMenu(self.menu_frame, self.font_var, *[f"{f[0]} {f[1]}" for f in FONTS], command=self.change_font)
        font_menu.pack(side=tk.LEFT, padx=5)

        # 스타일 버튼
        self.bold_btn = tk.Button(self.menu_frame, text="B", width=2, command=self.toggle_bold)
        self.bold_btn.pack(side=tk.LEFT, padx=2)

        self.italic_btn = tk.Button(self.menu_frame, text="I", width=2, command=self.toggle_italic)
        self.italic_btn.pack(side=tk.LEFT, padx=2)

        self.underline_btn = tk.Button(self.menu_frame, text="U", width=2, command=self.toggle_underline)
        self.underline_btn.pack(side=tk.LEFT, padx=2)

        self.update_button_styles()

    def update_button_styles(self):
        self.bold_btn.config(relief=tk.SUNKEN if self.sticker_data['bold'] else tk.RAISED)
        self.italic_btn.config(relief=tk.SUNKEN if self.sticker_data['italic'] else tk.RAISED)
        self.underline_btn.config(relief=tk.SUNKEN if self.sticker_data['underline'] else tk.RAISED)

    def change_bg_color(self, color):
        self.sticker_data['bg_color'] = color
        self.window.configure(bg=color)
        self.text_widget.configure(bg=color)
        self.on_text_change(None)

    def change_text_color(self, color):
        self.sticker_data['text_color'] = color
        self.text_widget.configure(fg=color)
        self.on_text_change(None)

    def change_font(self, font_str):
        parts = font_str.rsplit(' ', 1)
        font_name = parts[0]
        font_size = int(parts[1])
        self.sticker_data['font_family'] = font_name
        self.sticker_data['font_size'] = font_size
        self.update_text_widget_font()
        self.on_text_change(None)

    def toggle_bold(self):
        self.sticker_data['bold'] = not self.sticker_data['bold']
        self.update_button_styles()
        self.update_text_widget_font()
        self.on_text_change(None)

    def toggle_italic(self):
        self.sticker_data['italic'] = not self.sticker_data['italic']
        self.update_button_styles()
        self.update_text_widget_font()
        self.on_text_change(None)

    def toggle_underline(self):
        self.sticker_data['underline'] = not self.sticker_data['underline']
        self.update_button_styles()
        self.update_text_widget_font()
        self.on_text_change(None)

    def update_text_widget_font(self):
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
            weight="bold" if self.sticker_data['bold'] else "normal",
            overstrike="overstrike" if self.sticker_data['underline'] else ""
        )
        self.text_widget.configure(font=new_font)

    def on_text_change(self, event):
        self.sticker_data['text'] = self.text_widget.get("1.0", tk.END).rstrip('\n')

        if self.auto_save_id:
            self.window.after_cancel(self.auto_save_id)
        self.auto_save_id = self.window.after(1000, self.save_to_file)

    def save_to_file(self):
        self.on_update_callback(self.sticker_data)
        self.auto_save_id = None

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
        # 최종 저장
        self.save_to_file()
        # 창 위치 저장
        self.sticker_data['x'] = self.window.winfo_x()
        self.sticker_data['y'] = self.window.winfo_y()
        self.sticker_data['width'] = self.window.winfo_width()
        self.sticker_data['height'] = self.window.winfo_height()
        self.on_close_callback(self.sticker_data['id'])
        self.window.destroy()
