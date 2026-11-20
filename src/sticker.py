import ctypes
import tkinter as tk
from tkinter import font
from config import STICKER_COLORS, TEXT_COLORS, FONT_FAMILIES, FONT_SIZES, ICON_PATH

BAR_H = 26
POLL_MS = 120
BTN_FONT = ("Segoe UI", 9)
MIN_W, MIN_H = 180, 140
MARKERS = ("bold", "italic", "underline", "strike")
FMT_TAGS = {
    (False, False): "fmt_n",
    (True, False): "fmt_b",
    (False, True): "fmt_i",
    (True, True): "fmt_bi",
}
BULLET = "• "
TAB_PX = "20"
SWATCH_PX = 14

GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
SW_MINIMIZE = 6
SW_RESTORE = 9
CORNER_RADIUS = 10
LR_LOADFROMFILE = 0x00000010
IMAGE_ICON = 1
WM_SETICON = 0x0080
ICON_SMALL = 0
ICON_BIG = 1
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32


def native_handle(window):
    return user32.GetParent(window.winfo_id())


def make_swatch(parent, color, command, size=SWATCH_PX):
    swatch = tk.Frame(parent, width=size, height=size, bg=color, cursor="hand2", highlightthickness=0)
    swatch.pack_propagate(False)
    swatch.bind("<Button-1>", lambda e: command())
    return swatch


def shade(hex_color, amount):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    if amount < 0:
        factor = 1 + amount
        return "#{:02X}{:02X}{:02X}".format(*(int(c * factor) for c in (r, g, b)))
    return "#{:02X}{:02X}{:02X}".format(*(min(255, int(c + (255 - c) * amount)) for c in (r, g, b)))


