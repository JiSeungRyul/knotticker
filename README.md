# Knotticker

Windows에서 쓰는 로컬 스티커 메모 앱입니다. 인터넷 없이 동작하므로 폐쇄망 환경에서도 쓸 수 있습니다.

## 주요 기능

- 스티커를 여러 개 띄워 두고, 각각 따로 이동하고 크기를 바꿀 수 있습니다.
- 내용은 입력하는 즉시 자동 저장됩니다.
- 글자는 선택한 부분만 굵게, 기울임, 밑줄, 취소선, 색상을 바꿀 수 있습니다.
- 글꼴과 글자 크기를 스티커별로 설정할 수 있습니다.
- 불릿 목록을 지원하고, Enter를 누르면 다음 줄에도 불릿이 이어집니다.
- 배경색은 파스텔 톤 8가지 중에서 고릅니다.
- 마우스를 올리면 상단과 하단 바가 나타납니다. 드래그로 창을 옮기고, 오른쪽 아래 모서리로 크기를 조절합니다.
- 창을 `x`로 닫아도 노트 목록에 남고, 다음 실행 때 열려 있던 스티커가 다시 열립니다.
- 노트 목록에서 제목과 날짜를 보고, 검색하고, 열고, 삭제할 수 있습니다.
- 트레이(시계 옆) 아이콘에서 새 메모, 목록 열기, 모든 메모 표시/숨기기, 종료를 할 수 있습니다.
- 작업표시줄 버튼으로 각 스티커를 최소화하거나 다시 띄울 수 있습니다.

## 설치 (Windows)

`KnottickerSetup.exe`를 실행하면 됩니다. Python은 필요하지 않습니다.

설치 프로그램은 다음을 수행합니다.
- `%LOCALAPPDATA%\Knotticker\knotticker.exe`에 프로그램을 복사합니다.
- 바탕화면 바로가기를 만듭니다.
- 로그인할 때 자동 실행되도록 시작프로그램 바로가기를 만듭니다.

## 데이터 위치

메모는 `%APPDATA%\Knotticker\stickers.json`에 저장됩니다. 이 파일을 복사하면 메모를 옮길 수 있습니다.

## 개발 환경에서 실행

```bash
pip install -r requirements.txt
python src/main.py
```

## 빌드

```bash
pyinstaller --onefile --windowed --name knotticker --icon src/assets/icon.ico --add-data "src/assets/icon.ico;assets" --hidden-import pystray._win32 src/main.py
pyinstaller --onefile --windowed --name KnottickerSetup --add-data "dist/knotticker.exe;." installer/setup.py
```

빌드가 끝나면 `dist/KnottickerSetup.exe`가 설치 파일입니다.

## 프로젝트 구조

```
src/
  main.py       진입점
  manager.py    노트 목록 창, 트레이 명령 처리
  sticker.py    스티커 창
  storage.py    JSON 저장과 불러오기
  tray.py       트레이 아이콘
  config.py     색상, 글꼴, 아이콘 경로
  assets/       아이콘
installer/
  setup.py      설치 프로그램
```
