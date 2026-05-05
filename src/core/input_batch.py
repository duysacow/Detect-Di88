import ctypes

import win32api


# Khai báo cấu trúc dữ liệu chuột cho Windows API
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        (
            "dwExtraInfo",
            (
                ctypes.POINTER(ctypes.c_ulonglong)
                if ctypes.sizeof(ctypes.c_void_p) == 8
                else ctypes.POINTER(ctypes.c_ulong)
            ),
        ),
    ]


# Khai báo cấu trúc dữ liệu bàn phím cho Windows API
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        (
            "dwExtraInfo",
            (
                ctypes.POINTER(ctypes.c_ulonglong)
                if ctypes.sizeof(ctypes.c_void_p) == 8
                else ctypes.POINTER(ctypes.c_ulong)
            ),
        ),
    ]


# Gom dữ liệu input chuột hoặc bàn phím vào một union
class INPUT_u(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


# Đóng gói một lệnh input gửi xuống Windows
class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("u", INPUT_u)]


def batch_send(inputs_list):
    """Engine xử lý chuột/phím siêu tốc cho FastLoot"""
    sw, sh = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)
    n = len(inputs_list)
    input_array = (INPUT * n)()
    for i, item in enumerate(inputs_list):
        if len(item) == 3:
            flags, x, y = item
            nx, ny = int(x * 65535 / sw), int(y * 65535 / sh)
            input_array[i].type = 0
            input_array[i].u.mi = MOUSEINPUT(nx, ny, 0, flags, 0, None)
        elif len(item) == 2:
            scan, flags = item
            input_array[i].type = 1
            input_array[i].u.ki = KEYBDINPUT(0, scan, flags | 0x0008, 0, None)
    ctypes.windll.user32.SendInput(n, ctypes.pointer(input_array), ctypes.sizeof(INPUT))