class StickerWindow:
    def __init__(self, parent, sticker_data, on_update_callback, on_close_callback,
                 on_new_callback, on_list_callback, on_delete_callback):
        self.sticker_data = sticker_data
        self.on_update_callback = on_update_callback
        self.on_close_callback = on_close_callback
        self.on_new_callback = on_new_callback
        self.on_list_callback = on_list_callback
        self.on_delete_callback = on_delete_callback
        self.auto_save_id = None
        self.bars_shown = False
        self.drag_offset = (0, 0)
        self.resize_origin = None
        self.bar_frames = []
        self.bar_buttons = []

        self.window = tk.Toplevel(parent)
        self.window.overrideredirect(True)
        self.window.geometry(
            f"{sticker_data['width']}x{sticker_data['height']}+{sticker_data['x']}+{sticker_data['y']}"
        )
        self.window.attributes('-topmost', sticker_data.get('always_on_top', False))
        self.window.title(sticker_data.get('title', 'Untitled'))
        self.window.iconbitmap(ICON_PATH)
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.container = tk.Frame(self.window, highlightthickness=0)
        self.container.pack(fill=tk.BOTH, expand=True)

        self.title_entry = tk.Entry(self.container, border=0, highlightthickness=0,
                                    font=("Segoe UI", 10, "bold"))
        self.title_entry.pack(fill=tk.X, padx=12, pady=(BAR_H + 4, 2))
        self.title_entry.insert(0, sticker_data.get('title', 'Untitled'))
        self.title_entry.bind("<KeyRelease>", self.on_title_change)
        self.title_entry.bind("<Return>", lambda e: self.text_widget.focus())

        self.separator = tk.Frame(self.container, height=1, highlightthickness=0)
        self.separator.pack(fill=tk.X, padx=12, pady=(0, 4))

        self.scroll_canvas = tk.Canvas(self.container, width=6, highlightthickness=0, bd=0)
        self.scroll_canvas.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, BAR_H), padx=(0, 3))
        self.scroll_thumb = self.scroll_canvas.create_rectangle(0, 0, 0, 0, width=0)
        self.scroll_canvas.bind("<ButtonPress-1>", self.scroll_press)
        self.scroll_canvas.bind("<B1-Motion>", self.scroll_press)

        self.text_widget = tk.Text(self.container, wrap=tk.WORD, padx=12, pady=6,
                                   border=0, highlightthickness=0, undo=True,
                                   tabs=(TAB_PX,), yscrollcommand=self.on_yscroll)
        self.text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, BAR_H))
        self.text_widget.insert("1.0", sticker_data['text'])
        self.text_widget.bind("<KeyRelease>", self.on_text_change)
        self.text_widget.bind("<Return>", self.on_return)
        self.text_widget.bind("<Button-3>", self.show_context_menu)
        self.text_widget.tag_configure("underline", underline=True)
        self.text_widget.tag_configure("strike", overstrike=True)
        self.load_styles()

        self.build_top_bar()
        self.build_bottom_bar()
        self.build_bg_palette()

        self.apply_colors()
        self.apply_format()
        self.show_in_taskbar()
        self.apply_round_corners()
        self.window.after(POLL_MS, self.poll_hover)

    def show_in_taskbar(self):
        self.window.update_idletasks()
        hwnd = native_handle(self.window)
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW)
        self.window.withdraw()
        self.window.deiconify()
        self.set_taskbar_icon()

    def set_taskbar_icon(self):
        hwnd = native_handle(self.window)
        for size_flag, target in ((ICON_SMALL, 16), (ICON_BIG, 32)):
            hicon = user32.LoadImageW(None, ICON_PATH, IMAGE_ICON, target, target, LR_LOADFROMFILE)
            if hicon:
                user32.SendMessageW(hwnd, WM_SETICON, size_flag, hicon)

    def apply_round_corners(self, w=None, h=None):
        w = w or self.window.winfo_width()
        h = h or self.window.winfo_height()
        if w <= 1 or h <= 1:
            return
        region = gdi32.CreateRoundRectRgn(0, 0, w + 1, h + 1, CORNER_RADIUS * 2, CORNER_RADIUS * 2)
        user32.SetWindowRgn(native_handle(self.window), region, True)

    def minimize(self):
        user32.ShowWindow(native_handle(self.window), SW_MINIMIZE)

    def restore(self):
        user32.ShowWindow(native_handle(self.window), SW_RESTORE)
        self.window.lift()

    def hide(self):
        self.hide_bars()
        self.window.withdraw()

    def show(self):
        self.window.deiconify()
        self.restore()

    def bar_button(self, parent, text, command, font_spec=BTN_FONT):
        btn = tk.Button(parent, text=text, command=command, font=font_spec, relief=tk.FLAT, bd=0,
                        padx=6, pady=0, cursor="hand2", highlightthickness=0)
        self.bar_buttons.append(btn)
        return btn

    def make_bar(self):
        frame = tk.Frame(self.window, height=BAR_H, highlightthickness=0)
        frame.pack_propagate(False)
        frame.bind("<ButtonPress-1>", self.start_drag)
        frame.bind("<B1-Motion>", self.drag)
        self.bar_frames.append(frame)
        return frame

    def build_top_bar(self):
        self.top_bar = self.make_bar()
        self.bar_button(self.top_bar, "+", self.on_new_callback, ("Segoe UI", 11)).pack(side=tk.LEFT)
        self.bar_button(self.top_bar, "x", self.on_closing, ("Segoe UI", 10)).pack(side=tk.RIGHT)
        self.bar_button(self.top_bar, "-", self.minimize, ("Segoe UI", 10, "bold")).pack(side=tk.RIGHT)
        self.bar_button(self.top_bar, "≡", self.on_list_callback, ("Segoe UI", 10, "bold")).pack(side=tk.RIGHT)
        self.bg_btn = make_swatch(self.top_bar, self.sticker_data['bg_color'], self.toggle_bg_palette)
        self.bg_btn.pack(side=tk.RIGHT, padx=(0, 4), pady=6)

    def build_bottom_bar(self):
        self.bottom_bar = self.make_bar()
        grip = tk.Label(self.bottom_bar, text="◢", font=("Segoe UI", 8), cursor="size_nw_se",
                        bd=0, highlightthickness=0)
        grip.pack(side=tk.RIGHT, padx=(0, 4))
        grip.bind("<ButtonPress-1>", self.resize_start)
        grip.bind("<B1-Motion>", self.resize_drag)
        self.bar_frames.append(grip)
        self.grip = grip

        self.style_buttons = {}
        for key, label, font_spec in (
            ("bold", "B", ("Segoe UI", 9, "bold")),
            ("italic", "I", ("Segoe UI", 9, "italic")),
            ("underline", "U", ("Segoe UI", 9, "underline")),
            ("strike", "S", ("Segoe UI", 9, "overstrike")),
        ):
            btn = self.bar_button(self.bottom_bar, label, lambda k=key: self.toggle_style(k), font_spec)
            btn.pack(side=tk.LEFT)
            self.style_buttons[key] = btn

        self.bar_button(self.bottom_bar, "•", self.toggle_bullet, ("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.family_btn = self.bar_button(self.bottom_bar, "Aa", self.open_family_menu, ("Segoe UI", 9))
        self.family_btn.pack(side=tk.LEFT)
        self.size_btn = self.bar_button(self.bottom_bar, str(self.sticker_data['font_size']),
                                        self.open_size_menu, ("Segoe UI", 9))
        self.size_btn.pack(side=tk.LEFT)

        self.color_btn = make_swatch(self.bottom_bar, self.sticker_data['text_color'], self.toggle_palette)
        self.color_btn.pack(side=tk.LEFT, padx=(6, 0), pady=6)

        self.palette = tk.Frame(self.window, highlightthickness=0)
        for color in TEXT_COLORS:
            make_swatch(self.palette, color, lambda c=color: self.pick_text_color(c)).pack(side=tk.LEFT, padx=3, pady=5)

    def build_bg_palette(self):
        self.bg_palette = tk.Frame(self.window, highlightthickness=0)
        for color in STICKER_COLORS:
            make_swatch(self.bg_palette, color, lambda c=color: self.pick_bg_color(c)).pack(side=tk.LEFT, padx=3, pady=5)

    def popup_above_bar(self, menu, anchor, entry_count):
        y = self.bottom_bar.winfo_rooty() - entry_count * 22 - 8
        try:
            menu.tk_popup(anchor.winfo_rootx(), y)
        finally:
            menu.grab_release()

    def open_family_menu(self):
        menu = tk.Menu(self.window, tearoff=0)
        for name in FONT_FAMILIES:
            menu.add_command(label=name, command=lambda n=name: self.change_font_family(n))
        self.popup_above_bar(menu, self.family_btn, len(FONT_FAMILIES))

    def open_size_menu(self):
        menu = tk.Menu(self.window, tearoff=0)
        for size in FONT_SIZES:
            menu.add_command(label=str(size), command=lambda s=size: self.change_font_size(s))
        self.popup_above_bar(menu, self.size_btn, len(FONT_SIZES))

    def toggle_bg_palette(self):
        if self.bg_palette.winfo_ismapped():
            self.bg_palette.place_forget()
        else:
            self.bg_palette.place(relx=1.0, y=BAR_H, x=-6, anchor="ne")
            self.bg_palette.lift()

    def pick_bg_color(self, color):
        self.bg_palette.place_forget()
        self.bg_btn.configure(bg=color)
        self.change_bg_color(color)

    def toggle_palette(self):
        if self.palette.winfo_ismapped():
            self.palette.place_forget()
        else:
            self.palette.place(relx=0.5, rely=1.0, y=-BAR_H, anchor="s")
            self.palette.lift()

    def pick_text_color(self, color):
        self.palette.place_forget()
        self.color_btn.configure(bg=color)
        self.change_text_color(color)

    def poll_hover(self):
        try:
            if not self.window.winfo_exists():
                return
            px, py = self.window.winfo_pointerxy()
            under = self.window.winfo_containing(px, py)
            inside = under is not None and (
                under == self.window or str(under).startswith(str(self.window) + ".")
            )
            if inside:
                self.show_bars()
            else:
                self.hide_bars()
            self.window.after(POLL_MS, self.poll_hover)
        except tk.TclError:
            return

    def show_bars(self):
        if self.bars_shown:
            return
        self.top_bar.place(x=0, y=0, relwidth=1, height=BAR_H)
        self.bottom_bar.place(x=0, rely=1.0, y=0, anchor="sw", relwidth=1, height=BAR_H)
        self.top_bar.lift()
        self.bottom_bar.lift()
        self.bars_shown = True

    def hide_bars(self):
        if not self.bars_shown:
            return
        self.top_bar.place_forget()
        self.bottom_bar.place_forget()
        self.palette.place_forget()
        self.bg_palette.place_forget()
        self.bars_shown = False

    def start_drag(self, event):
        self.drag_offset = (event.x_root - self.window.winfo_x(), event.y_root - self.window.winfo_y())

    def drag(self, event):
        self.window.geometry(f"+{event.x_root - self.drag_offset[0]}+{event.y_root - self.drag_offset[1]}")

    def resize_start(self, event):
        self.resize_origin = (event.x_root, event.y_root, self.window.winfo_width(), self.window.winfo_height())

    def resize_drag(self, event):
        x0, y0, w0, h0 = self.resize_origin
        w = max(MIN_W, w0 + event.x_root - x0)
        h = max(MIN_H, h0 + event.y_root - y0)
        self.window.geometry(f"{w}x{h}+{self.window.winfo_x()}+{self.window.winfo_y()}")
        self.apply_round_corners(w, h)
        self.refresh_thumb()

    def on_yscroll(self, first, last):
        self.refresh_thumb()

    def refresh_thumb(self):
        first, last = self.text_widget.yview()
        height = self.scroll_canvas.winfo_height()
        if last - first >= 1.0 or height <= 1:
            self.scroll_canvas.itemconfigure(self.scroll_thumb, fill="")
            return
        self.scroll_canvas.coords(self.scroll_thumb, 0, first * height, 6, last * height)
        self.scroll_canvas.itemconfigure(self.scroll_thumb, fill=shade(self.sticker_data['bg_color'], -0.3))

    def scroll_press(self, event):
        height = self.scroll_canvas.winfo_height()
        first, last = self.text_widget.yview()
        span = last - first
        self.text_widget.yview_moveto(max(0.0, min(1.0 - span, event.y / height - span / 2)))

    def apply_colors(self):
        bg = self.sticker_data['bg_color']
        fg = self.sticker_data['text_color']
        bar = shade(bg, -0.12)
        bar_hover = shade(bg, -0.22)

        self.window.configure(bg=bg)
        self.container.configure(bg=bg)
        self.title_entry.configure(bg=bg, fg=fg, insertbackground=fg)
        self.separator.configure(bg=shade(bg, -0.2))
        self.scroll_canvas.configure(bg=bg)
        self.text_widget.configure(bg=bg, fg=fg, insertbackground=fg)
        self.refresh_thumb()

        for frame in self.bar_frames:
            frame.configure(bg=bar)
        for btn in self.bar_buttons:
            btn.configure(bg=bar, fg=fg, activebackground=bar_hover, activeforeground=fg)

        self.palette.configure(bg=bar)
        self.bg_palette.configure(bg=bar)

    def apply_format(self):
        d = self.sticker_data
        base = {"family": d['font_family'], "size": d['font_size']}
        self._fonts = {
            (False, False): font.Font(**base),
            (True, False): font.Font(weight="bold", **base),
            (False, True): font.Font(slant="italic", **base),
            (True, True): font.Font(weight="bold", slant="italic", **base),
        }
        for key, tag in FMT_TAGS.items():
            self.text_widget.tag_configure(tag, font=self._fonts[key])
        self.text_widget.configure(font=self._fonts[(False, False)])
        self.refresh_fonts()

    def char_positions(self, start, end):
        t = self.text_widget
        pos = t.index(start)
        stop = t.index(end)
        while t.compare(pos, "<", stop):
            yield pos
            pos = t.index(f"{pos}+1c")

    def refresh_fonts(self, start="1.0", end="end"):
        t = self.text_widget
        for pos in self.char_positions(start, end):
            nxt = t.index(f"{pos}+1c")
            names = t.tag_names(pos)
            for tag in FMT_TAGS.values():
                t.tag_remove(tag, pos, nxt)
            t.tag_add(FMT_TAGS[("bold" in names, "italic" in names)], pos, nxt)

    def toggle_style(self, marker):
        t = self.text_widget
        sel = t.tag_ranges("sel")
        if not sel:
            return
        start, end = sel
        covered = all(marker in t.tag_names(pos) for pos in self.char_positions(start, end))
        if covered:
            t.tag_remove(marker, start, end)
        else:
            t.tag_add(marker, start, end)
        if marker in ("bold", "italic"):
            self.refresh_fonts(start, end)
        self.schedule_save()

    def toggle_bullet(self):
        t = self.text_widget
        sel = t.tag_ranges("sel")
        if sel:
            first_line = int(str(sel[0]).split('.')[0])
            last_line = int(str(sel[1]).split('.')[0])
        else:
            first_line = last_line = int(t.index("insert").split('.')[0])
        lines = range(first_line, last_line + 1)
        all_bulleted = all(t.get(f"{n}.0", f"{n}.0+2c") == BULLET for n in lines)
        for n in lines:
            start = f"{n}.0"
            if all_bulleted:
                t.delete(start, f"{start}+2c")
            else:
                t.insert(start, BULLET)
        self.schedule_save()

    def on_return(self, event):
        t = self.text_widget
        line_start = t.index("insert linestart")
        line_text = t.get(line_start, "insert lineend")
        if not line_text.startswith(BULLET):
            return None
        if line_text.strip() == BULLET.strip():
            t.delete(line_start, f"{line_start}+2c")
            return None
        t.insert("insert", "\n" + BULLET)
        return "break"

    def color_tag(self, color):
        name = "c_" + color[1:]
        self.text_widget.tag_configure(name, foreground=color)
        return name

    def apply_text_color(self, color, start, end):
        t = self.text_widget
        for other in TEXT_COLORS:
            t.tag_remove(self.color_tag(other), start, end)
        t.tag_add(self.color_tag(color), start, end)
        self.schedule_save()

    def collect_styles(self):
        t = self.text_widget
        styles = []
        color_names = [self.color_tag(c) for c in TEXT_COLORS]
        for marker in list(MARKERS) + color_names:
            ranges = t.tag_ranges(marker)
            for i in range(0, len(ranges), 2):
                styles.append({
                    "tag": marker,
                    "start": self.offset(ranges[i]),
                    "end": self.offset(ranges[i + 1]),
                })
        return styles

    def offset(self, index):
        result = self.text_widget.count("1.0", index, "chars")
        return result[0] if result else 0

    def load_styles(self):
        t = self.text_widget
        for style in self.sticker_data.get('styles', []):
            tag = style['tag']
            if tag in MARKERS:
                t.tag_add(tag, f"1.0+{style['start']}c", f"1.0+{style['end']}c")
            elif tag.startswith("c_") and ("#" + tag[2:]) in TEXT_COLORS:
                self.color_tag("#" + tag[2:])
                t.tag_add(tag, f"1.0+{style['start']}c", f"1.0+{style['end']}c")

    def change_bg_color(self, color):
        self.sticker_data['bg_color'] = color
        self.apply_colors()
        self.schedule_save()

    def change_text_color(self, color):
        sel = self.text_widget.tag_ranges("sel")
        if sel:
            self.apply_text_color(color, *sel)
            return
        self.sticker_data['text_color'] = color
        self.apply_colors()
        self.schedule_save()

    def change_font_family(self, name):
        self.sticker_data['font_family'] = name
        self.apply_format()
        self.schedule_save()

    def change_font_size(self, size):
        self.sticker_data['font_size'] = size
        self.size_btn.configure(text=str(size))
        self.apply_format()
        self.schedule_save()

    def toggle_always_on_top(self):
        self.sticker_data['always_on_top'] = not self.sticker_data.get('always_on_top', False)
        self.window.attributes('-topmost', self.sticker_data['always_on_top'])
        self.schedule_save()

    def on_title_change(self, event):
        self.sticker_data['title'] = self.title_entry.get() or 'Untitled'
        self.window.title(self.sticker_data['title'])
        self.schedule_save()

    def on_text_change(self, event):
        self.schedule_save()

    def schedule_save(self):
        if self.auto_save_id:
            self.window.after_cancel(self.auto_save_id)
        self.auto_save_id = self.window.after(1000, self.save_to_file)

    def save_to_file(self):
        self.sticker_data['text'] = self.text_widget.get("1.0", tk.END).rstrip('\n')
        self.sticker_data['styles'] = self.collect_styles()
        self.auto_save_id = None
        self.on_update_callback(self.sticker_data)

    def show_context_menu(self, event):
        menu = tk.Menu(self.window, tearoff=0)
        menu.add_command(label="Cut", command=lambda: self.text_widget.event_generate("<<Cut>>"))
        menu.add_command(label="Copy", command=lambda: self.text_widget.event_generate("<<Copy>>"))
        menu.add_command(label="Paste", command=lambda: self.text_widget.event_generate("<<Paste>>"))
        menu.add_separator()
        pinned = tk.BooleanVar(value=self.sticker_data.get('always_on_top', False))
        menu.add_checkbutton(label="Always on top", variable=pinned, command=self.toggle_always_on_top)
        menu.add_separator()
        menu.add_command(label="노트 삭제", command=lambda: self.on_delete_callback(self.sticker_data['id']))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def on_closing(self):
        if self.auto_save_id:
            self.window.after_cancel(self.auto_save_id)
        self.sticker_data['x'] = self.window.winfo_x()
        self.sticker_data['y'] = self.window.winfo_y()
        self.sticker_data['width'] = self.window.winfo_width()
        self.sticker_data['height'] = self.window.winfo_height()
        self.save_to_file()
        self.on_close_callback(self.sticker_data['id'])
        self.window.destroy()
