import os
import sys
import subprocess

import shutil

# 1. --- DANG KIEM TRA MOI TRUONG ---
print("[*] Dang kiem tra moi truong: Python, Nuitka, GCC...")
mingw_bin = r"C:\msys64\mingw64\bin"
if mingw_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = mingw_bin + os.pathsep + os.environ.get("PATH", "")

# 2. --- DANG DON DEP LICH SU BUILD ---
print("[*] Dang don dep lich su build (dist, .build)...")
build_dir = "dist"
build_work_dir = "MacroDi88.build"
onefile_work_dir = "MacroDi88.onefile-build"

for d in [build_dir, build_work_dir, onefile_work_dir]:
    if os.path.exists(d):
        try: shutil.rmtree(d)
        except Exception: pass

# 3. --- DANG DONG GOI AUTO DETECTOR DI88VP ---
print("[*] Dang dong goi Auto Detector DI88VP...")

cmd = (
    "python -m nuitka "
    "--standalone "
    "--onefile "
    # Tắt nén để né AV và tăng tốc build
    "--onefile-no-compression " 
    "--onefile-tempdir-spec=\"{TEMP}/DI88VP_{TIME}\" "
    "--windows-console-mode=disable "
    "--remove-output "
    "--enable-plugin=pyqt6 "
    "--windows-icon-from-ico=di88vp.ico "
    "--windows-uac-admin "
    "--mingw64 "
    "--lto=yes "
    
    "--company-name=\"DI88-VP ELITE\" "
    "--product-name=\"DI88-VP PUBG MACRO\" "
    "--file-version=1.2.0.0 "
    "--product-version=1.2.0.0 "
    "--file-description=\"Advanced Recoil Control Engine\" "
    "--copyright=\"© 2026 DI88-VP Team. All rights reserved.\" "
    
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
    f"{'--include-data-dir=FullHD=FullHD ' if os.path.exists('FullHD') else ''}"
    f"{'--include-data-dir=2K=2K ' if os.path.exists('2K') else ''}"
    f"{'--include-data-dir=src/gui=src/gui ' if os.path.exists('src/gui') else ''}"
    "--include-data-files=di88vp.ico=di88vp.ico "

    
    "--include-package=src.core "
    "--include-package=src.gui "
    "--include-package=src.detect "
    
    "--output-dir=dist "
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
