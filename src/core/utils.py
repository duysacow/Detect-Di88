import ctypes
import os
import sys
import win32gui
import win32process
import psutil


def is_admin():
    """Kiểm tra quyền Administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


_is_game_active_cache = False
_last_check_time = 0
_last_hwnd = 0

_last_game_hwnd = 0


def get_game_hwnd():
    """Lấy HWND của cửa sổ PUBG hiện tại (Có cache)"""
    global _last_game_hwnd
    import time

    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return _last_game_hwnd

    # Kiểm tra nhanh
    class_name = win32gui.GetClassName(hwnd)
    title = win32gui.GetWindowText(hwnd)
    if class_name == "UnrealWindow" and ("PUBG" in title or "PLAYERUNKNOWN" in title):
        _last_game_hwnd = hwnd
        return hwnd
    return _last_game_hwnd  # Trả về HWND cũ nếu cửa sổ hiện tại ko phải game


def is_game_active():
    """
    Kiểm tra cực nhanh cửa sổ PUBG.
    Loại bỏ psutil để tránh gây micro-stutter (khựng khung hình).
    """
    global _last_hwnd, _is_game_active_cache
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return False

        # Nếu vẫn là cửa sổ cũ -> Trả về cache ngay (Siêu nhanh)
        if hwnd == _last_hwnd:
            return _is_game_active_cache

        _last_hwnd = hwnd
        class_name = win32gui.GetClassName(hwnd)

        # PUBG dùng UnrealWindow, chỉ cần check Class và Title là đủ an toàn & cực nhẹ
        if class_name == "UnrealWindow":
            title = win32gui.GetWindowText(hwnd)
            if "PUBG" in title or "PLAYERUNKNOWN" in title:
                _is_game_active_cache = True
                return True

        _is_game_active_cache = False
        return False
    except:
        return False


def set_high_dpi():
    """Tối ưu hóa hiển thị DPI cho ứng dụng GUI"""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def get_app_path():
    """Lấy đường dẫn thư mục gốc của ứng dụng"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))
