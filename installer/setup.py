import ctypes
import os
import shutil
import subprocess
import sys
from pathlib import Path


def bundled(name):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / name


def make_shortcuts(target, workdir):
    script = (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$target = '{target}'; $workdir = '{workdir}'; "
        "foreach ($dir in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Startup'))) {"
        " $s = $ws.CreateShortcut((Join-Path $dir 'Knotticker.lnk'));"
        " $s.TargetPath = $target; $s.WorkingDirectory = $workdir; $s.IconLocation = \"$target,0\"; $s.Save() }"
    )
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                   check=True, creationflags=subprocess.CREATE_NO_WINDOW)


def main():
    install_dir = Path(os.environ["LOCALAPPDATA"]) / "Knotticker"
    target = install_dir / "knotticker.exe"

    subprocess.run(["taskkill", "/IM", "knotticker.exe", "/F"],
                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)

    install_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bundled("knotticker.exe"), target)
    make_shortcuts(target, install_dir)
    subprocess.Popen([str(target)], cwd=str(install_dir))

    ctypes.windll.user32.MessageBoxW(0, "Knotticker 설치가 끝났습니다.\n바탕화면 바로가기와 자동 실행이 등록되었습니다.",
                                     "Knotticker 설치", 0x40)


if __name__ == "__main__":
    main()
