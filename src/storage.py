import json
import os
from pathlib import Path
from datetime import datetime
import uuid

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_FILE = DATA_DIR / "stickers.json"

def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)

def load_stickers():
    ensure_data_dir()
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading stickers: {e}")
            return []
    return []

def save_stickers(stickers):
    ensure_data_dir()
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(stickers, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving stickers: {e}")
        return False

def create_sticker(text="", bg_color="#FFFACD", text_color="#2C3E50", font=("Segoe UI", 11)):
    return {
        "id": str(uuid.uuid4()),
        "text": text,
        "bg_color": bg_color,
        "text_color": text_color,
        "font_family": font[0],
        "font_size": font[1],
        "bold": False,
        "italic": False,
        "underline": False,
        "strikethrough": False,
        "always_on_top": False,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "x": 100,
        "y": 100,
        "width": 320,
        "height": 280,
    }

def update_sticker(stickers, sticker_id, **kwargs):
    for sticker in stickers:
        if sticker["id"] == sticker_id:
            sticker.update(kwargs)
            sticker["updated_at"] = datetime.now().isoformat()
            return True
    return False

def delete_sticker(stickers, sticker_id):
    return [s for s in stickers if s["id"] != sticker_id]
