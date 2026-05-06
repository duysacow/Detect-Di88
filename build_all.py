import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BUILD_OUTPUT_DIR = PROJECT_ROOT / "dist"
BUILD_WORK_DIR = PROJECT_ROOT / "MacroDi88.build"
ONEFILE_WORK_DIR = PROJECT_ROOT / "MacroDi88.onefile-build"
ONEFILE_TEMP_SPEC = "{TEMP}/DI88VP_{TIME}"
GAME_PATH_TOKENS = (
    "pubg",
    "tslgame",
    "binaries/win64",
    "steamapps/common/pubg",
)


def _normalize_path(path_value):
    return str(Path(path_value).resolve()).replace("\\", "/").lower()


def _is_disallowed_game_path(path_value):
    normalized = _normalize_path(path_value)
    return any(token in normalized for token in GAME_PATH_TOKENS)


def _ensure_safe_build_paths():
    temp_root = Path(tempfile.gettempdir()).resolve()
    guarded_paths = {
        "project_root": PROJECT_ROOT,
        "build_output_dir": BUILD_OUTPUT_DIR,
        "build_work_dir": BUILD_WORK_DIR,
        "onefile_work_dir": ONEFILE_WORK_DIR,
        "temp_root": temp_root,
    }
    for label, path_value in guarded_paths.items():
        if _is_disallowed_game_path(path_value):
            print(f"[WARN] Blocked unsafe {label}: {path_value}")
            sys.exit(1)

    if BUILD_OUTPUT_DIR != PROJECT_ROOT / "dist":
        print(f"[WARN] Build output must stay inside dist/: {BUILD_OUTPUT_DIR}")
        sys.exit(1)

# 1. --- DANG KIEM TRA MOI TRUONG ---
print("[*] Dang kiem tra moi truong: Python, Nuitka, GCC...")
_ensure_safe_build_paths()
mingw_bin = r"C:\msys64\mingw64\bin"
if mingw_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = mingw_bin + os.pathsep + os.environ.get("PATH", "")

# 2. --- DANG DON DEP LICH SU BUILD ---
print("[*] Dang don dep lich su build (dist, .build)...")
build_dir = str(BUILD_OUTPUT_DIR)
build_work_dir = str(BUILD_WORK_DIR)
onefile_work_dir = str(ONEFILE_WORK_DIR)

for d in [build_dir, build_work_dir, onefile_work_dir]:
    if os.path.exists(d):
        try:
            shutil.rmtree(d)
        except Exception:
            pass

# 3. --- DANG DONG GOI AUTO DETECTOR DI88VP ---
print("[*] Dang dong goi Auto Detector DI88VP...")

cmd = (
    "python -m nuitka "
    "--standalone "
    "--onefile "
    # Tắt nén để né AV và tăng tốc build
    "--onefile-no-compression "
    f'--onefile-tempdir-spec="{ONEFILE_TEMP_SPEC}" '
    "--windows-console-mode=disable "
    "--remove-output "
    "--enable-plugin=pyqt6 "
    "--windows-icon-from-ico=di88vp.ico "
    "--windows-uac-admin "
    "--mingw64 "
    "--lto=yes "
    '--company-name="DI88-VP ELITE" '
    '--product-name="DI88-VP PUBG MACRO" '
    "--file-version=1.2.0.0 "
    "--product-version=1.2.0.0 "
    '--file-description="Advanced Recoil Control Engine" '
    '--copyright="© 2026 DI88-VP Team. All rights reserved." '
    "--include-module=cv2 "
    "--include-module=numpy "
    "--include-module=psutil "
    "--include-module=mss "
    "--include-module=dxcam "
    "--include-module=win32api "
    "--include-module=win32gui "
    "--include-module=win32con "
    "--include-module=win32process "
    "--include-module=win32event "
    "--include-module=ctypes "
    "--include-package=PyQt6 "
    # --- DATA & ASSETS ---
    f"{'--include-data-dir=src/config=src/config ' if os.path.exists('src/config') else ''}"
    f"{'--include-data-dir=src/Template=src/Template ' if os.path.exists('src/Template') else ''}"
    f"{'--include-data-dir=src/gui=src/gui ' if os.path.exists('src/gui') else ''}"
    "--include-data-files=di88vp.ico=di88vp.ico "
    "--include-package=src.core "
    "--include-package=src.detection "
    "--include-package=src.gui "
    "--include-package=src.input "
    "--include-package=src.recoil "
    f'--output-dir="{BUILD_OUTPUT_DIR}" '
    "--output-filename=DI88VP.exe "
    "src/app/main.py"
)

result = subprocess.run(cmd, shell=True, env=os.environ)

if result.returncode == 0:
    print("\n[OK] Build hoan tat!")
    print("      -> File EXE: dist/DI88VP.exe")
    print("\n[SUCCESS] Chuc bac tieu diet ke thu thanh cong!")
else:
    print("\n[ERROR] Co loi xay ra trong qua trinh build. Vui long kiem tra logs.")
