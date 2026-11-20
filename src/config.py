# Configuration for Knotticker
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    ASSET_DIR = Path(sys._MEIPASS) / "assets"
else:
    ASSET_DIR = Path(__file__).parent / "assets"
ICON_PATH = str(ASSET_DIR / "icon.ico")

# 파스텔톤 색상 팔레트
STICKER_COLORS = [
    "#FFFACD",  # 파스텔 노랑
    "#FFD1DC",  # 파스텔 분홍
    "#ADD8E6",  # 파스텔 파랑
    "#B0E0E6",  # 파스텔 청록
    "#98D98E",  # 파스텔 초록
    "#DDA0DD",  # 파스텔 보라
    "#FFDAB9",  # 파스텔 복숭아
    "#F0E68C",  # 파스텔 카키
]

# 글자 색상 (검 빨 파 노 초 보 회)
TEXT_COLORS = [
    "#1F1F1F",  # 검
    "#D32F2F",  # 빨
    "#1565C0",  # 파
    "#B7950B",  # 노
    "#2E7D32",  # 초
    "#6A1B9A",  # 보
    "#7F8C8D",  # 회
]

# 폰트
FONT_FAMILIES = ["Segoe UI", "Arial", "Courier New", "Times New Roman"]
FONT_SIZES = [9, 10, 11, 12, 13, 14, 16, 18]

# UI 설정
STICKER_WIDTH = 320
STICKER_HEIGHT = 280
STICKER_PADDING = 8
MENU_FADE_TIME = 300  # 메뉴 페이드 타임 (ms)
