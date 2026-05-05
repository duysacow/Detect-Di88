import sys
import os
import time
import ctypes
import subprocess
import copy
import json
import threading
import re
import math
import hashlib
import concurrent.futures
import zlib
from pathlib import Path

import cv2
import numpy as np
import psutil
import ClassBaseRecoil as BaseRecoilDataModule
import win32api
import win32con
import win32gui
from pynput import keyboard, mouse
try:
    import mss
except Exception:
    mss = None
try:
    import dxcam
except Exception:
    dxcam = None

try:
    cv2.setNumThreads(1)
    cv2.ocl.setUseOpenCL(False)
except Exception:
    pass

from ctypes import wintypes
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint, QSize, QEvent, QObject, QRectF
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPen, QBrush, QKeySequence, QPixmap, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QGridLayout, QGroupBox, QComboBox, QStackedWidget, QDialog, QSlider,
    QGraphicsDropShadowEffect, QMessageBox, QSystemTrayIcon, QMenu
)

# TẮT TOÀN BỘ THÔNG BÁO RÁC CỦA QT VÀ HỆ THỐNG
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
UI_ONLY_MODE = False


class EngineCoreImageView(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.POINTER(ctypes.c_uint8)),
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
        ("channels", ctypes.c_int),
        ("stride", ctypes.c_int),
    ]


class EngineCoreFastLootConfig(ctypes.Structure):
    _fields_ = [
        ("enabled", ctypes.c_int),
        ("loot_key_vk", ctypes.c_ushort),
        ("inventory_key_vk", ctypes.c_ushort),
        ("screen_width", ctypes.c_int),
        ("screen_height", ctypes.c_int),
        ("source_x", ctypes.c_int),
        ("source_y", ctypes.c_int),
        ("source_row_step", ctypes.c_int),
        ("target_x", ctypes.c_int),
        ("target_y", ctypes.c_int),
        ("sweep_count", ctypes.c_int),
        ("inventory_open_delay_ms", ctypes.c_int),
        ("post_drop_delay_ms", ctypes.c_int),
        ("loop_delay_ms", ctypes.c_int),
        ("require_game_window", ctypes.c_int),
    ]


class EngineCoreSlideConfig(ctypes.Structure):
    _fields_ = [
        ("enabled", ctypes.c_int),
        ("trigger_vk", ctypes.c_ushort),
        ("crouch_vk", ctypes.c_ushort),
        ("shift_vk", ctypes.c_ushort),
        ("shift_left_vk", ctypes.c_ushort),
        ("shift_right_vk", ctypes.c_ushort),
        ("forward_vk", ctypes.c_ushort),
        ("left_vk", ctypes.c_ushort),
        ("right_vk", ctypes.c_ushort),
        ("cooldown_ms", ctypes.c_int),
        ("release_to_crouch_delay_ms", ctypes.c_int),
        ("first_crouch_release_delay_ms", ctypes.c_int),
        ("crouch_repress_delay_ms", ctypes.c_int),
        ("final_restore_delay_ms", ctypes.c_int),
        ("trailing_cleanup_delay_ms", ctypes.c_int),
        ("require_game_window", ctypes.c_int),
    ]

APP_STYLE_QSS = '/* MAIN WINDOW CONTAINER */\nQFrame#MainContainer {\n    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #252525, stop:1 #0f0f0f);\n    border-radius: 15px; \n    border: 1px solid #444;\n}\n\n/* TITLE BAR */\nQFrame#TitleBar {\n    background-color: transparent;\n    border: none;\n}\n\nQLabel#AppTitle {\n    color: qlineargradient(x1:0, y1:0.5, x2:1, y2:0.5, stop:0 #FFFFFF, stop:1 #A0A0A0);\n    background: transparent;\n    text-transform: uppercase;\n    font-size: 13px;\n    font-weight: bold;\n}\n\n/* WINDOW CONTROLS */\nQPushButton#MinBtn {\n    background: #333;\n    color: white;\n    border-radius: 10px;\n    font-weight: bold;\n    font-size: 10px;\n}\nQPushButton#MinBtn:hover {\n    background: #555;\n}\n\nQPushButton#CloseBtn {\n    background: #333;\n    color: #ff4444;\n    border-radius: 10px;\n    font-weight: bold;\n    font-size: 10px;\n}\nQPushButton#CloseBtn:hover {\n    background: #ff4444;\n    color: white;\n}\n\n/* PANELS (GUN 1, GUN 2) */\nQFrame.PanelFrame {\n    background-color: #1e1e1e;\n    border-radius: 10px;\n    border: 1px solid #333;\n}\n\nQLabel.PanelHeader {\n    font-size: 13px;\n    font-weight: 900;\n    letter-spacing: 2px;\n    background-color: rgba(0,0,0,0.2); \n    border-radius: 5px;\n    padding: 3px;\n}\n\n/* DATA ROWS (Name, Scope, etc.) */\nQLabel.RowLabel {\n    color: #888;\n    font-size: 11px;\n    font-weight: bold;\n}\n\nQLabel.ValueLabel {\n    color: #fff;\n    font-size: 11px;\n    font-weight: bold;\n    background-color: #252525;\n    padding: 2px 5px;\n    border-radius: 3px;\n}\n\n/* STATUS & INFO LABELS */\nQLabel#StanceLabel {\n    background-color: #2a2a2a;\n    color: #FFFF00;\n    font-size: 13px;\n    font-weight: bold;\n    border: 1px solid #444;\n    border-radius: 8px;\n}\n\nQLabel#DetectInfoLabel {\n    background-color: #2a2a2a;\n    color: #00FFFF;\n    font-size: 11px;\n    font-weight: bold;\n    border: 1px solid #444;\n    border-radius: 8px;\n}\n\n/* BUTTONS */\nQPushButton#MacroBtn {\n    border-radius: 8px;\n    font-weight: bold;\n    font-size: 14px;\n}\n\n/* SETTING ROWS */\nQLabel.SettingLabel {\n    background-color: #2a2a2a;\n    color: #bbb; \n    border: 1px solid #444;\n    border-radius: 4px;\n    padding: 2px;\n    font-size: 11px;\n    font-weight: bold;\n}\n\nQPushButton.SettingBtn {\n    background-color: #2a2a2a;\n    color: #ccc; \n    border: 1px solid #444;\n    border-radius: 4px;\n    font-size: 11px;\n}\nQPushButton.SettingBtn:hover {\n    border: 1px solid #666;\n    background-color: #333;\n}\n\n/* CAPTURE MODE BUTTONS */\nQPushButton.CaptureBtn {\n    background-color: #2a2a2a;\n    color: #888;\n    border: 1px solid #444;\n    border-radius: 4px;\n    font-size: 11px;\n    font-weight: bold;\n}\nQPushButton.CaptureBtn:hover {\n    background-color: #333;\n    border: 1px solid #555;\n}\nQPushButton.CaptureBtn[active="true"] {\n    background-color: #ff6b6b;\n    color: white;\n    border: 1px solid #ff5252;\n    font-weight: bold;\n}\n\n/* SPECIAL TOGGLE BUTTONS */\nQPushButton#OverlayToggleBtn[state="ON"], \nQPushButton#FastLootToggleBtn[state="ON"] {\n    background-color: #00FF00;\n    color: #000;\n    border: 2px solid #00AA00;\n    border-radius: 6px;\n    font-size: 12px;\n    font-weight: bold;\n}\nQPushButton#OverlayToggleBtn[state="OFF"], \nQPushButton#FastLootToggleBtn[state="OFF"] {\n    background-color: #666;\n    color: #ccc;\n    border: 2px solid #444;\n    border-radius: 6px;\n    font-size: 12px;\n    font-weight: bold;\n}\n\nQPushButton#CrosshairToggleBtn[checked="true"] {\n    background-color: #00FFFF;\n    color: #000;\n    border-radius: 4px;\n    font-size: 10px;\n    font-weight: bold;\n}\nQPushButton#CrosshairToggleBtn[checked="false"] {\n    background-color: #444;\n    color: #aaa;\n    border-radius: 4px;\n    font-size: 10px;\n    font-weight: bold;\n}\n\nQPushButton#AdsHideBtn {\n    background-color: #FF00FF;\n    color: #fff;\n    border-radius: 4px;\n    font-size: 10px;\n    font-weight: bold;\n}\n\n/* COMBO BOXES */\nQComboBox {\n    background-color: #2a2a2a;\n    color: white;\n    border: 1px solid #444;\n    border-radius: 4px;\n    font-size: 10px;\n    padding: 1px 5px;\n}\n\n/* FOOTER BUTTONS */\nQPushButton#DefaultBtn {\n    background-color: #333;\n    color: white;\n    border: none;\n    border-radius: 4px;\n    font-weight: bold;\n    font-size: 10px;\n}\nQPushButton#DefaultBtn:hover {\n    background-color: #444;\n}\n\nQPushButton#SaveBtn {\n    background-color: #ff6b6b;\n    color: white;\n    border: none;\n    border-radius: 4px;\n    font-weight: bold;\n    font-size: 10px;\n}\nQPushButton#SaveBtn:hover {\n    background-color: #ff5252;\n}\n\nQLabel#CrosshairSectionTitle {\n    color: #aaaaaa;\n    font-size: 11px;\n    font-weight: bold;\n    margin-top: 5px;\n    margin-bottom: 2px;\n}\n'


def get_resource_path(relative_path):
    """
    Get the absolute path to a resource, works for dev and for Nuitka/PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        # Chế độ đóng gói: __file__ sẽ trỏ vào thư mục tạm mà Nuitka xả nén ra
        base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)
    
    # Chế độ phát triển (Local)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


# ===== Utils.py =====

import ctypes
import os
import sys
import win32gui
import win32process
import psutil

def is_admin():
    """M? t? ?? ???c l?m s?ch."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

_is_game_active_cache = False
_last_check_time = 0
_last_hwnd = 0

_last_game_hwnd = 0

def get_game_hwnd():
    """M? t? ?? ???c l?m s?ch."""
    global _last_game_hwnd
    import time
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd: return _last_game_hwnd
    
    # Đã làm sạch chú thích lỗi mã hóa.
    class_name = win32gui.GetClassName(hwnd)
    title = win32gui.GetWindowText(hwnd)
    if class_name == "UnrealWindow" and ("PUBG" in title or "PLAYERUNKNOWN" in title):
        _last_game_hwnd = hwnd
        return hwnd
    return _last_game_hwnd  # Đã làm sạch chú thích lỗi mã hóa.

def is_game_active():
    """
    Kiểm tra cực nhanh cửa sổ PUBG.
    Loại bỏ psutil để tránh gây micro-stutter (khựng khung hình).
    """
    global _last_hwnd, _is_game_active_cache
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd: return False
        
        # Đã làm sạch chú thích lỗi mã hóa.
        if hwnd == _last_hwnd: return _is_game_active_cache
            
        _last_hwnd = hwnd
        class_name = win32gui.GetClassName(hwnd)
        
        # Đã làm sạch chú thích lỗi mã hóa.
        if class_name == "UnrealWindow":
            title = win32gui.GetWindowText(hwnd)
            if "PUBG" in title or "PLAYERUNKNOWN" in title:
                _is_game_active_cache = True
                return True
        
        _is_game_active_cache = False
        return False
    except:
        return False


def gui_key_to_vk(key_name: str) -> int:
    key = str(key_name or "f1").strip().lower().replace(" ", "_")
    mapping = {
        "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73, "f5": 0x74, "f6": 0x75,
        "f7": 0x76, "f8": 0x77, "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
        "home": 0x24, "insert": 0x2D, "delete": 0x2E, "end": 0x23,
        "shift": 0x10, "shift_l": 0xA0, "shift_r": 0xA1,
        "ctrl": 0x11, "ctrl_l": 0xA2, "ctrl_r": 0xA3,
        "alt": 0x12, "alt_l": 0xA4, "alt_r": 0xA5,
        "space": 0x20, "tab": 0x09, "esc": 0x1B, "escape": 0x1B,
        "caps_lock": 0x14, "capslock": 0x14,
        "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
        "comma": 0xBC,
    }
    if key in mapping:
        return mapping[key]
    if len(key) == 1:
        return ord(key.upper())
    return 0x70


def set_high_dpi():
    """M? t? ?? ???c l?m s?ch."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

def get_app_path():
    """M? t? ?? ???c l?m s?ch."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# ===== ClassTimer.py =====

import ctypes
import time

class HighPrecisionTimer:
    """
    Enforces Windows Timer Resolution to 1ms (High Precision).
    This ensures time.sleep() and other timing functions are accurate to ~1-2ms 
    instead of the default ~15.6ms on Windows.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HighPrecisionTimer, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if not self.initialized:
            self.winmm = ctypes.windll.winmm
            self.started = False
            self.initialized = True

    def start(self):
        """Enable High Precision Timer (1ms)"""
        if not self.started:
            try:
                # timeBeginPeriod(1) sets the minimum timer resolution to 1ms
                self.winmm.timeBeginPeriod(1)
                self.started = True
                pass
            except Exception as e:
                pass

    def stop(self):
        """Disable High Precision Timer (Revert to System Default)"""
        if self.started:
            try:
                self.winmm.timeEndPeriod(1)
                self.started = False
                pass
            except Exception as e:
                pass


# ===== ClassSettings.py =====
class SettingsManager:
    """Manages application settings with persistent storage"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.settings_file = Path(__file__).parent / "Config" / "settings.json"
            self._cache = None
            self.initialized = True

    def _get_defaults(self):
        return {
            "keybinds": {
                "gui_toggle": "f1"
            },
            "ads_mode": "HOLD",
            "stop_keys": ["x", "g", "5"],
            "fast_loot": True,
            "fast_loot_key": "caps_lock",
            "overlay_key": "delete",
            "slide_trick": True,
            "crosshair": {
                "active": True,
                "style": "1: Gap Cross",
                "color": "Red",
                "ads_mode": "HOLD"
            },
            "capture_mode": "DXGI"
        }

    def load(self):
        if self._cache is not None:
            return self._cache

        if not self.settings_file.exists():
            defaults = self._get_defaults()
            self.save(defaults)
            self._cache = defaults
            return self._cache

        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                self._cache = json.load(f)
            defaults = self._get_defaults()
            self._merge_defaults(self._cache, defaults)
        except Exception as e:
            print(f"[WARN] Failed to load settings: {e}, using defaults")
            self._cache = self._get_defaults()

        return self._cache

    def _merge_defaults(self, current, defaults):
        for key, value in defaults.items():
            if key not in current:
                current[key] = value
            elif isinstance(value, dict) and isinstance(current[key], dict):
                self._merge_defaults(current[key], value)

    def save(self, settings=None):
        if settings is None:
            settings = self._cache
        if settings is None:
            return
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            self._cache = settings

    def get(self, key, default=None):
        settings = self.load()
        keys = key.split('.')
        value = settings
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key, value):
        settings = self.load()
        keys = key.split('.')
        current = settings
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
        self.save(settings)

    def reset_to_defaults(self):
        defaults = self._get_defaults()
        self.save(defaults)
        return defaults

# ===== ClassPubgConfig.py =====

import os
import re

class PubgConfig:
    def __init__(self):
        self.config_path = os.path.join(os.environ['LOCALAPPDATA'], 
                                        r"TslGame\Saved\Config\WindowsNoEditor\GameUserSettings.ini")
        self.last_mtime = 0.0
        self.last_size = 0
        self.sensitivities = {}
        self.true_sensitivities = {}  # LastConvertedSensitivity per scope
        self.vertical_multiplier = 1.0

    def parse_config(self):
        if not os.path.exists(self.config_path):
            return False

        try:
            st = os.stat(self.config_path)
            curr_mtime = st.st_mtime
            curr_size = st.st_size
            
            if curr_mtime == self.last_mtime and curr_size == self.last_size:
                return False

            try:
                with open(self.config_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except PermissionError:
                return False
            
            self.last_mtime = curr_mtime
            self.last_size = curr_size

            old_v = self.vertical_multiplier
            old_sens = self.sensitivities.copy()
            old_mode = getattr(self, 'ads_mode', 'HOLD')

            v_matches = list(re.finditer(r'MouseVerticalSensitivityMultiplierAdjusted=([\d\.]+)', content))
            if v_matches:
                self.vertical_multiplier = float(v_matches[-1].group(1))

            new_sens = {}
            true_sens_map = {}
            mouse_matches = list(re.finditer(r'SensitiveMap=\(Array=\((.*?)\)\)', content, re.DOTALL))
            
            match_source = content
            if mouse_matches:
                match_source = mouse_matches[-1].group(1)

            parsed_any = False
            for match in re.finditer(r'SensitiveName="([^"]+)",Sensitivity=([\d\.]+),LastConvertedSensitivity=([\d\.]+)', match_source):
                name = match.group(1)
                new_sens[name] = float(match.group(2))
                true_sens_map[name] = float(match.group(3))
                parsed_any = True

            if not parsed_any:
                for match in re.finditer(r'SensitiveName="([^"]+)",Sensitivity=([\d\.]+),LastConvertedSensitivity=([\d\.]+)', content):
                    name = match.group(1)
                    new_sens[name] = float(match.group(2))
                    true_sens_map[name] = float(match.group(3))

            self.sensitivities = new_sens
            self.true_sensitivities = true_sens_map
            
            per_scope_matches = re.findall(r'bIsUsingPerScopeMouseSensitivity=(True|False)', content)
            self.per_scope_enabled = False
            if per_scope_matches and per_scope_matches[-1] == "False":
                self.per_scope_enabled = True
                master_sens = new_sens.get("ScopingMagnified", 50.0)
                master_true = true_sens_map.get("ScopingMagnified", 0.02)
                for s_key in ["Scope2X", "Scope3X", "Scope4X", "Scope6X", "Scope8X", "Scope15X"]:
                    self.sensitivities[s_key] = master_sens
                    self.true_sensitivities[s_key] = master_true

            ads_match = re.search(r'InputModeADS=(\w+)', content)
            self.ads_mode = ads_match.group(1) if ads_match else "Hold"
            if (old_v == self.vertical_multiplier and old_sens == self.sensitivities and old_mode == self.ads_mode): return False
            return True
        except Exception as e: return False

    def debug_print(self):
        print("[HOT-RELOAD] Đã tải settings game thành công!")
        print(f" => Vertical: {self.vertical_multiplier}")
        print(f" => ADS Mode: {getattr(self, 'ads_mode', 'Hold')}")
        order = ["Normal", "Targeting", "Scoping", "ScopingMagnified", "Scope2X", "Scope3X", "Scope4X", "Scope6X", "Scope8X", "Scope15X"]
        for name in order:
            if name in self.sensitivities:
                print(f" => {name}: {round(self.sensitivities[name], 1)}")

# ===== Detect/ClassToaDo.py =====

# Đã làm sạch chú thích lỗi mã hóa.

RAW_LAYOUTS = {
    '1728x1080': {
        'gun1_name': [1269, 76, 167, 53],
        'gun1_scope': [1506, 101, 54, 62],
        'gun1_muzzle': [1236, 220, 53, 66],
        'gun1_grip': [1337, 220, 54, 66],
        'gun2_name': [1268, 302, 169, 54],
        'gun2_scope': [1507, 325, 55, 63],
        'gun2_muzzle': [1235, 447, 53, 66],
        'gun2_grip': [1338, 447, 52, 63],
        'stance': [602, 954, 54, 79],
    },
    '1920x1080': {
        'gun1_name': [1365, 77, 167, 52],
        'gun1_scope': [1602, 98, 54, 66],
        'gun1_muzzle': [1330, 220, 55, 67],
        'gun1_grip': [1434, 220, 53, 65],
        'gun2_name': [1364, 302, 170, 53],
        'gun2_scope': [1602, 323, 56, 66],
        'gun2_muzzle': [1331, 448, 54, 65],
        'gun2_grip': [1432, 448, 54, 64],
        'stance': [699, 958, 52, 74],
    },
}

DATA = RAW_LAYOUTS

# Helper Functions
def get_roi(resolution_key):
    return DATA.get(resolution_key, None)


# ===== Detect/ClassCapture.py =====

class CaptureLayoutContext:
    def __init__(self, capture_mode="DXGI"):
        self.capture_mode = str(capture_mode).upper()
        self.native = None
        self.native_capture_available = False
        if self.capture_mode in {"DXGI", "NATIVE"}:
            self.capture_mode = "DXGI"
            self._init_native_capture()

        # 0. Init DXCam if needed
        self.camera = None
        if self.capture_mode == "DXCAM":
            try:
                self.camera = dxcam.create(output_color="BGR")
            except Exception:
                self.capture_mode = "MSS"
        elif self.capture_mode not in {"MSS", "DXGI"}:
            self.capture_mode = "MSS"

        self._sct = None
        self.bbox = {}
        self.local_rois = {}
        self.region = None
        self.full_monitor = None
        user32 = ctypes.windll.user32
        self.width = user32.GetSystemMetrics(0)
        self.height = user32.GetSystemMetrics(1)
        self.resolution = (self.width, self.height)
        self.res_key = f"{self.width}x{self.height}"

        saved_rois = get_roi(self.res_key)
        if not saved_rois:
            saved_rois = get_roi("1920x1080")

        if saved_rois:
            self.rois = self.convert_list_to_dict(saved_rois)
        else:
            self.rois = {}

        self.calculate_bounding_box()

    def _init_native_capture(self):
        try:
            dll_path = get_resource_path(os.path.join("native", "EngineCore.dll"))
            if not os.path.exists(dll_path):
                self.capture_mode = "MSS"
                return
            self.native = ctypes.CDLL(dll_path)
            self.native.EngineCore_CaptureRegionBgr.argtypes = [
                ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                ctypes.POINTER(EngineCoreImageView),
            ]
            self.native.EngineCore_CaptureRegionBgr.restype = ctypes.c_int
            self.native.EngineCore_CaptureScreenBgr.argtypes = [ctypes.POINTER(EngineCoreImageView)]
            self.native.EngineCore_CaptureScreenBgr.restype = ctypes.c_int
            self.native.EngineCore_ReleaseCaptureBuffer.argtypes = []
            self.native.EngineCore_ReleaseCaptureBuffer.restype = None
            self.native_capture_available = True
        except Exception:
            self.native = None
            self.native_capture_available = False
            self.capture_mode = "MSS"

    def set_capture_mode(self, mode):
        mode_upper = str(mode or "DXGI").strip().upper()
        if mode_upper in {"NATIVE", "DXGI"}:
            mode_upper = "DXGI"
        elif mode_upper in {"DIRECTX"}:
            mode_upper = "DXCAM"
        elif mode_upper in {"GDI", "GDI+", "PIL"}:
            mode_upper = "MSS"
        elif mode_upper not in {"DXCAM", "MSS"}:
            mode_upper = "DXGI"

        if self.capture_mode == mode_upper:
            return

        self.capture_mode = mode_upper

        if mode_upper == "DXGI":
            self.camera = None
            self._init_native_capture()
        elif mode_upper == "DXCAM":
            self.native = None
            self.native_capture_available = False
            self.camera = None
            try:
                self.camera = dxcam.create(output_color="BGR")
            except Exception:
                self.capture_mode = "MSS"
                self.camera = None
        else:
            self.native = None
            self.native_capture_available = False
            self.camera = None

    def _native_view_to_ndarray(self, view):
        if not view or not bool(view.data) or view.width <= 0 or view.height <= 0 or view.channels != 3:
            return None
        total_size = int(view.stride) * int(view.height)
        base_ptr = ctypes.cast(view.data, ctypes.POINTER(ctypes.c_uint8))
        raw = np.ctypeslib.as_array(base_ptr, shape=(total_size,))
        frame = raw.reshape((int(view.height), int(view.stride)))
        return frame[:, : int(view.width) * 3].reshape((int(view.height), int(view.width), 3)).copy()

    def get_sct(self):
        if self._sct is None:
            if mss is None:
                raise RuntimeError("mss is not available")
            self._sct = mss.mss()
        return self._sct

    def convert_list_to_dict(self, saved_rois):
        rois = {}
        for key, val in saved_rois.items():
            rois[key] = {"left": val[0], "top": val[1], "width": val[2], "height": val[3]}
        return rois

    def calculate_bounding_box(self):
        if not self.rois:
            return None

        l = min(r["left"] for r in self.rois.values())
        t = min(r["top"] for r in self.rois.values())
        r_max = max(r["left"] + r["width"] for r in self.rois.values())
        b_max = max(r["top"] + r["height"] for r in self.rois.values())

        self.bbox = {
            "left": l - 10,
            "top": t - 10,
            "width": (r_max - l) + 20,
            "height": (b_max - t) + 20
        }
        self.region = (
            self.bbox["left"],
            self.bbox["top"],
            self.bbox["left"] + self.bbox["width"],
            self.bbox["top"] + self.bbox["height"],
        )
        self.full_monitor = {"top": 0, "left": 0, "width": self.width, "height": self.height}
        self.local_rois = {
            key: (
                roi["left"] - self.bbox["left"],
                roi["top"] - self.bbox["top"],
                roi["width"],
                roi["height"],
            )
            for key, roi in self.rois.items()
        }

    def grab_regional_image(self):
        if not hasattr(self, 'bbox') or not self.bbox:
            self.calculate_bounding_box()

        if self.capture_mode == "DXGI" and self.native_capture_available and self.native:
            view = EngineCoreImageView()
            ok = self.native.EngineCore_CaptureRegionBgr(
                int(self.bbox["left"]),
                int(self.bbox["top"]),
                int(self.bbox["width"]),
                int(self.bbox["height"]),
                ctypes.byref(view),
            )
            if ok:
                arr = self._native_view_to_ndarray(view)
                self.native.EngineCore_ReleaseCaptureBuffer()
                if arr is not None:
                    return arr

        if self.capture_mode == "DXCAM" and self.camera:
            frame = self.camera.grab(region=self.region)
            if frame is not None:
                return frame

        sct_img = self.get_sct().grab(self.bbox)
        return np.asarray(sct_img)[:, :, :3]

    def get_roi_from_image(self, regional_img, roi_name):
        roi = self.local_rois.get(roi_name)
        if not roi or regional_img is None:
            return None

        lx, ly, w, h = roi
        return regional_img[ly:ly+h, lx:lx+w]

    def grab_screen(self):
        if self.capture_mode == "DXGI" and self.native_capture_available and self.native:
            view = EngineCoreImageView()
            ok = self.native.EngineCore_CaptureScreenBgr(ctypes.byref(view))
            if ok:
                arr = self._native_view_to_ndarray(view)
                self.native.EngineCore_ReleaseCaptureBuffer()
                if arr is not None:
                    return arr

        if self.capture_mode == "DXCAM" and self.camera:
            frame = self.camera.grab()
            if frame is not None:
                return frame

        sct_img = self.get_sct().grab(self.full_monitor)
        return np.asarray(sct_img)[:, :, :3]

    def debug_rois(self):
        img = self.grab_screen()
        if not hasattr(self, 'bbox'):
            self.calculate_bounding_box()

        bx, by, bw, bh = self.bbox["left"], self.bbox["top"], self.bbox["width"], self.bbox["height"]
        cv2.rectangle(img, (bx, by), (bx+bw, by+bh), (0, 0, 255), 3)
        cv2.putText(img, "REGION", (bx, by-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        for name, roi in self.rois.items():
            x, y, w, h = roi["left"], roi["top"], roi["width"], roi["height"]
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(img, name, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        filename = "debug_roi_preview.jpg"
        cv2.imwrite(filename, img)
        return filename


# ===== Detect/ClassDetection.py =====

import cv2
import os
import numpy as np

class PythonDetectionEngine:
    def __init__(self, template_folder="templates"):
        """
        Khởi tạo hệ thống và nạp sẵn toàn bộ mẫu ảnh vào RAM.
        """
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_dir = os.path.join(self.base_dir, template_folder)

        width = win32api.GetSystemMetrics(0)
        height = win32api.GetSystemMetrics(1)
        self.res_key = f"{width}x{height}"
        if os.path.isdir(os.path.join(self.template_dir, self.res_key)):
            self.template_dir = os.path.join(self.template_dir, self.res_key)
        elif os.path.isdir(os.path.join(self.template_dir, "1920x1080")):
            self.template_dir = os.path.join(self.template_dir, "1920x1080")

        self.templates = {
            "weapons": {},
            "ui": {},
            "accessories": {},
            "grip": {},
            "scopes": {},
            "stances": {},
            "dieukien": {},
        }
        self.template_items = {key: [] for key in self.templates.keys()}

        total_count = 0
        for category in self.templates.keys():
            total_count += self._load_category(category)
        for category, mapping in self.templates.items():
            items = []
            for name, tpl in mapping.items():
                tpl_h, tpl_w = tpl.shape[:2]
                features = self._compute_template_features(tpl)
                items.append((name, tpl, tpl_h, tpl_w, features))
            self.template_items[category] = tuple(items)
        self._last_match_by_category = {}
        self._roi_match_cache = {}
        self._weapon_prefilter_mean_delta = 26.0
        self._weapon_prefilter_std_delta = 22.0
        self._weapon_prefilter_probe_delta = 34.0
        self._perfect_match_thresholds = {
            "weapons": 0.995,
            "scopes": 0.985,
            "grip": 0.985,
            "accessories": 0.985,
            "stances": 0.980,
            "dieukien": 0.970,
        }
        self._strong_match_thresholds = {
            "weapons": 0.980,
            "scopes": 0.965,
            "grip": 0.965,
            "accessories": 0.965,
            "stances": 0.950,
            "dieukien": 0.930,
        }
        print(f" > [SYSTEM] Detection Engine: Loaded {total_count} templates (BGR Mode)")

    def _load_category(self, category):
        path = os.path.join(self.template_dir, category)
        if category == "stances":
            path = os.path.join(self.template_dir, "stance")
        if not os.path.exists(path):
            return 0

        count = 0
        for file in os.listdir(path):
            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                full_path = os.path.join(path, file)
                img = self._read_image_unicode(full_path)
                if img is not None:
                    name = os.path.splitext(file)[0].upper()
                    self.templates[category][name] = img
                    count += 1
        return count

    def _read_image_unicode(self, full_path):
        try:
            data = np.fromfile(full_path, dtype=np.uint8)
            if data.size == 0:
                return None
            return cv2.imdecode(data, cv2.IMREAD_COLOR)
        except Exception:
            return None

    def _compute_template_features(self, image):
        if image is None or getattr(image, "size", 0) == 0:
            return None
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        probe = cv2.resize(gray, (8, 8), interpolation=cv2.INTER_AREA)
        return {
            "gray_mean": float(gray.mean()),
            "gray_std": float(gray.std()),
            "probe": probe.astype(np.float32, copy=False),
        }

    def _compute_roi_features(self, roi):
        if roi is None or getattr(roi, "size", 0) == 0:
            return None
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        probe = cv2.resize(gray, (8, 8), interpolation=cv2.INTER_AREA)
        return {
            "gray_mean": float(gray.mean()),
            "gray_std": float(gray.std()),
            "probe": probe.astype(np.float32, copy=False),
        }

    def _weapon_prefilter_pass(self, roi_features, tpl_features):
        if not roi_features or not tpl_features:
            return True
        if abs(roi_features["gray_mean"] - tpl_features["gray_mean"]) > self._weapon_prefilter_mean_delta:
            return False
        if abs(roi_features["gray_std"] - tpl_features["gray_std"]) > self._weapon_prefilter_std_delta:
            return False
        probe_delta = cv2.absdiff(roi_features["probe"], tpl_features["probe"])
        return float(probe_delta.mean()) <= self._weapon_prefilter_probe_delta

    def _make_roi_cache_key(self, roi, category, threshold):
        if roi is None or getattr(roi, "size", 0) == 0:
            return None
        try:
            roi_bytes = roi.tobytes()
        except Exception:
            return None
        roi_hash = zlib.adler32(roi_bytes) & 0xFFFFFFFF
        return (category, roi.shape[0], roi.shape[1], int(round(float(threshold) * 1000.0)), roi_hash)

    def _match(self, roi, category, threshold=0.8):
        templates = self.template_items.get(category)
        if not templates:
            return "NONE"
        cache_key = self._make_roi_cache_key(roi, category, threshold)
        if cache_key is not None:
            cached_value = self._roi_match_cache.get(cache_key)
            if cached_value is not None:
                if cached_value != "NONE":
                    self._last_match_by_category[category] = cached_value
                return cached_value

        max_val = -1.0
        best_name = "NONE"
        roi_h, roi_w = roi.shape[:2]
        recent_name = self._last_match_by_category.get(category)
        perfect_match_threshold = float(self._perfect_match_thresholds.get(category, 0.995))
        strong_match_threshold = float(self._strong_match_thresholds.get(category, 0.980))
        roi_features = self._compute_roi_features(roi) if category == "weapons" else None

        if recent_name:
            for name, tpl, tpl_h, tpl_w, tpl_features in templates:
                if name != recent_name:
                    continue
                if tpl_h <= roi_h and tpl_w <= roi_w:
                    if category == "weapons" and not self._weapon_prefilter_pass(roi_features, tpl_features):
                        break
                    res = cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED)
                    _, val, _, _ = cv2.minMaxLoc(res)
                    if val > max_val:
                        max_val = val
                        best_name = name
                    if val >= perfect_match_threshold:
                        self._last_match_by_category[category] = name
                        if cache_key is not None:
                            self._roi_match_cache[cache_key] = name
                        return name
                break

        for name, tpl, tpl_h, tpl_w, tpl_features in templates:
            if name == recent_name or tpl_h > roi_h or tpl_w > roi_w:
                continue
            if category == "weapons" and not self._weapon_prefilter_pass(roi_features, tpl_features):
                continue

            res = cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED)
            _, val, _, _ = cv2.minMaxLoc(res)

            if val > max_val:
                max_val = val
                best_name = name

            if val >= strong_match_threshold:
                break

        if max_val >= threshold:
            self._last_match_by_category[category] = best_name
            if cache_key is not None:
                self._roi_match_cache[cache_key] = best_name
            return best_name
        if cache_key is not None:
            self._roi_match_cache[cache_key] = "NONE"
        return "NONE"

    def detect_weapon_name(self, roi, threshold=0.8):
        return self._match(roi, "weapons", threshold)

    def detect_ui_anchor(self, roi, threshold=0.65):
        return self._match(roi, "dieukien", threshold)

    def detect_accessory(self, roi, threshold=0.8):
        res = self._match(roi, "accessories", threshold)
        if res == "NONE":
            return "NONE"
        name = res.upper()
        if "GIAMGIAT" in name:
            return "GiamGiat"
        if "ANTIALUA" in name:
            return "AnTiaLua"
        if "GIAMRUNG" in name:
            return "GiamRung"
        if "ATLSMG" in name:
            return "ATLsmg"
        if "GGIATSMG" in name:
            return "GGiatSMG"
        if "GTHANHSMG" in name:
            return "GThanhSMG"
        return res

    def detect_grip(self, roi, threshold=0.8):
        res = self._match(roi, "grip", threshold)
        if res == "NONE":
            return "NONE"
        name = res.upper()
        if "TCDUNG" in name:
            return "tcDung"
        if "TCHONG" in name:
            return "tcHong"
        if "TCLASER" in name:
            return "tcLaser"
        if "TCNAMCHAT" in name:
            return "tcNamChat"
        if "TCNGHIENG" in name:
            return "tcNghieng"
        if "TCNHE" in name:
            return "tcNhe"
        return res

    def detect_scope(self, roi, threshold=0.8):
        res = self._match(roi, "scopes", threshold)
        if res == "NONE":
            return "NONE"
        name = res.upper()
        if "SCOPEKH" in name:
            return "ScopeKH"
        match = re.search(r'SCOPE(\d+)', name)
        if match:
            return "Scope" + match.group(1)
        return res

    def detect_stance(self, roi, threshold=0.6):
        res = self._match(roi, "stances", threshold)
        if res == "NONE":
            return "Stand"

        name = res.upper()
        if "DUNG" in name:
            return "Stand"
        if "NGOI" in name:
            return "Crouch"
        if "NAM" in name:
            return "Prone"
        if "STANDING" in name:
            return "Stand"
        if "CROUCHING" in name:
            return "Crouch"
        if "PRONE" in name:
            return "Prone"
        return "Stand"

# ===== Recoil/ClassConfig.py =====

import importlib
import re
from pathlib import Path

# Pre-load data once

class RecoilConfig:
    def __init__(self):
        self.data = BaseRecoilDataModule.BaseRecoilData
        self.cache = {}

    def reload_data(self):
        try:
            importlib.reload(BaseRecoilDataModule)
            self.data = BaseRecoilDataModule.BaseRecoilData
            self.cache.clear()
            return True
        except Exception:
            return False

    def sync_native(self):
        return True


    def get_attr(self, obj, attr, default=None):
        if isinstance(obj, dict): return obj.get(attr, default)
        return getattr(obj, attr, default)

    def get_master_multiplier(self, gun_data):
        """
        Calculates Final Fixed Multiplier (Base * Scope * Grip * Muzzle)
        """
        try:
            w_name_raw = str(gun_data.get("name", "NONE")).strip()
            weapons_dict = getattr(self.data, "Weapons", {})
            w_name = w_name_raw if w_name_raw in weapons_dict else w_name_raw.upper()

            if w_name not in weapons_dict:
                return 1.0
            w_data = weapons_dict[w_name]

            sc_val_raw = str(gun_data.get("scope", "NONE"))
            sc_val_upper = sc_val_raw.upper()

            scope_map = {
                "REDDOT": "Scope1", "HOLOSIGHT": "Scope1", "NONE": "Scope1",
                "2X": "Scope2", "3X": "Scope3", "4X": "Scope4", "6X": "Scope6", "8X": "Scope8"
            }

            if "KH" in sc_val_upper:
                match = re.search(r"\d+", sc_val_upper)
                digit = match.group() if match else "1"
                sc_key = f"ScopeKH{digit}"
            else:
                sc_key = scope_map.get(sc_val_upper)
                if not sc_key:
                    val = sc_val_raw.split('_')[0]
                    sc_key = val.capitalize() if val.lower().startswith('scope') else val

            scope_mult = getattr(self.data, "scope_multipliers", {}).get(sc_key, 1.0)

            g_key_raw = gun_data.get("grip", "NONE")
            grips_map = getattr(self.data, "grips", {})
            grip_match = next((v for k, v in grips_map.items() if k.lower() == g_key_raw.lower()), None)
            grip_mult = float(grip_match if grip_match is not None else grips_map.get("NONE", 1.25))

            m_key_raw = gun_data.get("accessories", "NONE")
            acc_map = getattr(self.data, "accessories", {})
            acc_match = next((v for k, v in acc_map.items() if k.lower() == m_key_raw.lower()), None)
            muzzle_mult = float(acc_match if acc_match is not None else acc_map.get("NONE", 1.25))

            total = scope_mult * grip_mult * muzzle_mult

            strength_map = {
                "Scope1": "Strength_Normal", "ScopeKH1": "Strength_Normal",
                "Scope2": "Strength_2x", "Scope3": "Strength_3x",
                "Scope4": "Strength_4x", "ScopeKH4": "Strength_4x",
                "Scope6": "Strength_6x", "Scope8": "Strength_8x"
            }
            str_attr = strength_map.get(sc_key)
            if str_attr:
                strength_percent = getattr(self.data, str_attr, 100)
                total = total * (float(strength_percent) / 100.0)

            return total

        except Exception:
            return 1.0

    def get_all_stance_multipliers(self, w_name):
        """Lấy bộ hệ số tư thế của súng từ ClassBaseRecoil"""
        try:
            weapons_dict = getattr(self.data, "Weapons", {})
            w_key = w_name if w_name in weapons_dict else w_name.upper()
            if w_key not in weapons_dict:
                return {"Stand": 1.25, "Crouch": 1.0, "Prone": 0.7}

            w_data = weapons_dict[w_key]
            st_data = self.get_attr(w_data, "stance_multipliers", {})

            return {
                "Stand": self.get_attr(st_data, "Stand", 1.0),
                "Crouch": self.get_attr(st_data, "Crouch", 1.0),
                "Prone": self.get_attr(st_data, "Prone", 1.0)
            }

        except:
            return {"Stand": 1.25, "Crouch": 1.0, "Prone": 0.7}

    def get_base_table(self, w_name):
        try:
            weapons_dict = getattr(self.data, "Weapons", {})
            w_key = w_name if w_name in weapons_dict else w_name.upper()
            if w_key not in weapons_dict:
                return []
            return self.get_attr(weapons_dict[w_key], "BaseTable", [])
        except:
            return []

    def get_raw_pattern(self, base_table):

        raw_pattern = []
        for entry in base_table:
            if len(entry) == 2:
                val, count = entry
                for _ in range(int(count)): raw_pattern.append(val)
            elif len(entry) == 1: raw_pattern.append(entry[0])
        return raw_pattern


class SensitivityCalculator:
    def __init__(self):
        self.base_vert_sens = 1.0
        self.base_sens = 30.0

    def calculate_sens_multiplier(self, pubg_config, gun_info, hybrid_mode="Scope1"):
        curr_vert = getattr(pubg_config, "vertical_multiplier", 1.0)
        if curr_vert <= 0:
            curr_vert = self.base_vert_sens
        vert_factor = self.base_vert_sens / curr_vert

        scope_name = str(gun_info.get("scope", "NONE")).upper()
        sens_key = "Scoping"
        if "NONE" in scope_name:
            sens_key = "Targeting"
        elif "2" in scope_name:
            sens_key = "Scope2X"
        elif "3" in scope_name:
            sens_key = "Scope3X"
        elif "4" in scope_name:
            sens_key = "Scope4X"
        elif "6" in scope_name:
            sens_key = "Scope3X"
        elif "8" in scope_name:
            sens_key = "Scope3X"
        elif "15" in scope_name:
            sens_key = "Scope3X"

        if "SCOPEKH" in scope_name:
            sens_key = "Scope4X" if hybrid_mode == "Scope4" else "Scoping"

        in_game_sens = getattr(pubg_config, "sensitivities", {}).get(sens_key, self.base_sens)
        if in_game_sens <= 0:
            in_game_sens = self.base_sens
        scope_factor = math.pow(10, (self.base_sens - in_game_sens) / 50.0)
        return scope_factor * vert_factor


# ===== Recoil/ClassGhimTam.py =====

import win32api
import win32con
import time
from threading import Thread

class RecoilExecutor:
    def __init__(self):
        super().__init__()
        self.config = RecoilConfig()
        self.running = False
        self.thread = None
        self.pattern = []
        self.current_index = 0
        self.full_pattern_done = False
        self.gun_base_mult = 1.0
        self.st_stand = 1.0
        self.st_crouch = 1.0
        self.st_prone = 1.0
        self.live_stance = "Stand"
        self.current_gun_name = "NONE"
        self._remainder_y = 0.0

    def start_recoil(self, base_pattern, initial_stance="Stand"):
        self.stop_recoil()
        self.live_stance = initial_stance
        self._remainder_y = 0.0
        self.pattern = list(base_pattern or [])
        self.current_index = 0
        self.full_pattern_done = False
        self.running = True
        self.thread = Thread(target=self._recoil_loop, daemon=True)
        self.thread.start()

    def stop_recoil(self):
        self.running = False

    def reload_config(self):
        if self.config:
            self.config.reload_data()
        self.thread = None

    def _recoil_loop(self):
        sampling_rate = 0.008
        if hasattr(self.config.data, "sampling_rate_ms"):
            sampling_rate = self.config.data.sampling_rate_ms / 1000.0

        next_time = time.perf_counter()
        while self.running:
            if not is_game_active():
                self.running = False
                break

            next_time += sampling_rate
            if self.current_index < len(self.pattern):
                st_mult = self.st_stand
                if self.live_stance == "Crouch":
                    st_mult = self.st_crouch
                elif self.live_stance == "Prone":
                    st_mult = self.st_prone

                final_mult = self.gun_base_mult * st_mult
                pixels = self.pattern[self.current_index] * final_mult
                self.current_index += 1
                if self.current_index >= len(self.pattern):
                    self.full_pattern_done = True

                total_y = pixels + self._remainder_y
                move_y = int(total_y)
                self._remainder_y = total_y - move_y

                if move_y != 0:
                    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, 0, move_y, 0, 0)

            curr_t = time.perf_counter()
            if next_time > curr_t:
                time.sleep(next_time - curr_t)
            else:
                next_time = curr_t


PHYSICAL_KEYS = set()
INJECT_LOCK = threading.Lock()
INJECTED_EVENTS = {}


def add_injected_event(key, is_press):
    with INJECT_LOCK:
        if key in ("shift_l", "shift_r"):
            key = "shift"
        token = f"{str(key).lower()}_{'press' if is_press else 'release'}"
        INJECTED_EVENTS.setdefault(token, []).append(time.time())


def consume_injected_event(key, is_press):
    with INJECT_LOCK:
        if key in ("shift_l", "shift_r"):
            key = "shift"
        token = f"{str(key).lower()}_{'press' if is_press else 'release'}"
        now = time.time()
        if token in INJECTED_EVENTS:
            INJECTED_EVENTS[token] = [t for t in INJECTED_EVENTS[token] if now - t < 1.0]
            if INJECTED_EVENTS[token]:
                INJECTED_EVENTS[token].pop(0)
                return True
        return False


class KeyboardListener(QObject):
    signal_key_event = pyqtSignal(str, bool)
    signal_action = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.listener = None
        self.running = False
        self.key_map = {
            "1": "SLOT_1", "!": "SLOT_1",
            "2": "SLOT_2", "@": "SLOT_2",
            "3": "MACRO_PAUSE", "#": "MACRO_PAUSE",
            "4": "MACRO_PAUSE", "$": "MACRO_PAUSE",
            "5": "MACRO_PAUSE", "%": "MACRO_PAUSE",
            "6": "MACRO_PAUSE", "^": "MACRO_PAUSE",
            "7": "MACRO_PAUSE", "&": "MACRO_PAUSE",
            "g": "MACRO_PAUSE",
            "x": "MACRO_PAUSE",
            "c": "STANCE_CROUCH",
            "z": "STANCE_PRONE",
            "space": "STANCE_JUMP",
        }
        self.raw_keys = {'r'}
        self.pressed_keys = set()
        self.current_guitoggle_key = 'f1'
        self.raw_keys.add(self.current_guitoggle_key)
        self.native_passthrough_keys = {
            "caps_lock", "shift", "shift_l", "shift_r",
            "ctrl", "ctrl_l", "ctrl_r",
            "alt", "alt_l", "alt_r",
            "w", "a", "s", "d", "c",
        }

    def _is_native_passthrough_release_noise(self, key_name: str) -> bool:
        if key_name not in self.native_passthrough_keys:
            return False
        vk = int(gui_key_to_vk(key_name))
        if vk <= 0:
            return False
        try:
            return (win32api.GetAsyncKeyState(vk) & 0x8000) != 0
        except Exception:
            return False

    def update_guitoggle_key(self, new_key):
        new_key = new_key.lower()
        if self.current_guitoggle_key in self.raw_keys:
            self.raw_keys.discard(self.current_guitoggle_key)
        self.raw_keys.add(new_key)
        self.current_guitoggle_key = new_key

    def start_listening(self):
        if not self.listener:
            self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
            self.listener.start()
            self.running = True

    def stop_listening(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
            self.running = False

    def on_press(self, key):
        try:
            k_str = self.get_key_name(key)
            if not k_str: return
            if consume_injected_event(k_str, True):
                return
            PHYSICAL_KEYS.add(k_str)
            is_raw = k_str in self.raw_keys
            is_native_passthrough = k_str in self.native_passthrough_keys
            action = self.key_map.get(k_str)
            if not is_raw and not action and not is_native_passthrough:
                return
            if k_str in self.pressed_keys:
                return
            self.pressed_keys.add(k_str)
            if is_raw or is_native_passthrough:
                self.signal_key_event.emit(k_str, True)
            if action:
                self.signal_action.emit(action)
        except Exception as e:
            print(f"[KeyError] {e}")

    def on_release(self, key):
        try:
            k_str = self.get_key_name(key)
            if not k_str: return
            if consume_injected_event(k_str, False):
                return
            if self._is_native_passthrough_release_noise(k_str):
                return
            if k_str in PHYSICAL_KEYS:
                PHYSICAL_KEYS.discard(k_str)
            if k_str in self.pressed_keys:
                self.pressed_keys.remove(k_str)
            if k_str in self.raw_keys or k_str in self.native_passthrough_keys:
                self.signal_key_event.emit(k_str, False)
        except Exception as e:
            print(f"[KEYBOARD] on_release error: {e}")

    def get_key_name(self, key):
        if hasattr(key, 'char') and key.char:
            return key.char.lower()
        elif hasattr(key, 'name'):
            return key.name
        else:
            return str(key).replace("Key.", "")


class MouseListener(QObject):
    signal_click = pyqtSignal(str, bool)

    def __init__(self):
        super().__init__()
        self.listener = None
        self.running = False

    def start_listening(self):
        if not self.listener:
            self.listener = mouse.Listener(on_click=self.on_click)
            self.listener.start()
            self.running = True

    def stop_listening(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
            self.running = False

    def on_click(self, x, y, button, pressed):
        try:
            btn_str = str(button).replace("Button.", "")
            self.signal_click.emit(btn_str, pressed)
        except Exception as e:
            print(f"[MOUSE] on_click error: {e}")

# ===== GUI/UI_Utils.py =====

from PyQt6.QtWidgets import (QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame)
from PyQt6.QtCore import Qt

def create_panel(title, color_hex, obj_name):
    """M? t? ?? ???c l?m s?ch."""
    panel = QFrame()
    panel.setObjectName(obj_name)
    panel.setProperty("class", "PanelFrame")
    p_layout = QVBoxLayout(panel)
    p_layout.setContentsMargins(8, 8, 8, 8)
    p_layout.setSpacing(4)
    
    # Title Label
    lbl = QLabel(title)
    lbl.setProperty("class", "PanelHeader")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    # Dynamic color based on weapon slot
    lbl.setStyleSheet(f"color: {color_hex};")
    p_layout.addWidget(lbl)
    
    return panel, p_layout

def add_setting_row(parent_layout, label_text, value_text):
    """M? t? ?? ???c l?m s?ch."""
    row_layout = QHBoxLayout()
    
    lbl = QLabel(label_text)
    lbl.setFixedWidth(100)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setProperty("class", "SettingLabel")
    
    btn = QPushButton(value_text)
    btn.setProperty("class", "SettingBtn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFixedHeight(25)
    
    row_layout.addWidget(lbl)
    row_layout.addWidget(btn)
    parent_layout.addLayout(row_layout)
    
    return btn

def create_data_row(grid, row, label):
    """M? t? ?? ???c l?m s?ch."""
    l = QLabel(f"{label}")
    l.setProperty("role", "row-label")
    
    val = QLabel("NONE")
    val.setProperty("role", "value-label")
    val.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    grid.addWidget(l, row, 0)
    grid.addWidget(val, row, 1)
    
    return val


# ===== GUI/TrayManager.py =====

from PyQt6.QtWidgets import (QSystemTrayIcon, QMenu, QApplication)
from PyQt6.QtGui import QIcon, QAction

class TrayManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.tray_icon = QSystemTrayIcon(self.main_window)
        
        # Load Icon
        icon_path = get_resource_path("di88vp.ico")
        self.tray_icon.setIcon(QIcon(icon_path))
        self.tray_icon.setToolTip("Macro By Di88")
        
        # Setup Menu
        self.setup_menu()
        
        # Connect Actions
        self.tray_icon.activated.connect(self.on_tray_activated)
        
    def setup_menu(self):
        menu = QMenu()
        
        # Restore Action
        action_show = QAction("Show", self.main_window)
        action_show.triggered.connect(self.main_window.restore_window)
        menu.addAction(action_show)
        
        # Exit Action
        action_exit = QAction("Exit", self.main_window)
        action_exit.triggered.connect(QApplication.instance().quit)
        menu.addAction(action_exit)
        
        self.tray_icon.setContextMenu(menu)
        
    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.main_window.restore_window()
            
    def show(self):
        self.tray_icon.show()
        
    def hide(self):
        self.tray_icon.hide()


class ResolutionNoticeDialog(QDialog):
    def __init__(self, resolution_text: str, parent=None):
        super().__init__(parent)
        self._drag_offset: QPoint | None = None
        self.setWindowTitle("Macro & Aim By Di88")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(432)

        icon_path = get_resource_path("di88vp.ico")
        self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet(
            """
            QDialog {
                background: transparent;
                border: none;
            }
            QFrame#Card {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #1c2128,
                    stop: 0.55 #171c23,
                    stop: 1 #14181e
                );
                border: 1px solid #43515e;
                border-radius: 14px;
            }
            QLabel#HeaderTitle {
                color: #f5f8fc;
                font-size: 13px;
                font-weight: 800;
                background: transparent;
            }
            QLabel#Title {
                color: #ffffff;
                font-size: 17px;
                font-weight: 900;
                background: transparent;
            }
            QLabel#Body {
                color: #dde8f4;
                font-size: 12px;
                font-weight: 700;
                background: transparent;
            }
            QLabel#Badge {
                background: qradialgradient(
                    cx: 0.42, cy: 0.35, radius: 1.0,
                    stop: 0 #1e6c96,
                    stop: 0.58 #124e73,
                    stop: 1 #0d3855
                );
                color: #eff9ff;
                border: 1px solid #6fcff4;
                border-radius: 26px;
                font-size: 27px;
                font-weight: 800;
                min-width: 52px;
                max-width: 52px;
                min-height: 52px;
                max-height: 52px;
            }
            QPushButton#CloseBtn {
                background: transparent;
                color: #f0f4f8;
                border: none;
                font-size: 17px;
                font-weight: 800;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
            }
            QPushButton#CloseBtn:hover {
                color: #ff8f8f;
            }
            QPushButton#PrimaryBtn {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2a323b,
                    stop: 1 #242b33
                );
                color: #ffffff;
                border: 1px solid #6f808d;
                border-radius: 8px;
                padding: 9px 18px;
                font-size: 12px;
                font-weight: 800;
                min-width: 128px;
            }
            QPushButton#PrimaryBtn:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #32404d,
                    stop: 1 #2a3641
                );
                border: 1px solid #8db3d1;
            }
            QPushButton#PrimaryBtn:pressed {
                background: #23303a;
                border: 1px solid #78a6c9;
            }
            QFrame#AccentLine {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #184f7e,
                    stop: 0.5 #2fb6ee,
                    stop: 1 #184f7e
                );
                border: none;
                border-radius: 1px;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("Card")
        root.addWidget(card)

        card_shadow = QGraphicsDropShadowEffect(card)
        card_shadow.setBlurRadius(32)
        card_shadow.setOffset(0, 10)
        card_shadow.setColor(QColor(0, 0, 0, 155))
        card.setGraphicsEffect(card_shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 18)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)

        header_icon = QLabel()
        header_icon.setPixmap(QIcon(icon_path).pixmap(16, 16))
        header_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(header_icon, 0, Qt.AlignmentFlag.AlignVCenter)

        header_title = QLabel("Macro & Aim By Di88")
        header_title.setObjectName("HeaderTitle")
        header_row.addWidget(header_title, 1, Qt.AlignmentFlag.AlignVCenter)

        close_button = QPushButton("\u00D7")
        close_button.setObjectName("CloseBtn")
        close_button.clicked.connect(self.reject)
        header_row.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addLayout(header_row)

        accent = QFrame()
        accent.setObjectName("AccentLine")
        accent.setFixedHeight(2)
        layout.addWidget(accent)

        badge = QLabel("i")
        badge.setObjectName("Badge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(2)
        layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignCenter)

        title = QLabel("\u0110\u1ed9\u0020\u0050\u0068\u00e2\u006e\u0020\u0047\u0069\u1ea3\u0069")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        body = QLabel(
            f"\u0110\u0061\u006e\u0067\u0020\u0073\u1eed\u0020\u0064\u1ee5\u006e\u0067\u0020\u0111\u1ed9\u0020\u0070\u0068\u00e2\u006e\u0020\u0067\u0069\u1ea3\u0069\u003a\u0020{resolution_text}"
        )
        body.setObjectName("Body")
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setWordWrap(True)
        body.setContentsMargins(12, 0, 12, 0)
        layout.addWidget(body)

        ok_button = QPushButton("OK")
        ok_button.setObjectName("PrimaryBtn")
        ok_button.clicked.connect(self.accept)
        layout.addSpacing(2)
        layout.addWidget(ok_button, 0, Qt.AlignmentFlag.AlignCenter)

        self.adjustSize()
        self.setFixedHeight(self.sizeHint().height())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)


class ModernDialog(QDialog):
    def __init__(self, parent, title, message, buttons=("Yes", "No"), is_question=True):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.result_value = None
        
        # Ensure focus and activation
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.activateWindow()
        self.raise_()
        
        # Main Container
        self.container = QFrame(self)
        self.container.setObjectName("DialogContainer")
        self.container.setStyleSheet("""
            QFrame#DialogContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2b2b2b, stop:1 #1a1a1a);
                border: 2px solid #444;
                border-radius: 12px;
            }
            QLabel#DialogTitle {
                color: #ff6b6b;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                background-color: rgba(0,0,0,0.2);
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QLabel#DialogMessage {
                color: #ddd;
                font-size: 13px;
                padding: 20px;
            }
            QPushButton {
                background-color: #333;
                color: white;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #444;
                border: 1px solid #ff6b6b;
            }
            QPushButton#PrimaryBtn {
                background-color: #ff6b6b;
                border: none;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #ff5252;
            }
        """)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(0)
        
        # Title
        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("DialogTitle")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_title)
        
        # Message
        self.lbl_msg = QLabel(message)
        self.lbl_msg.setObjectName("DialogMessage")
        self.lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_msg.setWordWrap(True)
        layout.addWidget(self.lbl_msg)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(15, 0, 15, 0)
        btn_layout.setSpacing(12)
        
        btn_layout.addStretch()
        for i, btn_text in enumerate(buttons):
            btn = QPushButton(btn_text)
            if i == 0 and is_question:
                btn.setObjectName("PrimaryBtn")
            
            # Using a more reliable way to connect buttons
            btn.clicked.connect(self.make_callback(btn_text))
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
            
        layout.addLayout(btn_layout)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.container.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.container)
        
        self.setFixedSize(420, 190)

    def make_callback(self, text):
        # Handle the 'checked' argument from clicked signal to avoid TypeError
        return lambda checked=False: self.on_click(text)

    def on_click(self, value):
        print(f"[DEBUG] ModernDialog: Button clicked -> {value}")
        self.result_value = value
        self.done(1)

class AppNoticeDialog:
    @staticmethod
    def question(parent, title, message, buttons=("Có", "Không")):
        dlg = ModernDialog(parent, title, message, buttons=buttons, is_question=True)
        dlg.exec()
        return dlg.result_value == buttons[0]

    @staticmethod
    def information(parent, title, message):
        dlg = ModernDialog(parent, title, message, buttons=("OK",), is_question=False)
        dlg.exec()

    @staticmethod
    def warning(parent, title, message):
        dlg = ModernDialog(parent, title, message, buttons=("Hiểu rồi",), is_question=False)
        dlg.exec()

    @staticmethod
    def custom_choice(parent, title, message, buttons=("Tắt", "Xuống Tray", "Hủy")):
        dlg = ModernDialog(parent, title, message, buttons=buttons, is_question=True)
        dlg.exec()
        return dlg.result_value

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class HomePanelBuilder:
    def __init__(self, owner):
        self.owner = owner

    def build(self):
        owner = self.owner

        owner.home_page = QWidget()
        owner.home_page.setObjectName("HomePage")

        layout = QVBoxLayout(owner.home_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        owner.home_content_panel = QFrame()
        owner.home_content_panel.setObjectName("HomeContentPanel")
        owner.home_content_panel.setStyleSheet(
            """
            QFrame#HomeContentPanel {
                background: #171717;
                border: 1px solid #343434;
                border-radius: 14px;
            }
            """
        )

        panel_layout = QVBoxLayout(owner.home_content_panel)
        panel_layout.setContentsMargins(14, 14, 14, 14)
        panel_layout.setSpacing(14)

        panel_layout.addWidget(self._build_metric_row())

        summaries_row = QHBoxLayout()
        summaries_row.setContentsMargins(0, 0, 0, 0)
        summaries_row.setSpacing(12)
        summaries_row.addWidget(
            self._build_summary_card(
                object_name="HomeMacroSummary",
                title="MACRO STATUS",
                title_color="#ff8f8f",
                rows=[
                    ("Tư thế", "home_macro_stance_value", "ĐỨNG", "#f2f2f2"),
                    ("ADS", "home_macro_ads_value", "HOLD", "#66ffc2"),
                    ("Chế Độ Chụp", "home_macro_capture_value", "DXGI", "#89d4ff"),
                ],
                toggle_attr="home_macro_toggle_btn",
                toggle_handler=getattr(owner, "toggle_home_macro", None),
            ),
            1,
        )
        summaries_row.addWidget(
            self._build_summary_card(
                object_name="HomeAimSummary",
                title="AIM STATUS",
                title_color="#73f0ff",
                rows=[
                    ("Model", "home_aim_model_value", "N/A", "#f2f2f2"),
                    ("Backend", "home_aim_backend_value", "Chưa nạp", "#f2f2f2"),
                    ("Chế Độ Chụp", "home_aim_capture_value", "DirectX", "#89d4ff"),
                ],
                toggle_attr="home_aim_toggle_btn",
                toggle_handler=getattr(owner, "toggle_home_aim", None),
            ),
            1,
        )
        panel_layout.addLayout(summaries_row)

        layout.addWidget(owner.home_content_panel)
        layout.addStretch(1)
        return owner.home_page

    def _build_metric_card(
        self,
        title: str,
        value_attr: str,
        text: str,
        color: str,
        unit_text: str,
        *,
        badge_text: str = "",
        badge_color: str = "#79ff9f",
        badge_attr: str | None = None,
        helper_text: str = "",
        tone: str = "#101010",
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("HomeMetricCard")
        card.setStyleSheet(
            f"""
            QFrame#HomeMetricCard {{
                background: {tone};
                border: 1px solid #2f2f2f;
                border-radius: 11px;
            }}
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(6)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 1px;
                background: transparent;
                border: none;
            }}
            """
        )

        badge_label = QLabel(badge_text)
        badge_label.setStyleSheet(
            f"""
            QLabel {{
                color: {badge_color};
                font-size: 10px;
                font-weight: 900;
                background: transparent;
                border: none;
            }}
            """
        )
        badge_label.setVisible(bool(badge_text))
        if badge_attr:
            setattr(self.owner, badge_attr, badge_label)

        title_row.addWidget(title_label, 0, Qt.AlignmentFlag.AlignVCenter)
        title_row.addStretch(1)
        title_row.addWidget(badge_label, 0, Qt.AlignmentFlag.AlignVCenter)

        value_row = QHBoxLayout()
        value_row.setContentsMargins(0, 0, 0, 0)
        value_row.setSpacing(6)

        value_label = QLabel(text)
        value_label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 19px;
                font-weight: 900;
                background: transparent;
                border: none;
            }}
            """
        )
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        setattr(self.owner, value_attr, value_label)

        unit_label = QLabel(unit_text)
        unit_label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 11px;
                font-weight: 800;
                background: transparent;
                border: none;
            }}
            """
        )
        unit_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        value_row.addWidget(value_label, 0, Qt.AlignmentFlag.AlignVCenter)
        value_row.addWidget(unit_label, 0, Qt.AlignmentFlag.AlignVCenter)
        value_row.addStretch(1)

        helper_label = QLabel(helper_text)
        helper_label.setStyleSheet(
            """
            QLabel {
                color: #6f767e;
                font-size: 9px;
                font-weight: 700;
                background: transparent;
                border: none;
            }
            """
        )
        helper_label.setVisible(bool(helper_text))

        status_label = QLabel("")
        status_label.setStyleSheet(
            """
            QLabel {
                color: #79ff9f;
                font-size: 9px;
                font-weight: 800;
                background: transparent;
                border: none;
            }
            """
        )
        status_label.hide()
        setattr(self.owner, f"{value_attr}_hint", status_label)

        layout.addLayout(title_row)
        layout.addLayout(value_row)
        layout.addWidget(helper_label)
        layout.addWidget(status_label)
        layout.addStretch(1)
        return card

    def _build_metric_row(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(
            self._build_metric_card(
                title="FPS",
                value_attr="home_metric_fps_value",
                text="0",
                color="#8dffb1",
                unit_text="FPS",
                badge_text="\u2022 T\u1ea1m D\u1eebng",
                badge_color="#ff7e7e",
                badge_attr="home_metric_fps_badge",
                helper_text="Khung hình thời gian thực",
                tone="#101612",
            ),
            1,
        )
        layout.addWidget(
            self._build_metric_card(
                title="Độ Trễ",
                value_attr="home_metric_inf_value",
                text="0",
                color="#ffd7a1",
                unit_text="MS",
                badge_text="\u2022 T\u1ea1m D\u1eebng",
                badge_color="#ff7e7e",
                badge_attr="home_metric_inf_badge",
                helper_text="Độ trễ suy luận hiện tại",
                tone="#17130f",
            ),
            1,
        )
        return row

    def _summary_row_frame(
        self,
        label_text: str,
        value_attr: str,
        value_text: str,
        value_color: str,
    ) -> QFrame:
        row = QFrame()
        row.setStyleSheet(
            """
            QFrame {
                background: #121212;
                border: 1px solid #2f2f2f;
                border-radius: 9px;
            }
            """
        )

        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        label = QLabel(label_text)
        label.setStyleSheet(
            """
            QLabel {
                color: #a7a7a7;
                font-size: 11px;
                font-weight: 700;
                background: transparent;
                border: none;
            }
            """
        )

        value = QLabel(value_text)
        value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        value.setStyleSheet(
            f"""
            QLabel {{
                color: {value_color};
                font-size: 12px;
                font-weight: 800;
                background: transparent;
                border: none;
            }}
            """
        )
        setattr(self.owner, value_attr, value)

        layout.addWidget(label)
        layout.addStretch(1)
        layout.addWidget(value)
        return row

    def _build_summary_card(
        self,
        object_name: str,
        title: str,
        title_color: str,
        rows: list[tuple[str, str, str, str]],
        *,
        toggle_attr: str | None = None,
        toggle_handler=None,
    ) -> QFrame:
        card = QFrame()
        card.setObjectName(object_name)
        card.setStyleSheet(
            """
            QFrame {
                background: #151515;
                border: 1px solid #343434;
                border-radius: 12px;
            }
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)

        accent_dot = QFrame()
        accent_dot.setFixedSize(8, 8)
        accent_dot.setStyleSheet(f"background: {title_color}; border: none; border-radius: 4px;")

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {title_color};
                font-size: 12px;
                font-weight: 900;
                letter-spacing: 1px;
                background: transparent;
                border: none;
            }}
            """
        )

        title_row.addWidget(accent_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        title_row.addWidget(title_label)
        title_row.addStretch(1)

        if toggle_attr:
            toggle_btn = QPushButton("OFF")
            toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            toggle_btn.setFixedSize(52, 24)
            toggle_btn.setStyleSheet(
                """
                QPushButton {
                    color: #ff7b7b;
                    background: #1a1111;
                    border: 1px solid #5a2525;
                    border-radius: 8px;
                    font-size: 10px;
                    font-weight: 900;
                    padding: 0 8px;
                }
                QPushButton:hover {
                    border-color: #7a3434;
                }
                """
            )
            if callable(toggle_handler):
                toggle_btn.clicked.connect(toggle_handler)
            setattr(self.owner, toggle_attr, toggle_btn)
            title_row.addWidget(toggle_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addLayout(title_row)

        for label_text, value_attr, value_text, value_color in rows:
            layout.addWidget(self._summary_row_frame(label_text, value_attr, value_text, value_color))

        return card

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class AimPanelBuilder:
    def __init__(self, owner, section_header_cls):
        self.owner = owner
        self.section_header_cls = section_header_cls

    def build(self):
        owner = self.owner

        owner.aim_workspace = QWidget()
        owner.aim_workspace.setObjectName("AimWorkspace")
        owner.aim_workspace.setStyleSheet("background: transparent; border: none;")

        aim_layout = QVBoxLayout(owner.aim_workspace)
        aim_layout.setContentsMargins(0, 0, 0, 0)
        aim_layout.setSpacing(6)

        self._build_runtime_bindings()
        self._build_display_box()
        self._build_model_box()
        self._build_capture_box()
        self._build_shortcuts_box()
        self._build_settings_box()
        self._build_smoothing_box()
        self._build_listing_box()
        self._build_advanced_toggles_box()

        main_row = QHBoxLayout()
        main_row.setContentsMargins(0, 0, 0, 0)
        main_row.setSpacing(6)

        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(6)
        left_col.addWidget(owner.aim_model_box)
        left_col.addWidget(owner.aim_settings_box)
        left_col.addWidget(owner.aim_smoothing_box)
        left_col.addWidget(owner.aim_display_box)
        left_col.addStretch(1)

        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(6)
        right_col.addWidget(owner.aim_capture_box)
        right_col.addWidget(owner.aim_shortcuts_box)
        right_col.addWidget(owner.aim_listing_box)
        right_col.addWidget(owner.aim_advanced_box)
        right_col.addStretch(1)

        main_row.addLayout(left_col, 1)
        main_row.addLayout(right_col, 1)

        aim_layout.addLayout(main_row)
        aim_layout.addStretch()

        return owner.aim_workspace

    def _group_box(self, attr_name, object_name):
        owner = self.owner
        box = MacroTitledBox("", object_name)
        setattr(owner, attr_name, box)
        return box

    def _header(self, attr_name, text, parent):
        if isinstance(parent, MacroTitledBox):
            parent.set_title(text)
            header = QWidget(parent)
            header.setFixedHeight(0)
            header.hide()
        else:
            header = self.section_header_cls(text, parent)
        setattr(self.owner, attr_name, header)
        return header

    def _create_button_row(self, label_attr, btn_attr, label_text, button_text, target_key):
        owner = self.owner
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        label = QLabel(label_text)
        label.setFixedWidth(126)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setProperty("role", "setting-label")
        owner.style_setting_label(label)

        button = QPushButton(button_text)
        button.setProperty("role", "setting-btn")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(24)
        owner.style_setting_button(button)
        button.clicked.connect(lambda: owner.start_keybind_listening(button, target_key))

        setattr(owner, label_attr, label)
        setattr(owner, btn_attr, button)

        row.addWidget(label)
        row.addWidget(button, stretch=1)
        return row

    def _create_slider_row(
        self,
        label_attr,
        slider_attr,
        value_attr,
        label_text,
        value_text,
        minimum,
        maximum,
        value,
        callback,
        *,
        value_width=44,
        step=1,
        page_step=1,
        label_width=104,
    ):
        owner = self.owner
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        label = QLabel(label_text)
        label.setFixedWidth(label_width)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setProperty("role", "setting-label")
        owner.style_setting_label(label)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setSingleStep(step)
        slider.setPageStep(page_step)
        slider.setValue(value)
        slider.setFixedHeight(20)
        slider.setMinimumWidth(120)
        slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        owner.style_scope_slider(slider)

        value_label = QLabel(value_text)
        value_label.setFixedWidth(value_width)
        value_label.setFixedHeight(24)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        owner.style_scope_value_label(value_label)

        slider.valueChanged.connect(callback)

        setattr(owner, label_attr, label)
        setattr(owner, slider_attr, slider)
        setattr(owner, value_attr, value_label)

        row.addWidget(label)
        row.addWidget(slider, stretch=1)
        row.addWidget(value_label)
        return row

    def _create_combo_row(self, label_attr, combo_attr, label_text, options, default_text, callback=None):
        owner = self.owner
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        label = QLabel(label_text)
        label.setFixedWidth(118)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setProperty("role", "setting-label")
        owner.style_setting_label(label)

        combo = QComboBox()
        combo.setFixedHeight(24)
        combo.setCursor(Qt.CursorShape.PointingHandCursor)
        combo.addItems(list(options))
        combo.setCurrentText(default_text)
        combo.setStyleSheet(
            """
            QComboBox {
                background-color: #1b1b1b;
                color: #f2f2f2;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 11px;
                font-weight: 700;
            }
            QComboBox::drop-down {
                border: none;
                width: 18px;
            }
            QComboBox QAbstractItemView {
                background: #1b1b1b;
                color: #f2f2f2;
                border: 1px solid #3a3a3a;
                selection-background-color: #2a2a2a;
            }
            """
        )
        if callback is not None:
            combo.currentTextChanged.connect(callback)

        setattr(owner, label_attr, label)
        setattr(owner, combo_attr, combo)

        row.addWidget(label)
        row.addWidget(combo, stretch=1)
        return row

    def _create_two_column_slider_block(self, left_rows, right_rows):
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent; border: none;")

        content = QHBoxLayout(wrapper)
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(12)

        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(6)

        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(6)

        for row in left_rows:
            left_col.addLayout(row)
        left_col.addStretch(1)

        for row in right_rows:
            right_col.addLayout(row)
        right_col.addStretch(1)

        content.addLayout(left_col, 1)
        content.addLayout(right_col, 1)
        return wrapper

    def _build_runtime_bindings(self):
        owner = self.owner
        owner.btn_aim_status = QPushButton("AIM : OFF")
        owner.btn_aim_status.setCursor(Qt.CursorShape.ForbiddenCursor)
        owner.update_aim_status_style(False)
        owner.btn_aim_status.hide()

        owner.lbl_aim_fps = QLabel("FPS : --")
        owner.lbl_aim_fps.setAlignment(Qt.AlignmentFlag.AlignCenter)
        owner.update_aim_metric_style(owner.lbl_aim_fps, "FPS : --", "#8dffb1")
        owner.lbl_aim_fps.hide()

        owner.lbl_aim_inf = QLabel("INF : --")
        owner.lbl_aim_inf.setAlignment(Qt.AlignmentFlag.AlignCenter)
        owner.update_aim_metric_style(owner.lbl_aim_inf, "INF : --", "#ffd7a1")
        owner.lbl_aim_inf.hide()

    def _build_display_box(self):
        owner = self.owner
        owner.aim_display_box = self._group_box("aim_display_box", "AimDisplayBox")
        layout = owner.aim_display_box.content_layout()
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self._header("header_aim_display", "Hiển Thị", owner.aim_display_box))

        display_toggle_row = QHBoxLayout()
        display_toggle_row.setContentsMargins(0, 0, 0, 0)
        display_toggle_row.setSpacing(18)

        owner.aim_chk_show_fov = QCheckBox("Hiển Thị FOV")
        owner.aim_chk_show_detect = QCheckBox("Hiển Thị Khung Detect")

        for checkbox in (owner.aim_chk_show_fov, owner.aim_chk_show_detect):
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            checkbox.setStyleSheet(
                """
                QCheckBox {
                    color: #e6e6e6;
                    font-size: 11px;
                    font-weight: 700;
                    spacing: 6px;
                    background: transparent;
                }
                QCheckBox::indicator {
                    width: 14px;
                    height: 14px;
                    border-radius: 3px;
                    border: 1px solid #5a5a5a;
                    background: #1e1e1e;
                }
                QCheckBox::indicator:checked {
                    background: #ff7070;
                    border: 1px solid #ff9c9c;
                }
                """
            )
            checkbox.stateChanged.connect(owner.on_aim_display_toggle_changed)
            display_toggle_row.addWidget(checkbox)
        display_toggle_row.addStretch(1)
        layout.addLayout(display_toggle_row)

    def _build_model_box(self):
        owner = self.owner
        owner.aim_model_box = self._group_box("aim_model_box", "AimModelBox")
        owner.aim_model_box.setFixedHeight(82)
        layout = owner.aim_model_box.content_layout()
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self._header("header_aim_model", "Model", owner.aim_model_box))

        owner.combo_aim_model = QComboBox()
        owner.combo_aim_model.setFixedHeight(26)
        owner.combo_aim_model.setCursor(Qt.CursorShape.PointingHandCursor)
        owner.combo_aim_model.setStyleSheet(
            """
            QComboBox {
                background-color: #1b1b1b;
                color: #f2f2f2;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 11px;
                font-weight: 700;
            }
            QComboBox::drop-down {
                border: none;
                width: 18px;
            }
            QComboBox QAbstractItemView {
                background: #1b1b1b;
                color: #f2f2f2;
                border: 1px solid #3a3a3a;
                selection-background-color: #2a2a2a;
            }
            """
        )
        owner.combo_aim_model.currentIndexChanged.connect(owner.on_aim_model_changed_safe)
        layout.addWidget(owner.combo_aim_model)

        owner.aim_model_status_row = QWidget()
        status_row_layout = QHBoxLayout(owner.aim_model_status_row)
        status_row_layout.setContentsMargins(2, 0, 2, 0)
        status_row_layout.setSpacing(6)
        owner.lbl_aim_model_title = QLabel("Models")
        owner.lbl_aim_model_sep = QLabel(":")
        owner.lbl_aim_model_status = QLabel("Chưa tải")
        for widget in (owner.lbl_aim_model_title, owner.lbl_aim_model_sep, owner.lbl_aim_model_status):
            widget.setStyleSheet(
                """
                QLabel {
                    color: #cfcfcf;
                    font-size: 11px;
                    font-weight: 700;
                    background: transparent;
                }
                """
            )
            status_row_layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)
        status_row_layout.addStretch(1)
        layout.addWidget(owner.aim_model_status_row)

        owner.lbl_aim_mode_info = QLabel("Chế Độ: Tăng Tốc")
        owner.lbl_aim_mode_info.setStyleSheet(
            """
            QLabel {
                color: #d7d7d7;
                font-size: 11px;
                font-weight: 700;
                background: transparent;
                padding-left: 2px;
            }
            """
        )
        layout.addWidget(owner.lbl_aim_mode_info)

        owner.lbl_aim_backend_info = QLabel("Backend: Chưa nạp")
        owner.lbl_aim_backend_info.setStyleSheet(
            """
            QLabel {
                color: #d7d7d7;
                font-size: 11px;
                font-weight: 700;
                background: transparent;
                padding-left: 2px;
            }
            """
        )
        layout.addWidget(owner.lbl_aim_backend_info)
        owner.aim_model_status_row.hide()
        owner.lbl_aim_mode_info.hide()
        owner.lbl_aim_backend_info.hide()

        owner.aim_model_meta_row = QWidget()
        meta_layout = QHBoxLayout(owner.aim_model_meta_row)
        meta_layout.setContentsMargins(2, 0, 2, 0)
        meta_layout.setSpacing(8)

        owner.lbl_aim_model_status_meta = QLabel("Runtime: Native DLL chờ")
        owner.lbl_aim_runtime_meta = QLabel("Backend: Chưa nạp")

        for widget, color in (
            (owner.lbl_aim_model_status_meta, "#cfcfcf"),
            (owner.lbl_aim_runtime_meta, "#d7d7d7"),
        ):
            widget.setStyleSheet(
                f"""
                QLabel {{
                    color: {color};
                    font-size: 10px;
                    font-weight: 700;
                    background: #1b1b1b;
                    border: 1px solid #3a3a3a;
                    border-radius: 5px;
                    padding: 2px 6px;
                }}
                """
            )
            meta_layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)
        meta_layout.addStretch(1)
        layout.addWidget(owner.aim_model_meta_row)

    def _build_capture_box(self):
        owner = self.owner
        owner.aim_capture_box = self._group_box("aim_capture_box", "AimCaptureBox")
        owner.aim_capture_box.setFixedHeight(82)
        layout = owner.aim_capture_box.content_layout()
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self._header("header_aim_capture", "Phương Thức Chụp", owner.aim_capture_box))

        owner.combo_aim_capture = QComboBox()
        owner.combo_aim_capture.setFixedHeight(26)
        owner.combo_aim_capture.setCursor(Qt.CursorShape.PointingHandCursor)
        owner.combo_aim_capture.setStyleSheet(
            """
            QComboBox {
                background-color: #1b1b1b;
                color: #f2f2f2;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 11px;
                font-weight: 700;
            }
            QComboBox::drop-down {
                border: none;
                width: 18px;
            }
            QComboBox QAbstractItemView {
                background: #1b1b1b;
                color: #f2f2f2;
                border: 1px solid #3a3a3a;
                selection-background-color: #2a2a2a;
            }
            """
        )
        owner.combo_aim_capture.addItems(["DirectX", "GDI+"])
        owner.combo_aim_capture.currentTextChanged.connect(owner.set_aim_capture_mode_ui)
        layout.addWidget(owner.combo_aim_capture)

    def _build_shortcuts_box(self):
        owner = self.owner
        owner.aim_shortcuts_box = self._group_box("aim_shortcuts_box", "AimShortcutsBox")
        layout = owner.aim_shortcuts_box.content_layout()
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self._header("header_aim_shortcuts", "Phím Tắt", owner.aim_shortcuts_box))

        layout.addLayout(
            self._create_button_row(
                "aim_lbl_emergency_stop",
                "aim_btn_emergency_stop",
                "Bật/Tắt Aim",
                "F8",
                "aim_emergency_stop_key",
            )
        )
        layout.addLayout(
            self._create_button_row(
                "aim_lbl_primary",
                "aim_btn_primary",
                "Phím Aim",
                "RIGHT MOUSE",
                "aim_primary_key",
            )
        )
        layout.addLayout(
            self._create_button_row(
                "aim_lbl_secondary",
                "aim_btn_secondary",
                "Phím Aim Phụ",
                "LEFT CTRL",
                "aim_secondary_key",
            )
        )
        layout.addLayout(
            self._create_button_row(
                "aim_lbl_trigger",
                "aim_btn_trigger",
                "Bật/Tắt Trigger",
                "F7",
                "aim_trigger_key",
            )
        )

    def _build_settings_box(self):
        owner = self.owner
        owner.aim_settings_box = self._group_box("aim_settings_box", "AimSettingsBox")
        layout = owner.aim_settings_box.content_layout()
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self._header("header_aim_settings", "Cài Đặt", owner.aim_settings_box))

        for row in (
            self._create_slider_row(
                "aim_lbl_fov",
                "aim_slider_fov",
                "aim_fov_value_label",
                "Vùng FOV",
                "300",
                10,
                640,
                300,
                owner.update_aim_fov_label,
                page_step=10,
            ),
            self._create_slider_row(
                "aim_lbl_confidence",
                "aim_slider_confidence",
                "aim_confidence_value_label",
                "Ngưỡng Tin Cậy AI",
                "45%",
                1,
                100,
                45,
                owner.update_aim_confidence_label,
                page_step=5,
            ),
            self._create_slider_row(
                "aim_lbl_trigger_delay",
                "aim_slider_trigger_delay",
                "aim_trigger_delay_value_label",
                "Độ Trễ Tự Bắn",
                "100 ms",
                10,
                1000,
                100,
                owner.update_aim_trigger_delay_label,
                value_width=60,
                step=10,
                page_step=50,
            ),
            self._create_slider_row(
                "aim_lbl_capture_fps",
                "aim_slider_capture_fps",
                "aim_capture_fps_value_label",
                "Tốc Độ Chụp (FPS)",
                "144",
                1,
                240,
                144,
                owner.update_aim_capture_fps_label,
                page_step=10,
            ),
            self._create_combo_row(
                "aim_lbl_target_priority",
                "combo_aim_target_priority",
                "Ưu Tiên",
                ("Body -> Head", "Head -> Body"),
                "Body -> Head",
            ),
        ):
            layout.addLayout(row)

    def _build_smoothing_box(self):
        owner = self.owner
        owner.aim_smoothing_box = self._group_box("aim_smoothing_box", "AimSmoothingBox")
        layout = owner.aim_smoothing_box.content_layout()
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self._header("header_aim_smoothing", "Độ Nhạy / Độ Mượt", owner.aim_smoothing_box))

        for row in (
            self._create_slider_row(
                "aim_lbl_sensitivity",
                "aim_slider_sensitivity",
                "aim_sensitivity_value_label",
                "Độ Nhạy Chuột",
                "0.80",
                1,
                100,
                80,
                owner.update_aim_sensitivity_label,
            ),
            self._create_slider_row(
                "aim_lbl_ema",
                "aim_slider_ema",
                "aim_ema_value_label",
                "Độ Mượt",
                "0.50",
                1,
                100,
                50,
                owner.update_aim_ema_label,
            ),
            self._create_slider_row(
                "aim_lbl_jitter",
                "aim_slider_jitter",
                "aim_jitter_value_label",
                "Độ Rung Chuột",
                "4",
                0,
                15,
                4,
                owner.update_aim_jitter_label,
            ),
            self._create_slider_row(
                "aim_lbl_primary_position",
                "aim_slider_primary_position",
                "aim_primary_position_value_label",
                "Vị Trí Aim Chính",
                "50",
                0,
                100,
                50,
                owner.update_aim_primary_position_label,
                page_step=5,
            ),
            self._create_slider_row(
                "aim_lbl_secondary_position",
                "aim_slider_secondary_position",
                "aim_secondary_position_value_label",
                "Vị Trí Aim Phụ",
                "50",
                0,
                100,
                50,
                owner.update_aim_secondary_position_label,
                page_step=5,
            ),
        ):
            layout.addLayout(row)

    def _build_listing_box(self):
        owner = self.owner
        owner.aim_listing_box = self._group_box("aim_listing_box", "AimListingBox")
        owner.aim_listing_box.setFixedHeight(238)
        layout = owner.aim_listing_box.content_layout()
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self._header("header_aim_listing", "Danh Sách Liệt Kê", owner.aim_listing_box))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #151515;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #ff9fb0;
                border-radius: 3px;
                min-height: 22px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
                background: transparent;
                border: none;
            }
            """
        )

        content = QWidget()
        content.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 2, 0)
        content_layout.setSpacing(6)

        owner.aim_listing_controls = {}
        for spec in self._listing_slider_specs():
            callback = lambda value, key=spec["key"]: owner.update_aim_listing_slider_label(key, value)
            row = self._create_slider_row(
                spec["label_attr"],
                spec["slider_attr"],
                spec["value_attr"],
                spec["label"],
                spec["value_text"],
                spec["min"],
                spec["max"],
                spec["slider_default"],
                callback,
                value_width=spec.get("value_width", 44),
                step=spec.get("step", 1),
                page_step=spec.get("page_step", 5),
                label_width=108,
            )
            content_layout.addLayout(row)
            owner.aim_listing_controls[spec["key"]] = {
                "spec": spec,
                "slider": getattr(owner, spec["slider_attr"]),
                "value_label": getattr(owner, spec["value_attr"]),
            }

        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

    def _build_advanced_toggles_box(self):
        owner = self.owner
        owner.aim_advanced_box = self._group_box("aim_advanced_box", "AimAdvancedBox")
        owner.aim_advanced_box.setFixedHeight(238)
        layout = owner.aim_advanced_box.content_layout()
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self._header("header_aim_advanced", "Tùy Chọn Nâng Cao", owner.aim_advanced_box))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #151515;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #66f0ff;
                border-radius: 3px;
                min-height: 22px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
                background: transparent;
                border: none;
            }
            """
        )

        content = QWidget()
        content.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 6, 0)
        content_layout.setSpacing(7)

        owner.aim_toggle_controls = {}
        for key, label in self._advanced_toggle_specs():
            checkbox = QCheckBox(label)
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            checkbox.setStyleSheet(
                """
                QCheckBox {
                    color: #e6e6e6;
                    font-size: 11px;
                    font-weight: 700;
                    spacing: 7px;
                    background: transparent;
                }
                QCheckBox::indicator {
                    width: 14px;
                    height: 14px;
                    border-radius: 3px;
                    border: 1px solid #5a5a5a;
                    background: #1e1e1e;
                }
                QCheckBox::indicator:checked {
                    background: #66f0ff;
                    border: 1px solid #9af7ff;
                }
                """
            )
            checkbox.stateChanged.connect(owner.on_aim_advanced_toggle_changed)
            content_layout.addWidget(checkbox)
            owner.aim_toggle_controls[key] = checkbox

        owner.aim_dropdown_controls = {}
        for spec in self._advanced_dropdown_specs():
            row = self._create_combo_row(
                spec["label_attr"],
                spec["combo_attr"],
                spec["label"],
                spec["options"],
                spec["default"],
                owner.on_aim_advanced_dropdown_changed,
            )
            content_layout.addLayout(row)
            owner.aim_dropdown_controls[spec["key"]] = {
                "spec": spec,
                "combo": getattr(owner, spec["combo_attr"]),
            }

        owner.aim_color_controls = {}
        for key, label, default_value in self._advanced_color_specs():
            row = self._create_action_row(
                f"aim_lbl_color_{key.replace(' ', '_').lower()}",
                f"aim_btn_color_{key.replace(' ', '_').lower()}",
                label,
                default_value,
                lambda _checked=False, color_key=key: owner.choose_aim_color(color_key),
            )
            content_layout.addLayout(row)
            owner.aim_color_controls[key] = getattr(owner, f"aim_btn_color_{key.replace(' ', '_').lower()}")

        owner.aim_file_controls = {}
        for key, label in self._advanced_file_specs():
            row = self._create_action_row(
                f"aim_lbl_file_{key.replace(' ', '_').lower()}",
                f"aim_btn_file_{key.replace(' ', '_').lower()}",
                label,
                "Chọn DLL",
                lambda _checked=False, file_key=key: owner.choose_aim_file_location(file_key),
            )
            content_layout.addLayout(row)
            owner.aim_file_controls[key] = getattr(owner, f"aim_btn_file_{key.replace(' ', '_').lower()}")

        owner.aim_minimize_controls = {}
        for key, label in self._advanced_minimize_specs():
            checkbox = QCheckBox(label)
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            checkbox.setStyleSheet(
                """
                QCheckBox {
                    color: #bfc6cf;
                    font-size: 11px;
                    font-weight: 700;
                    spacing: 7px;
                    background: transparent;
                }
                QCheckBox::indicator {
                    width: 14px;
                    height: 14px;
                    border-radius: 3px;
                    border: 1px solid #5a5a5a;
                    background: #1e1e1e;
                }
                QCheckBox::indicator:checked {
                    background: #a98cff;
                    border: 1px solid #c4b4ff;
                }
                """
            )
            checkbox.stateChanged.connect(owner.on_aim_advanced_toggle_changed)
            content_layout.addWidget(checkbox)
            owner.aim_minimize_controls[key] = checkbox

        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

    def _create_action_row(self, label_attr, button_attr, label_text, button_text, callback):
        owner = self.owner
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        label = QLabel(label_text)
        label.setFixedWidth(124)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setProperty("role", "setting-label")
        owner.style_setting_label(label)

        button = QPushButton(button_text)
        button.setProperty("role", "setting-btn")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(24)
        owner.style_setting_button(button)
        button.clicked.connect(callback)

        setattr(owner, label_attr, label)
        setattr(owner, button_attr, button)

        row.addWidget(label)
        row.addWidget(button, stretch=1)
        return row

    def _advanced_toggle_specs(self):
        return [
            ("Constant AI Tracking", "Tracking Liên Tục"),
            ("Sticky Aim", "Sticky Aim"),
            ("Predictions", "Dự Đoán"),
            ("Enable Model Switch Keybind", "Bật Phím Đổi Model"),
            ("FOV", "Logic FOV"),
            ("Dynamic FOV", "FOV Động"),
            ("Third Person Support", "Góc Nhìn Thứ 3"),
            ("Masking", "Masking"),
            ("Cursor Check", "Cursor Check"),
            ("Spray Mode", "Spray Mode"),
            # Đã làm sạch chú thích lỗi mã hóa.
            # Đã làm sạch chú thích lỗi mã hóa.
            ("Collect Data While Playing", "Thu Data Khi Chơi"),
            ("Auto Label Data", "Auto Label Data"),
            ("LG HUB Mouse Movement", "LG HUB Mouse"),
            # Đã làm sạch chú thích lỗi mã hóa.
            ("Debug Mode", "Debug Mode"),
            ("UI TopMost", "UI Luôn Trên Cùng"),
            ("StreamGuard", "StreamGuard"),
            # Đã làm sạch chú thích lỗi mã hóa.
            # Đã làm sạch chú thích lỗi mã hóa.
        ]

    def _advanced_dropdown_specs(self):
        return [
            {
                "key": "Prediction Method",
                "label": "Kiểu Dự Đoán",
                "label_attr": "aim_lbl_prediction_method",
                "combo_attr": "combo_aim_prediction_method",
                "default": "Kalman Filter",
                "options": ("Kalman Filter", "Shall0e's Prediction", "wisethef0x's EMA Prediction"),
            },
            {
                "key": "Detection Area Type",
                "label": "Vùng Detect",
                "label_attr": "aim_lbl_detection_area_type",
                "combo_attr": "combo_aim_detection_area_type",
                "default": "Closest to Center Screen",
                "options": ("Closest to Center Screen", "Closest to Mouse"),
            },
            {
                "key": "Aiming Boundaries Alignment",
                "label": "Căn Biên Aim",
                "label_attr": "aim_lbl_aiming_boundaries",
                "combo_attr": "combo_aim_aiming_boundaries",
                "default": "Center",
                "options": ("Center", "Top", "Bottom"),
            },
            {
                "key": "Mouse Movement Method",
                "label": "Kiểu Di Chuột",
                "label_attr": "aim_lbl_mouse_movement_method",
                "combo_attr": "combo_aim_mouse_movement_method",
                "default": "Mouse Event",
                "options": ("Mouse Event", "SendInput", "LG HUB", "Razer Synapse (Require Razer Peripheral)", "ddxoft Virtual Input Driver"),
            },
            {
                "key": "Tracer Position",
                "label": "Vị Trí Tracer",
                "label_attr": "aim_lbl_tracer_position",
                "combo_attr": "combo_aim_tracer_position",
                "default": "Bottom",
                "options": ("Top", "Middle", "Bottom"),
            },
            {
                "key": "Movement Path",
                "label": "Đường Aim",
                "label_attr": "aim_lbl_movement_path",
                "combo_attr": "combo_aim_movement_path",
                "default": "Cubic Bezier",
                "options": ("Cubic Bezier", "Exponential", "Linear", "Adaptive", "Perlin Noise"),
            },
            {
                "key": "Image Size",
                "label": "Image Size",
                "label_attr": "aim_lbl_image_size",
                "combo_attr": "combo_aim_image_size",
                "default": "640",
                "options": ("640", "512", "416", "320", "256", "160"),
            },
            {
                "key": "Target Class",
                "label": "Class Mục Tiêu",
                "label_attr": "aim_lbl_target_class",
                "combo_attr": "combo_aim_target_class",
                "default": "Best Confidence",
                "options": ("Best Confidence", "body", "head", "enemy"),
            },
        ]

    def _advanced_color_specs(self):
        return [
            ("FOV Color", "Màu FOV", "#FF8080FF"),
            ("Detected Player Color", "Màu ESP", "#FF00FFFF"),
            ("Theme Color", "Màu Theme", "#FF722ED1"),
        ]

    def _advanced_file_specs(self):
        return [
            ("ddxoft DLL Location", "ddxoft DLL"),
        ]

    def _advanced_minimize_specs(self):
        return [
            ("Aim Assist", "Panel Aim Assist"),
            ("Aim Config", "Panel Aim Config"),
            ("Predictions", "Panel Predictions"),
            ("Auto Trigger", "Panel Auto Trigger"),
            ("FOV Config", "Panel FOV Config"),
            ("ESP Config", "Panel ESP Config"),
            ("Model Settings", "Panel Model Settings"),
            ("Settings Menu", "Panel Settings Menu"),
            ("X/Y Percentage Adjustment", "Panel X/Y %"),
            ("Theme Settings", "Panel Theme"),
            ("Screen Settings", "Panel Screen"),
        ]

    def _listing_slider_specs(self):
        return [
            {
                "key": "Dynamic FOV Size",
                "label": "Kích Thước FOV Động",
                "label_attr": "aim_lbl_dynamic_fov",
                "slider_attr": "aim_slider_dynamic_fov",
                "value_attr": "aim_dynamic_fov_value_label",
                "min": 10,
                "max": 640,
                "slider_default": 10,
                "default": 10,
                "value_text": "10",
                "format": "int",
                "scale": 1,
                "page_step": 10,
            },
            {
                "key": "Sticky Aim Threshold",
                "label": "Ngưỡng Bám Mục Tiêu",
                "label_attr": "aim_lbl_sticky_threshold",
                "slider_attr": "aim_slider_sticky_threshold",
                "value_attr": "aim_sticky_threshold_value_label",
                "min": 0,
                "max": 100,
                "slider_default": 0,
                "default": 0,
                "value_text": "0",
                "format": "int",
                "scale": 1,
            },
            {
                "key": "Y Offset (Up/Down)",
                "label": "Lệch Y",
                "label_attr": "aim_lbl_y_offset",
                "slider_attr": "aim_slider_y_offset",
                "value_attr": "aim_y_offset_value_label",
                "min": -150,
                "max": 150,
                "slider_default": 0,
                "default": 0,
                "value_text": "0",
                "format": "int",
                "scale": 1,
            },
            {
                "key": "Y Offset (%)",
                "label": "Lệch Y %",
                "label_attr": "aim_lbl_y_offset_percent",
                "slider_attr": "aim_slider_y_offset_percent",
                "value_attr": "aim_y_offset_percent_value_label",
                "min": 0,
                "max": 100,
                "slider_default": 50,
                "default": 50,
                "value_text": "50%",
                "format": "percent",
                "scale": 1,
            },
            {
                "key": "X Offset (Left/Right)",
                "label": "Lệch X",
                "label_attr": "aim_lbl_x_offset",
                "slider_attr": "aim_slider_x_offset",
                "value_attr": "aim_x_offset_value_label",
                "min": -150,
                "max": 150,
                "slider_default": 0,
                "default": 0,
                "value_text": "0",
                "format": "int",
                "scale": 1,
            },
            {
                "key": "X Offset (%)",
                "label": "Lệch X %",
                "label_attr": "aim_lbl_x_offset_percent",
                "slider_attr": "aim_slider_x_offset_percent",
                "value_attr": "aim_x_offset_percent_value_label",
                "min": 0,
                "max": 100,
                "slider_default": 50,
                "default": 50,
                "value_text": "50%",
                "format": "percent",
                "scale": 1,
            },
            {
                "key": "Kalman Lead Time",
                "label": "Kalman Lead",
                "label_attr": "aim_lbl_kalman_lead",
                "slider_attr": "aim_slider_kalman_lead",
                "value_attr": "aim_kalman_lead_value_label",
                "min": 2,
                "max": 30,
                "slider_default": 10,
                "default": 0.10,
                "value_text": "0.10",
                "format": "float2",
                "scale": 100,
            },
            {
                "key": "WiseTheFox Lead Time",
                "label": "Wise Lead",
                "label_attr": "aim_lbl_wise_lead",
                "slider_attr": "aim_slider_wise_lead",
                "value_attr": "aim_wise_lead_value_label",
                "min": 2,
                "max": 30,
                "slider_default": 15,
                "default": 0.15,
                "value_text": "0.15",
                "format": "float2",
                "scale": 100,
            },
            {
                "key": "Shalloe Lead Multiplier",
                "label": "Shalloe Lead",
                "label_attr": "aim_lbl_shalloe_lead",
                "slider_attr": "aim_slider_shalloe_lead",
                "value_attr": "aim_shalloe_lead_value_label",
                "min": 2,
                "max": 20,
                "slider_default": 6,
                "default": 3.0,
                "value_text": "3.0",
                "format": "float1",
                "scale": 2,
            },
            {
                "key": "AI Confidence Font Size",
                "label": "Font Detect",
                "label_attr": "aim_lbl_conf_font_size",
                "slider_attr": "aim_slider_conf_font_size",
                "value_attr": "aim_conf_font_size_value_label",
                "min": 1,
                "max": 30,
                "slider_default": 20,
                "default": 20,
                "value_text": "20",
                "format": "int",
                "scale": 1,
            },
            {
                "key": "Corner Radius",
                "label": "Bo Góc ESP",
                "label_attr": "aim_lbl_corner_radius",
                "slider_attr": "aim_slider_corner_radius",
                "value_attr": "aim_corner_radius_value_label",
                "min": 0,
                "max": 100,
                "slider_default": 0,
                "default": 0,
                "value_text": "0",
                "format": "int",
                "scale": 1,
            },
            {
                "key": "Border Thickness",
                "label": "Dày Viền",
                "label_attr": "aim_lbl_border_thickness",
                "slider_attr": "aim_slider_border_thickness",
                "value_attr": "aim_border_thickness_value_label",
                "min": 1,
                "max": 100,
                "slider_default": 10,
                "default": 1.0,
                "value_text": "1.0",
                "format": "float1",
                "scale": 10,
            },
            {
                "key": "Opacity",
                "label": "Độ Trong",
                "label_attr": "aim_lbl_opacity",
                "slider_attr": "aim_slider_opacity",
                "value_attr": "aim_opacity_value_label",
                "min": 0,
                "max": 10,
                "slider_default": 10,
                "default": 1.0,
                "value_text": "1.0",
                "format": "float1",
                "scale": 10,
            },
        ]

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFrame, QGridLayout, QGroupBox, QComboBox, QSizePolicy, QSlider, QCheckBox,
                             QStackedWidget, QGraphicsDropShadowEffect, QMessageBox, QSystemTrayIcon, QMenu, QStyledItemDelegate,
                             QStylePainter, QStyleOptionComboBox, QStyle, QColorDialog, QFileDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint, QSize, QEvent, QRect
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QBrush, QKeySequence, QPixmap
import ctypes
import win32api
import winsound
import sys
import os
from pathlib import Path

# IMPORT LOCAL COMPONENTS



# IMPORT HELPERS & MANAGERS (STEP 6)

class BevelLine(QWidget):
    def __init__(self, side: str, color: str = "#333333", parent=None):
        super().__init__(parent)
        self.side = side
        self.color = QColor(color)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.color))

        width = self.width()
        height = self.height()
        center_y = 0
        thickness = 1
        cut = min(5, max(2, width // 8))

        if self.side == "left":
            points = [
                QPoint(0, center_y + thickness),
                QPoint(cut, center_y - thickness),
                QPoint(width, center_y - thickness),
                QPoint(width, center_y + thickness),
            ]
        else:
            points = [
                QPoint(0, center_y - thickness),
                QPoint(width - cut, center_y - thickness),
                QPoint(width, center_y + thickness),
                QPoint(0, center_y + thickness),
            ]

        painter.drawPolygon(*points)
        painter.end()


class FlatLine(QWidget):
    def __init__(self, color: str = "#333333", parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(8)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.color))
        center_y = self.height() // 2
        painter.drawRect(0, center_y - 1, self.width(), 2)
        painter.end()


class SectionHeader(QWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("SectionHeader")
        self._text = text
        self.title_label = self
        self.setFixedHeight(16)

    def setText(self, text: str):
        self._text = text
        self.update()

    def text(self) -> str:
        return self._text

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        font = painter.font()
        font.setPixelSize(10)
        font.setBold(True)
        painter.setFont(font)

        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(self._text)
        pad_x = 12
        bg_w = text_w + (pad_x * 2)
        bg_h = fm.height()
        bg_x = max(0, (self.width() - bg_w) // 2)
        line_y = 0
        bg_y = line_y - (bg_h // 2) + 1

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#1b1b1b"))
        painter.drawRect(bg_x, bg_y, bg_w, bg_h)

        painter.setPen(QColor("#e5e5e5"))
        painter.drawText(QRect(bg_x, bg_y, bg_w, bg_h), int(Qt.AlignmentFlag.AlignCenter), self._text)
        painter.end()


class MacroTitledBox(QFrame):
    def __init__(self, title: str, object_name: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        if object_name:
            self.setObjectName(object_name)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._content_layout = QVBoxLayout(self)
        self._content_layout.setContentsMargins(10, 16, 10, 8)
        self._content_layout.setSpacing(6)

    def content_layout(self):
        return self._content_layout

    def set_title(self, title: str):
        self._title = title
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        border_rect = self.rect().adjusted(0, 6, -1, -1)
        painter.setPen(QPen(QColor("#333333"), 1))
        painter.setBrush(QBrush(QColor("#1b1b1b")))
        painter.drawRoundedRect(border_rect, 10, 10)

        font = painter.font()
        font.setFamily("Segoe UI")
        font.setPixelSize(11)
        font.setBold(True)
        painter.setFont(font)

        fm = painter.fontMetrics()
        title_w = fm.horizontalAdvance(self._title) + 22
        title_h = max(18, fm.height() + 2)
        title_x = max(12, (self.width() - title_w) // 2)
        title_y = border_rect.top() - (title_h // 2) - 1
        title_rect = QRect(title_x, title_y, title_w, title_h)

        painter.fillRect(title_rect, QColor("#1b1b1b"))
        shadow_rect = title_rect.adjusted(0, 1, 0, 1)
        painter.setPen(QColor(0, 0, 0, 140))
        painter.drawText(shadow_rect, int(Qt.AlignmentFlag.AlignCenter), self._title)
        painter.setPen(QColor("#e5e5e5"))
        painter.drawText(title_rect, int(Qt.AlignmentFlag.AlignCenter), self._title)
        painter.end()


class MobileSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = bool(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(52, 28)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        checked = bool(checked)
        if self._checked == checked:
            return
        self._checked = checked
        self.update()
        self.toggled.emit(self._checked)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect().adjusted(1, 3, -1, -3)
        track_color = QColor("#8a56ff") if self._checked else QColor("#3a3a3a")
        track_border = QColor("#b088ff") if self._checked else QColor("#565656")

        painter.setPen(QPen(track_border, 1))
        painter.setBrush(QBrush(track_color))
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)

        knob_size = rect.height() - 4
        knob_y = rect.y() + 2
        knob_x = rect.right() - knob_size - 2 if self._checked else rect.x() + 2
        knob_rect = QRectF(knob_x, knob_y, knob_size, knob_size)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawEllipse(knob_rect)
        painter.end()


class SplitSectionHeader(QWidget):
    def __init__(self, left_text: str, right_text: str, separator_width: int = 1, separator_gap: int = 10, parent=None):
        super().__init__(parent)
        self.setObjectName("SplitSectionHeader")
        self.setFixedHeight(14)
        self.left_text = left_text
        self.right_text = right_text
        self.separator_width = separator_width
        self.separator_gap = separator_gap
        self.center_gap_width = max(1, ((separator_gap * 2) + separator_width) - 2)
        self.line_color = QColor("#333333")
        self.left_text_color = QColor("#eefbff")
        self.right_text_color = QColor("#fff1f8")
        self.text_gap = 6
        self.outer_margin = 8
        self.font = QFont()
        self.font.setPixelSize(12)
        self.font.setBold(True)

    def _draw_flat_line(self, painter: QPainter, x1: int, x2: int, center_y: int):
        if x2 <= x1:
            return
        painter.drawRect(x1, center_y - 1, x2 - x1, 2)

    def _draw_bevel_left(self, painter: QPainter, x1: int, x2: int, center_y: int):
        if x2 <= x1:
            return
        cut = min(5, max(2, (x2 - x1) // 8))
        painter.drawPolygon(
            QPoint(x1, center_y + 1),
            QPoint(x1 + cut, center_y - 1),
            QPoint(x2, center_y - 1),
            QPoint(x2, center_y + 1),
        )

    def _draw_bevel_right(self, painter: QPainter, x1: int, x2: int, center_y: int):
        if x2 <= x1:
            return
        cut = min(5, max(2, (x2 - x1) // 8))
        painter.drawPolygon(
            QPoint(x1, center_y - 1),
            QPoint(x2 - cut, center_y - 1),
            QPoint(x2, center_y + 1),
            QPoint(x1, center_y + 1),
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.line_color))

        rect = self.rect()
        center_y = rect.height() // 2
        total_width = rect.width()
        center_x = total_width // 2
        half_width = center_x - self.outer_margin
        right_half_width = total_width - self.outer_margin - center_x

        painter.setFont(self.font)
        metrics = painter.fontMetrics()

        left_text_width = metrics.horizontalAdvance(self.left_text)
        left_text_x = self.outer_margin + max(0, (half_width - left_text_width) // 2)
        left_text_y = (rect.height() + metrics.ascent() - metrics.descent()) // 2 - 1

        right_text_width = metrics.horizontalAdvance(self.right_text)
        right_text_x = center_x + max(0, (right_half_width - right_text_width) // 2)
        right_text_y = left_text_y

        self._draw_bevel_left(painter, self.outer_margin, max(self.outer_margin, left_text_x - self.text_gap), center_y)
        self._draw_flat_line(painter, left_text_x + left_text_width + self.text_gap, max(left_text_x + left_text_width + self.text_gap, right_text_x - self.text_gap), center_y)
        self._draw_bevel_right(painter, right_text_x + right_text_width + self.text_gap, total_width - self.outer_margin, center_y)

        painter.setPen(self.left_text_color)
        painter.drawText(left_text_x, left_text_y, self.left_text)
        painter.setPen(self.right_text_color)
        painter.drawText(right_text_x, right_text_y, self.right_text)
        painter.end()


class MarqueeLabel(QLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self._source_text = ""
        self._display_text = ""
        self._timer = QTimer(self)
        self._timer.setInterval(140)
        self._timer.timeout.connect(self._tick)
        self.set_source_text(text)

    def set_source_text(self, text: str):
        self._source_text = (text or "").strip()
        if not self._source_text:
            self._display_text = ""
            self.setText("")
            self._timer.stop()
            return
        self._display_text = f"   {self._source_text}   "
        self.setText(self._display_text)
        if not self._timer.isActive():
            self._timer.start()

    def _tick(self):
        if not self._display_text:
            return
        self._display_text = self._display_text[1:] + self._display_text[0]
        self.setText(self._display_text)


class CenteredComboBox(QComboBox):
    def __init__(self, parent=None, center_mode: str = "field"):
        super().__init__(parent)
        self.setEditable(False)
        self.setIconSize(QSize(28, 14))
        self.center_mode = center_mode

    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        option.currentText = ""
        option.currentIcon = QIcon()
        painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)

        if self.center_mode == "full":
            text_rect = self.rect().adjusted(2, 0, -2, 0)
        else:
            text_rect = self.style().subControlRect(
                QStyle.ComplexControl.CC_ComboBox,
                option,
                QStyle.SubControl.SC_ComboBoxEditField,
                self,
            )
            text_rect.adjust(2, 0, -2, 0)
        icon = self.itemIcon(self.currentIndex()) if self.currentIndex() >= 0 else QIcon()
        if not icon.isNull():
            pixmap = icon.pixmap(self.iconSize())
            x = text_rect.center().x() - (pixmap.width() // 2)
            y = text_rect.center().y() - (pixmap.height() // 2)
            painter.drawPixmap(x, y, pixmap)
        else:
            painter.setPen(QColor("#f2f2f2"))
            painter.drawText(text_rect, int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter), self.currentText())
        painter.end()


class IconOnlyComboDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()

        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#232323"))
        else:
            painter.fillRect(option.rect, QColor("#1b1b1b"))

        icon = index.data(Qt.ItemDataRole.DecorationRole)
        if isinstance(icon, QIcon) and not icon.isNull():
            pixmap = icon.pixmap(36, 18)
            x = option.rect.center().x() - (pixmap.width() // 2)
            y = option.rect.center().y() - (pixmap.height() // 2)
            painter.drawPixmap(x, y, pixmap)

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(48, 24)


class CrosshairOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.ToolTip
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        w = win32api.GetSystemMetrics(0)
        h = win32api.GetSystemMetrics(1)
        self.setGeometry(0, 0, w, h)

        self.active = False
        self.style = "10: X-Shape"
        self.color = QColor(255, 255, 255)
        self.ads_mode = "HOLD"
        self.ads_active = False
        self.rmb_prev = False

        self.timer_ads = QTimer(self)
        self.timer_ads.timeout.connect(self.check_ads)
        self.timer_ads.setInterval(100)
        QTimer.singleShot(500, lambda: self.set_capture_invisible(int(self.winId())))

    def set_capture_invisible(self, hwnd_int):
        try:
            ctypes.windll.user32.SetWindowDisplayAffinity(int(hwnd_int), 0)
        except Exception:
            pass

    def check_ads(self):
        if not self.active:
            return
        if not Utils.is_game_active():
            if not self.isVisible():
                self.show()
            return
        lmb_down = win32api.GetKeyState(0x01) < 0
        rmb_down = win32api.GetKeyState(0x02) < 0
        should_hide = lmb_down or rmb_down
        if should_hide:
            if self.isVisible():
                self.hide()
        else:
            if not self.isVisible():
                self.show()
        self.rmb_prev = rmb_down

    def set_ads_mode(self, mode):
        self.ads_mode = str(mode or "HOLD").upper()
        self.ads_active = False
        self.rmb_prev = False
        if self.active and self.ads_mode != "HOLD":
            self.show()

    def reset_toggle_state(self):
        if self.ads_mode == "TOGGLE":
            self.ads_active = False
            if self.active:
                self.show()

    def set_active(self, active):
        self.active = bool(active)
        if self.active:
            if not self.timer_ads.isActive():
                self.timer_ads.start()
            self.show()
        else:
            if self.timer_ads.isActive():
                self.timer_ads.stop()
            self.hide()
        self.update()

    def set_style(self, style):
        self.style = str(style or "10: X-Shape")
        self.update()

    def set_color(self, color_name):
        colors = {
            "Đỏ": QColor(255, 30, 30),
            "Đỏ Cam": QColor(255, 69, 0),
            "Cam": QColor(255, 140, 0),
            "Vàng": QColor(255, 255, 0),
            "Xanh Lá": QColor(0, 255, 0),
            "Xanh Ngọc": QColor(0, 255, 255),
            "Xanh Dương": QColor(0, 180, 255),
            "Tím": QColor(180, 0, 255),
            "Tím Hồng": QColor(255, 60, 255),
            "Hồng": QColor(255, 105, 180),
            "Trắng": QColor(255, 255, 255),
            "Bạc": QColor(192, 192, 192),
        }
        self.color = colors.get(str(color_name), QColor(255, 255, 255))
        self.update()

    def paintEvent(self, event):
        if not self.active:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = self.width() // 2
        cy = self.height() // 2

        def draw_shape(p):
            if self.style == "10: X-Shape":
                l = 6
                gap = 3
                p.drawLine(cx - gap - l, cy - gap - l, cx - gap, cy - gap)
                p.drawLine(cx + gap + l, cy + gap + l, cx + gap, cy + gap)
                p.drawLine(cx - gap - l, cy + gap + l, cx - gap, cy + gap)
                p.drawLine(cx + gap + l, cy - gap - l, cx + gap, cy - gap)
            elif self.style == "6: Micro Dot":
                p.drawEllipse(QPoint(cx, cy), 2, 2)
            elif self.style == "14: Square Dot":
                p.drawRect(cx - 2, cy - 2, 4, 4)
            else:
                gap = 4
                l = 8
                p.drawLine(cx - gap - l, cy, cx - gap, cy)
                p.drawLine(cx + gap, cy, cx + gap + l, cy)
                p.drawLine(cx, cy - gap - l, cx, cy - gap)
                p.drawLine(cx, cy + gap, cx, cy + gap + l)

        pen_outline = QPen(QColor(0, 0, 0, 255))
        pen_outline.setWidth(4)
        pen_outline.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_outline)
        if self.style in {"6: Micro Dot", "14: Square Dot"}:
            painter.setBrush(QBrush(QColor(0, 0, 0, 255)))
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
        draw_shape(painter)

        pen_core = QPen(self.color)
        pen_core.setWidth(2)
        pen_core.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_core)
        if self.style in {"6: Micro Dot", "14: Square Dot"}:
            painter.setBrush(QBrush(self.color))
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
        draw_shape(painter)


class GameOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        screen = QApplication.primaryScreen().geometry()
        self.w, self.h = 300, 26
        self.x_pos = (screen.width() - self.w) // 2
        self.y_pos = screen.height() - self.h
        self.setGeometry(self.x_pos, self.y_pos, self.w, self.h)

        self.frame = QFrame(self)
        self.frame.setGeometry(0, 0, self.w, self.h)
        self._frame_qss = "QFrame { background-color: rgba(10, 10, 10, 180); border: 1px solid #444444; border-radius: 6px; }"
        self.frame.setStyleSheet(self._frame_qss)

        self.lbl = QLabel(self.frame)
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl.setGeometry(0, 0, self.w, self.h)
        self.lbl.setText("Di88-VP MACRO")
        self._label_qss_tpl = "color: {color}; font-weight: 900; font-family: 'Segoe UI'; font-size: 10px; border: none; background: transparent;"
        self.lbl.setStyleSheet(self._label_qss_tpl.format(color="#00FF00"))

        self.last_color = None
        self.last_full_text = ""
        self.is_firing = False

        self.flash_timer = QTimer(self)
        self.flash_timer.setInterval(100)
        self.flash_timer.timeout.connect(self._do_flash)
        self.color_idx = 0

        self.detect_timer = QTimer(self)
        self.detect_timer.setInterval(200)
        self.detect_timer.timeout.connect(self._do_detect_flash)
        self.detect_idx = 0

        self.show()
        self._adjust_to_content("Di88-VP MACRO")

    def _do_flash(self):
        color = "#00FFFF" if self.color_idx % 2 == 0 else "#001a1a"
        self.lbl.setStyleSheet(self._label_qss_tpl.format(color=color))
        self.frame.setStyleSheet(self._frame_qss)
        self.color_idx += 1

    def _do_detect_flash(self):
        if self.flash_timer.isActive():
            return
        color = "#FFA500" if self.detect_idx % 2 == 0 else "#331a00"
        self.lbl.setStyleSheet(self._label_qss_tpl.format(color=color))
        self.frame.setStyleSheet(self._frame_qss)
        self.detect_idx += 1

    def _adjust_to_content(self, text):
        width = self.lbl.fontMetrics().horizontalAdvance(text) + 40
        self.w = width
        screen_w = QApplication.primaryScreen().geometry().width()
        self.setGeometry((screen_w - self.w) // 2, self.y_pos, self.w, self.h)
        self.frame.setGeometry(0, 0, self.w, self.h)
        self.lbl.setGeometry(0, 0, self.w, self.h)

    def update_status(self, gun_name, scope, stance, grip="NONE", muzzle="NONE", is_paused=False, is_firing=False, ai_status="HIBERNATE"):
        self.is_firing = bool(is_firing)
        if is_paused:
            text, color = "TẠM DỪNG", "#FF0000"
        elif gun_name == "NONE":
            text, color = "CHƯA CÓ SÚNG", "#FFFF00"
        else:
            scope_raw = str(scope).lower()
            sc_val = "X1"
            if "2" in scope_raw:
                sc_val = "X2"
            elif "3" in scope_raw:
                sc_val = "X3"
            elif "4" in scope_raw:
                sc_val = "X4"
            elif "6" in scope_raw:
                sc_val = "X6"
            elif "8" in scope_raw:
                sc_val = "X8"
            elif "15" in scope_raw:
                sc_val = "X15"
            if "kh" in scope_raw:
                sc_val = f"KH {sc_val}"

            vn_stance = str(stance)
            if "STAND" in vn_stance.upper():
                vn_stance = "ĐỨNG"
            elif "CROUCH" in vn_stance.upper():
                vn_stance = "NGỒI"
            elif "PRONE" in vn_stance.upper():
                vn_stance = "NẰM"

            parts = [str(gun_name).upper(), sc_val]
            if str(grip).upper() != "NONE":
                parts.append("TAY")
            if str(muzzle).upper() != "NONE":
                parts.append("NÒNG")
            parts.append(vn_stance)
            text = " | ".join(parts)
            color = "#00FF00"

        if ai_status == "ACTIVE":
            if not self.detect_timer.isActive():
                self.detect_timer.start()
            color = "#FFA500"
        else:
            if self.detect_timer.isActive():
                self.detect_timer.stop()
                self.last_color = None

        if self.last_full_text != text:
            self.lbl.setText(text)
            self.last_full_text = text
            self.show()
            self._adjust_to_content(text)

        if self.is_firing:
            if not self.flash_timer.isActive():
                self.flash_timer.start()
            if self.detect_timer.isActive():
                self.detect_timer.stop()
        else:
            if self.flash_timer.isActive():
                self.flash_timer.stop()
                self.last_color = None
            if not self.detect_timer.isActive() and self.last_color != color:
                self.lbl.setStyleSheet(self._label_qss_tpl.format(color=color))
                self.frame.setStyleSheet(self._frame_qss)
                self.last_color = color

class MacroWindow(QMainWindow):
    signal_settings_changed = pyqtSignal() # Signal to notify Backend/InputBridge of config changes
    WINDOW_WIDTH = 810

    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(self.WINDOW_WIDTH)
        icon_path = get_resource_path("di88vp.ico")
        self.setWindowIcon(QIcon(icon_path))
        
        # 3. Startup metadata
        w = win32api.GetSystemMetrics(0)
        h = win32api.GetSystemMetrics(1)
        self.detected_resolution = f"{w}x{h}"
        
        # 2. Logic Components (Connected via set_backend)
        self.backend = None
        self.keyboard_listener = None
        self.mouse_listener = None
        self._runtime_timers = []
        self._shutdown_in_progress = False
        self._last_macro_ui_signature = None
        self._last_macro_toggle_state = None
        self._last_stance_style_signature = None
        self._last_game_overlay_signature = None
        self._layout_sync_timer = QTimer(self)
        self._layout_sync_timer.setSingleShot(True)
        self._layout_sync_timer.timeout.connect(self.sync_window_height_to_content)
        
        # 3. Threads (PLACEHOLDER)
        
        # 4. Crosshair Overlay & Game HUD
        self.crosshair = CrosshairOverlay(self)
        
        self.game_overlay = GameOverlay(None)  # DETACH TO AVOID TASKBAR ISSUES

        # Temporary unsaved keybind values must exist before setup_ui_v2(),
        # because load_crosshair_settings() can trigger save_crosshair_settings()
        # through combo index change handlers during initial UI construction.
        self.temp_guitoggle_value = None
        self.temp_overlay_key_value = None
        self.temp_fast_loot_key_value = None
        self.temp_crosshair_toggle_key_value = None
        self.temp_aim_primary_key_value = None
        self.temp_aim_secondary_key_value = None
        self.temp_aim_trigger_key_value = None
        self.temp_aim_emergency_key_value = None

        # Keybind listener state must exist before setup_ui_v2(), because
        # child widgets install this window as an event filter while UI builds.
        self.listening_key = False
        self.target_key_btn = None
        self.target_setting_key = None
        self.temp_original_text = None
        
        # 5. UI Setup
        self.load_style()
        self.setup_ui_v2()
        
        # 6. Tray Manager (Step 6)
        self.tray_manager = TrayManager(self)
        self.tray_manager.show()
        
        self.dragPos = None
        self._crosshair_hidden_for_window = False
        
        # Enable keyboard events for arrow keys AND Keybinds
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        
        # Install Global Event Filter to catch clicks anywhere
        self.installEventFilter(self)
        

    def repolish(self, widget):
        """Forces Qt to re-read properties and apply QSS"""
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def style_setting_label(self, widget: QLabel):
        widget.setStyleSheet("""
            QLabel {
                color: #bcbcbc;
                background: transparent;
                border: none;
                padding: 0 6px;
                font-size: 11px;
                font-weight: bold;
            }
        """)

    def style_setting_button(self, widget: QPushButton):
        widget.setStyleSheet("""
            QPushButton {
                background-color: #1b1b1b;
                color: #d6d6d6;
                border: 1px solid #444;
                border-radius: 4px;
                font-size: 11px;
                padding: 0 8px;
            }
            QPushButton:hover {
                background-color: #1b1b1b;
                border: 1px solid #666;
            }
            QPushButton:disabled {
                background-color: #1b1b1b;
                color: #bfbfbf;
                border: 1px solid #444;
            }
        """)

    def style_capture_button(self, widget: QPushButton, active: bool):
        if active:
            widget.setStyleSheet("""
                QPushButton {
                    background-color: #8a56ff;
                    color: #ffffff;
                    border: 1px solid #b088ff;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background-color: #9766ff;
                    border: 1px solid #c3a5ff;
                }
            """)
        else:
            widget.setStyleSheet("""
                QPushButton {
                    background-color: #1b1b1b;
                    color: #d0d0d0;
                    border: 1px solid #444;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background-color: #202020;
                    border: 1px solid #666;
                }
            """)

    def style_switch_button(self, widget: QPushButton, active: bool):
        if active:
            widget.setStyleSheet("""
                QPushButton {
                    background-color: #12341b;
                    color: #9dffb7;
                    border: 1px solid #2e9b50;
                    border-radius: 8px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background-color: #174223;
                    border: 1px solid #41ba66;
                }
            """)
        else:
            widget.setStyleSheet("""
                QPushButton {
                    background-color: #242424;
                    color: #d0d0d0;
                    border: 1px solid #4a4a4a;
                    border-radius: 8px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background-color: #2c2c2c;
                    border: 1px solid #666666;
                }
            """)

    def style_scope_value_label(self, widget: QLabel):
        widget.setStyleSheet("""
            QLabel {
                background-color: #181818;
                color: #ffffff;
                border: 1px solid #3f3f3f;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 0 6px;
            }
        """)

    def style_scope_slider(self, widget: QSlider):
        widget.setStyleSheet("""
            QSlider::groove:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2a2a2a, stop:1 #242424);
                height: 6px;
                border-radius: 3px;
                border: 1px solid #2f2f2f;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8457ef, stop:0.5 #9164fb, stop:1 #a57aff);
                height: 6px;
                border-radius: 3px;
            }
            QSlider::add-page:horizontal {
                background: #2a2a2a;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: qradialgradient(cx:0.45, cy:0.35, radius:0.95, stop:0 #fffefe, stop:0.55 #f1e6ff, stop:1 #dcc4ff);
                border: 1px solid #d2b0ff;
                width: 13px;
                height: 13px;
                margin: -5px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: qradialgradient(cx:0.45, cy:0.35, radius:1.0, stop:0 #ffffff, stop:0.5 #f7efff, stop:1 #e7d4ff);
                border: 1px solid #e6d0ff;
                width: 14px;
                height: 14px;
                margin: -6px 0;
            }
            QSlider::handle:horizontal:pressed {
                background: qradialgradient(cx:0.5, cy:0.45, radius:0.95, stop:0 #f7efff, stop:0.55 #ead8ff, stop:1 #cea7ff);
                border: 1px solid #bc8fff;
                width: 12px;
                height: 12px;
                margin: -4px 0;
            }
            QSlider::sub-page:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8a5df7, stop:0.5 #9b70ff, stop:1 #b085ff);
            }
        """)

    def style_action_button(self, widget: QPushButton, primary: bool):
        if primary:
            widget.setStyleSheet("""
                QPushButton {
                    background-color: #232629;
                    color: white;
                    border: 1px solid #50555a;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 11px;
                    padding: 0 18px;
                    outline: none;
                }
                QPushButton:hover {
                    background-color: #363b40;
                    border: 1px solid #8a949e;
                    color: #ffffff;
                }
                QPushButton:focus {
                    outline: none;
                    border: 1px solid #8a949e;
                }
            """)
        else:
            widget.setStyleSheet("""
                QPushButton {
                    background-color: #232629;
                    color: white;
                    border: 1px solid #50555a;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 11px;
                    padding: 0 18px;
                    outline: none;
                }
                QPushButton:hover {
                    background-color: #31363b;
                    border: 1px solid #7b848d;
                    color: #ffffff;
                }
                QPushButton:focus {
                    outline: none;
                    border: 1px solid #7b848d;
                }
            """)

    def show_bottom_action_status(self, message: str, tone: str = "info", auto_hide_ms: int = 2200):
        if not hasattr(self, "bottom_action_status") or self.bottom_action_status is None:
            return
        palette = {
            "success": "#d8ffea",
            "error": "#ffd6d6",
            "info": "#d9e8ff",
        }
        fg = palette.get(tone, palette["info"])
        self.bottom_action_status.setText(f"! {message}")
        self.bottom_action_status.setStyleSheet(f"""
            QLabel {{
                color: {fg};
                background: transparent;
                border: none;
                font-size: 11px;
                font-weight: 800;
                padding: 2px 6px;
            }}
        """)
        self.bottom_action_status.show()
        self.bottom_action_status.raise_()
        if not hasattr(self, "_bottom_action_status_timer"):
            self._bottom_action_status_timer = QTimer(self)
            self._bottom_action_status_timer.setSingleShot(True)
            self._bottom_action_status_timer.timeout.connect(self.hide_bottom_action_status)
        self._bottom_action_status_timer.start(auto_hide_ms)

    def hide_bottom_action_status(self):
        if hasattr(self, "bottom_action_status") and self.bottom_action_status is not None:
            self.bottom_action_status.hide()

    def play_action_beep(self, action: str):
        try:
            if action == "save":
                winsound.Beep(1046, 80)
                winsound.Beep(1318, 90)
            elif action == "reset":
                winsound.Beep(880, 90)
                winsound.Beep(659, 130)
            else:
                winsound.MessageBeep()
        except Exception:
            QApplication.beep()

    def update_stance_status_style(self, stance_text: str, color: str = "#aaaaaa"):
        if not hasattr(self, 'lbl_stance') or self.lbl_stance is None:
            return
        signature = (stance_text, color)
        if self._last_stance_style_signature == signature:
            return
        self._last_stance_style_signature = signature
        self.lbl_stance.setText(stance_text)
        self.lbl_stance.setStyleSheet(f"""
            QLabel {{
                background-color: #1b1b1b;
                color: {color};
                font-size: 11px;
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 0 8px;
            }}
        """)
        self.update_home_snapshot()

    def update_aim_status_style(self, is_on: bool):
        if not hasattr(self, 'btn_aim_status') or self.btn_aim_status is None:
            return
        base = "font-size: 12px; font-weight: bold; letter-spacing: 2px; border-radius: 5px;"
        if is_on:
            self.btn_aim_status.setText("AIM : ON")
            self.btn_aim_status.setStyleSheet(
                f"QPushButton {{ color: #00FFFF; background: #1b1b1b; border: 1px solid #006666; {base} }}"
            )
        else:
            self.btn_aim_status.setText("AIM : OFF")
            self.btn_aim_status.setStyleSheet(
                f"QPushButton {{ color: #ff4444; background: #1b1b1b; border: 1px solid #441111; {base} }}"
            )
        self.update_home_snapshot()

    def update_aim_metric_style(self, widget: QLabel, text: str, color: str = "#d7d7d7"):
        if widget is None:
            return
        widget.setText(text)
        widget.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
                background: #1b1b1b;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 0 6px;
            }}
        """)

    def sync_crosshair_columns(self):
        if not hasattr(self, "crosshair_box"):
            return

        available = max(0, self.crosshair_box.contentsRect().width() - 16)
        gap_total = 3
        left_width = max(72, (available - gap_total) // 2)

        mapping = [
            ("lbl_cross_style", left_width),
            ("combo_style", left_width),
            ("lbl_cross_color", left_width),
            ("combo_color", left_width),
        ]
        for attr, width in mapping:
            widget = getattr(self, attr, None)
            if widget is None:
                continue
            widget.setMinimumWidth(0)
            widget.setMaximumWidth(width)
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def sync_window_height_to_content(self):
        if self.centralWidget() is None:
            return
        if self.centralWidget().layout():
            self.centralWidget().layout().activate()
        target_height = max(560, self.centralWidget().sizeHint().height() + 12)
        screen = self.screen()
        if screen is None:
            app = QApplication.instance()
            screen = app.primaryScreen() if app else None
        if screen is not None:
            available = screen.availableGeometry()
            target_height = min(target_height, max(560, available.height() - 24))
        if abs(self.height() - target_height) <= 2:
            return
        self.setFixedHeight(target_height)
        self.sync_window_width_to_frame()

    def fit_window_to_screen(self):
        self.sync_window_width_to_frame()
        self.sync_window_height_to_content()
        self.center_on_screen()

    def sync_window_width_to_frame(self):
        central = self.centralWidget()
        if central is None:
            return
        self.setFixedWidth(self.WINDOW_WIDTH)
        central.resize(self.width(), central.height())
        if hasattr(self, 'container') and self.container:
            self.container.setFixedWidth(max(0, self.width() - 10))
        self.sync_macro_box_heights()
        self.sync_crosshair_columns()

    def sync_macro_half_boxes(self):
        self.sync_crosshair_columns()

    def sync_macro_box_heights(self):
        pairs = [
            ("capture_box", "crosshair_box"),
        ]
        for left_attr, right_attr in pairs:
            left = getattr(self, left_attr, None)
            right = getattr(self, right_attr, None)
            if left is None or right is None:
                continue
            target = max(left.sizeHint().height(), right.sizeHint().height())
            left.setFixedHeight(target)
            right.setFixedHeight(target)

    def build_nav_button(self, text: str, page_name: str):
        button = QPushButton(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(42)
        button.clicked.connect(lambda: self.set_main_page(page_name))
        button.setProperty("page_name", page_name)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return button

    def update_nav_button_styles(self):
        buttons = getattr(self, "_nav_buttons", {})
        current = getattr(self, "_current_main_page", "home")
        for page_name, button in buttons.items():
            active = page_name == current
            accent = "#00d8ff" if active else "#343434"
            text_color = "#f2f2f2" if active else "#c6c6c6"
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: #141414;
                    color: {text_color};
                    border: 1px solid #2e2e2e;
                    border-left: 3px solid {accent};
                    border-radius: 10px;
                    font-size: 11px;
                    font-weight: 800;
                    letter-spacing: 1px;
                    padding: 0 14px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: #1b1b1b;
                    border: 1px solid #414141;
                    border-left: 3px solid #5be6ff;
                }}
            """)

    def set_main_page(self, page_name: str):
        if not hasattr(self, "page_stack") or self.page_stack is None:
            return
        page_map = getattr(self, "_page_widgets", {})
        target = page_map.get(page_name)
        if target is None:
            return
        self._current_main_page = page_name
        self.page_stack.setCurrentWidget(target)
        self.update_nav_button_styles()
        self.update_main_page_banner()
        self._layout_sync_timer.start(16)

    def update_main_page_banner(self):
        if not hasattr(self, "page_banner_title"):
            return
        current = getattr(self, "_current_main_page", "home")

        macro_on = False
        if hasattr(self, "btn_macro") and self.btn_macro:
            macro_on = "ON" in self.btn_macro.text().upper()
        aim_on = False
        if hasattr(self, "btn_aim_status") and self.btn_aim_status:
            aim_on = "ON" in self.btn_aim_status.text().upper()

        banner_map = {
            "home": {
                "eyebrow": "DI88 CONTROL",
                "title": "TRUNG TÂM ĐIỀU KHIỂN",
                "subtitle": "Macro & Aim By Di88",
                "badge": "TỔNG HỢP",
                "gradient_start": "#0d1e33",
                "gradient_end": "#112944",
                "hover_start": "#123053",
                "hover_end": "#16385f",
                "border": "#2f3942",
                "hover_border": "#476586",
                "eyebrow_color": "#77dfff",
                "badge_color": "#00d8ff",
                "badge_bg": "rgba(3, 22, 34, 0.36)",
                "badge_border": "#00d8ff",
                "badge_hover_bg": "rgba(0, 216, 255, 0.18)",
                "badge_hover_border": "#56e8ff",
                "badge_shadow": (0, 216, 255, 0),
            },
            "macro": {
                "eyebrow": "DI88 MACRO",
                "title": "TRUNG TÂM MACRO",
                "subtitle": "Nhận diện súng, ADS và điều khiển recoil",
                "badge": "• ĐANG BẬT" if macro_on else "• ĐANG TẮT",
                "gradient_start": "#251112",
                "gradient_end": "#34181a",
                "hover_start": "#341618",
                "hover_end": "#432022",
                "border": "#4a2a2d",
                "hover_border": "#6b3b40",
                "eyebrow_color": "#ff9c9c",
                "badge_color": "#ffecec" if macro_on else "#ffb0b0",
                "badge_bg": "rgba(255, 86, 86, 0.30)" if macro_on else "rgba(28, 8, 10, 0.35)",
                "badge_border": "#ff6a6a" if macro_on else "#b96a6a",
                "badge_hover_bg": "rgba(255, 106, 106, 0.40)" if macro_on else "rgba(70, 22, 24, 0.48)",
                "badge_hover_border": "#ff8b8b" if macro_on else "#d68b8b",
                "badge_shadow": (255, 90, 90, 120) if macro_on else (0, 0, 0, 0),
            },
            "aim": {
                "eyebrow": "DI88 AIM",
                "title": "TRUNG TÂM AIM",
                "subtitle": "Theo dõi mục tiêu và điều khiển ngắm",
                "badge": "• ĐANG BẬT" if aim_on else "• ĐANG TẮT",
                "gradient_start": "#0d2417",
                "gradient_end": "#143121",
                "hover_start": "#12311f",
                "hover_end": "#19402a",
                "border": "#294536",
                "hover_border": "#3e6c54",
                "eyebrow_color": "#74ffc8",
                "badge_color": "#effff8" if aim_on else "#a6d7bf",
                "badge_bg": "rgba(0, 255, 170, 0.24)" if aim_on else "rgba(7, 22, 14, 0.35)",
                "badge_border": "#52ffd1" if aim_on else "#5b9077",
                "badge_hover_bg": "rgba(0, 255, 170, 0.34)" if aim_on else "rgba(18, 46, 31, 0.50)",
                "badge_hover_border": "#8affdf" if aim_on else "#79af96",
                "badge_shadow": (0, 255, 170, 110) if aim_on else (0, 0, 0, 0),
            },
        }
        banner = banner_map.get(current, banner_map["home"])
        title = banner["title"]
        subtitle = banner["subtitle"]
        badge = banner["badge"]
        self.page_banner_title.setText(title)
        self.page_banner_subtitle.setText(subtitle)
        self.page_banner_badge.setText(badge)
        self.page_banner_eyebrow.setText(banner["eyebrow"])
        self.page_banner_eyebrow.setStyleSheet(f"""
            QLabel {{
                color: {banner["eyebrow_color"]};
                font-size: 10px;
                font-weight: 900;
                letter-spacing: 1px;
                background: transparent;
                border: none;
            }}
        """)
        self.page_banner.setStyleSheet(f"""
            QFrame#MainPageBanner {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {banner["gradient_start"]},
                    stop: 1 {banner["gradient_end"]}
                );
                border: 1px solid {banner["border"]};
                border-radius: 14px;
            }}
            QFrame#MainPageBanner:hover {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {banner["hover_start"]},
                    stop: 1 {banner["hover_end"]}
                );
                border: 1px solid {banner["hover_border"]};
            }}
        """)
        self.page_banner_badge.setStyleSheet(f"""
            QLabel {{
                color: {banner["badge_color"]};
                border: 1px solid {banner["badge_border"]};
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 10px;
                font-weight: 900;
                background: {banner["badge_bg"]};
                letter-spacing: 1px;
            }}
            QLabel:hover {{
                background: {banner["badge_hover_bg"]};
                border: 1px solid {banner["badge_hover_border"]};
            }}
        """)
        badge_shadow = getattr(self, "_page_banner_badge_shadow", None)
        if badge_shadow is None:
            badge_shadow = QGraphicsDropShadowEffect(self.page_banner_badge)
            badge_shadow.setBlurRadius(22)
            badge_shadow.setOffset(0, 0)
            self.page_banner_badge.setGraphicsEffect(badge_shadow)
            self._page_banner_badge_shadow = badge_shadow
        shadow_r, shadow_g, shadow_b, shadow_a = banner["badge_shadow"]
        badge_shadow.setColor(QColor(shadow_r, shadow_g, shadow_b, shadow_a))

    def _update_home_toggle_button_style(self, button, is_on: bool, accent_color: str):
        if button is None:
            return
        if is_on:
            button.setText("ON")
            button.setStyleSheet(
                f"""
                QPushButton {{
                    color: {accent_color};
                    background: rgba(10, 28, 20, 0.95);
                    border: 1px solid {accent_color};
                    border-radius: 8px;
                    font-size: 10px;
                    font-weight: 900;
                    padding: 0 8px;
                }}
                QPushButton:hover {{
                    background: rgba(14, 34, 25, 0.98);
                }}
                """
            )
        else:
            button.setText("OFF")
            button.setStyleSheet(
                """
                QPushButton {
                    color: #ff7b7b;
                    background: #1a1111;
                    border: 1px solid #5a2525;
                    border-radius: 8px;
                    font-size: 10px;
                    font-weight: 900;
                    padding: 0 8px;
                }
                QPushButton:hover {
                    border-color: #7a3434;
                }
                """
            )

    def _update_home_metric_badge(self, badge_label, is_on: bool, on_color: str):
        if badge_label is None:
            return
        if is_on:
            # Đã làm sạch chú thích lỗi mã hóa.
            badge_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {on_color};
                    font-size: 10px;
                    font-weight: 900;
                    background: transparent;
                    border: none;
                }}
                """
            )
        else:
            # Đã làm sạch chú thích lỗi mã hóa.
            badge_label.setStyleSheet(
                """
                QLabel {
                    color: #ff7e7e;
                    font-size: 10px;
                    font-weight: 900;
                    background: transparent;
                    border: none;
                }
                """
            )

    def toggle_home_macro(self):
        if getattr(self, "backend", None) is None:
            return
        current_on = hasattr(self, "btn_macro") and self.btn_macro and "ON" in self.btn_macro.text().upper()
        next_on = not current_on
        try:
            self.backend.set_paused(not next_on)
            self.update_macro_style(next_on)
        except Exception:
            pass

    def toggle_home_aim(self):
        if getattr(self, "backend", None) is None:
            return
        try:
            if hasattr(self.backend, "toggle_aim_assist_direct"):
                self.backend.toggle_aim_assist_direct()
        except Exception:
            pass

    def update_home_snapshot(self):
        if not hasattr(self, "home_page"):
            return

        def _safe_float(raw_text: str) -> float:
            try:
                return float(str(raw_text).strip())
            except Exception:
                return 0.0

        macro_text = "OFF"
        if hasattr(self, "btn_macro") and self.btn_macro:
            macro_text = "ON" if "ON" in self.btn_macro.text().upper() else "OFF"
        aim_text = "OFF"
        if hasattr(self, "btn_aim_status") and self.btn_aim_status:
            aim_text = "ON" if "ON" in self.btn_aim_status.text().upper() else "OFF"

        fps_text = "0"
        if hasattr(self, "lbl_aim_fps") and self.lbl_aim_fps:
            fps_text = self.lbl_aim_fps.text().replace("FPS :", "").replace("FPS:", "").strip() or "0"
        if fps_text in ("--", "N/A"):
            fps_text = "0"
        inf_text = "0"
        if hasattr(self, "lbl_aim_inf") and self.lbl_aim_inf:
            inf_text = self.lbl_aim_inf.text().replace("INF :", "").replace("INF:", "").replace("MS", "").strip() or "0"
        if inf_text in ("--", "N/A"):
            inf_text = "0"
        runtime_active = (aim_text == "ON") and (_safe_float(fps_text) > 0.0)

        macro_color = "#00e0ff" if macro_text == "ON" else "#ff7070"
        aim_color = "#00ffaa" if aim_text == "ON" else "#ff7070"

        if hasattr(self, "home_metric_macro_value"):
            self.home_metric_macro_value.setText(macro_text)
            self.home_metric_macro_value.setStyleSheet(f"QLabel {{ color: {macro_color}; font-size: 14px; font-weight: 900; background: transparent; border: none; }}")
        if hasattr(self, "home_metric_macro_value_hint"):
            # Đã làm sạch chú thích lỗi mã hóa.
            self.home_metric_macro_value_hint.setVisible(macro_text == "ON")
        if hasattr(self, "home_metric_aim_value"):
            self.home_metric_aim_value.setText(aim_text)
            self.home_metric_aim_value.setStyleSheet(f"QLabel {{ color: {aim_color}; font-size: 14px; font-weight: 900; background: transparent; border: none; }}")
        if hasattr(self, "home_metric_aim_value_hint"):
            # Đã làm sạch chú thích lỗi mã hóa.
            self.home_metric_aim_value_hint.setVisible(aim_text == "ON")
        if hasattr(self, "home_metric_fps_value"):
            self.home_metric_fps_value.setText(fps_text)
        if hasattr(self, "home_metric_inf_value"):
            self.home_metric_inf_value.setText(inf_text)
        if hasattr(self, "home_metric_fps_badge"):
            self._update_home_metric_badge(self.home_metric_fps_badge, runtime_active, "#8dffb1")
        if hasattr(self, "home_metric_inf_badge"):
            self._update_home_metric_badge(self.home_metric_inf_badge, runtime_active, "#ffcf5a")

        if hasattr(self, "home_macro_status_value"):
            self.home_macro_status_value.setText(macro_text)
            self.home_macro_status_value.setStyleSheet(f"QLabel {{ color: {macro_color}; font-size: 12px; font-weight: 800; background: transparent; border: none; }}")
        if hasattr(self, "home_aim_status_value"):
            self.home_aim_status_value.setText(aim_text)
            self.home_aim_status_value.setStyleSheet(f"QLabel {{ color: {aim_color}; font-size: 12px; font-weight: 800; background: transparent; border: none; }}")

        if hasattr(self, "home_macro_toggle_btn"):
            self._update_home_toggle_button_style(self.home_macro_toggle_btn, macro_text == "ON", "#66ffc2")
        if hasattr(self, "home_aim_toggle_btn"):
            self._update_home_toggle_button_style(self.home_aim_toggle_btn, aim_text == "ON", "#73f0ff")

        stance_text = "ĐỨNG"
        if hasattr(self, "lbl_stance") and self.lbl_stance:
            stance_text = self.lbl_stance.text().split(":")[-1].strip() or stance_text
        ads_text = "HOLD"
        if hasattr(self, "lbl_ads_status") and self.lbl_ads_status:
            ads_text = self.lbl_ads_status.text().split(":")[-1].strip() or ads_text
        capture_text = getattr(self, "current_capture_mode", "DXGI")
        model_text = "N/A"
        if hasattr(self, "combo_aim_model") and self.combo_aim_model and self.combo_aim_model.count():
            model_text = self.combo_aim_model.currentText().strip() or model_text
        aim_capture_text = getattr(self, "current_aim_capture_mode", "DirectX")
        backend_text = "Chưa nạp"
        runtime_source = ""
        if hasattr(self, "last_data") and isinstance(self.last_data, dict):
            aim_runtime_state = self.last_data.get("aim", {})
            runtime_backend = str(aim_runtime_state.get("inference_backend", "") or "").strip()
            runtime_source = str(aim_runtime_state.get("runtime_source", "") or "").strip()
            if runtime_backend and runtime_backend.lower() not in {"not loaded", "booting", "idle"}:
                backend_text = self._format_home_aim_backend_text(runtime_backend, runtime_source)
        elif hasattr(self, "lbl_aim_backend_info") and self.lbl_aim_backend_info:
            backend_text = self.lbl_aim_backend_info.text().replace("Backend:", "").strip() or backend_text

        for attr_name, text in (
            ("home_macro_stance_value", stance_text),
            ("home_macro_ads_value", ads_text),
            ("home_macro_capture_value", capture_text),
            ("home_aim_model_value", model_text),
            ("home_aim_backend_value", backend_text),
            ("home_aim_capture_value", aim_capture_text),
        ):
            label = getattr(self, attr_name, None)
            if label is not None:
                label.setText(text)

        self.update_main_page_banner()

    def list_aim_models(self):
        model_dir = Path(__file__).resolve().parents[1] / "bin" / "models"
        if not model_dir.exists():
            return []
        return sorted([p.name for p in model_dir.glob("*.onnx") if p.is_file()])

    def _format_aim_runtime_source_text(self, runtime_source: str) -> str:
        text = str(runtime_source or "").strip()
        normalized = text.lower()
        if "error" in normalized or "lỗi" in normalized:
            return "Runtime: Native DLL lỗi"
        if "not ready" in normalized or "chưa" in normalized:
            return "Runtime: Native DLL chờ"
        if "native" in normalized:
            return "Runtime: Native DLL"
        return "Runtime: Chưa nạp"

    def _normalize_aim_backend_text(self, backend_text: str) -> str:
        text = str(backend_text or "").strip() or "Chưa nạp"
        if text.lower() in {"not loaded", "booting", "idle"}:
            return "Chưa nạp"
        for prefix in ("Native DLL /", "Native "):
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()
                break
        if text.lower() in {"not ready", "none", "n/a"}:
            return "Chưa nạp"
        return text.upper() if text != "Chưa nạp" else text

    def _format_aim_backend_meta_text(self, backend_text: str, runtime_source: str = "") -> str:
        return f"Backend: {self._normalize_aim_backend_text(backend_text)}"

    def _format_home_aim_backend_text(self, backend_text: str, runtime_source: str = "") -> str:
        runtime = self._format_aim_runtime_source_text(runtime_source).replace("Runtime:", "").strip()
        backend = self._normalize_aim_backend_text(backend_text)
        if runtime and runtime != "Chưa nạp":
            return f"{runtime} / {backend}"
        return backend

    def set_aim_model_status(self, text: str, color: str = "#cfcfcf"):
        normalized = {
            "Không có model": "\u004b\u0068\u00f4\u006e\u0067 \u0063\u00f3 \u006d\u006f\u0064\u0065\u006c",
            # Đã làm sạch chú thích lỗi mã hóa.
            # Đã làm sạch chú thích lỗi mã hóa.
        }.get(text, text)
        if normalized == "\u0110\u00e3 \u0074\u1ea3\u0069":
            normalized = "\u0110\u00e3 \u004e\u1ea1\u0070"
        if hasattr(self, "lbl_aim_model_status") and self.lbl_aim_model_status:
            self.lbl_aim_model_status.setText(normalized)
            self.lbl_aim_model_title.setStyleSheet("""
                QLabel {
                    color: #cfcfcf;
                    font-size: 11px;
                    font-weight: 700;
                    background: transparent;
                }
            """)
            self.lbl_aim_model_sep.setStyleSheet("""
                QLabel {
                    color: #cfcfcf;
                    font-size: 11px;
                    font-weight: 700;
                    background: transparent;
                }
            """)
            self.lbl_aim_model_status.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-size: 11px;
                    font-weight: 700;
                    background: transparent;
                }}
            """)
        if hasattr(self, "lbl_aim_model_status_meta") and self.lbl_aim_model_status_meta:
            runtime_source = ""
            if hasattr(self, "last_data") and isinstance(self.last_data, dict):
                runtime_source = str(self.last_data.get("aim", {}).get("runtime_source", "") or "")
            self.lbl_aim_model_status_meta.setText(self._format_aim_runtime_source_text(runtime_source))
            self.lbl_aim_model_status_meta.setStyleSheet(f"""
                QLabel {{
                    color: #cfcfcf;
                    font-size: 10px;
                    font-weight: 700;
                    background: #1b1b1b;
                    border: 1px solid #3a3a3a;
                    border-radius: 5px;
                    padding: 2px 6px;
                }}
            """)
        if hasattr(self, "lbl_aim_runtime_meta") and self.lbl_aim_runtime_meta:
            backend_text = "Chưa nạp"
            runtime_source = ""
            if hasattr(self, "last_data") and isinstance(self.last_data, dict):
                runtime_source = str(self.last_data.get("aim", {}).get("runtime_source", "") or "")
            if hasattr(self, "lbl_aim_backend_info") and self.lbl_aim_backend_info:
                backend_text = self.lbl_aim_backend_info.text().replace("Backend:", "").strip() or backend_text
            self.lbl_aim_runtime_meta.setText(self._format_aim_backend_meta_text(backend_text, runtime_source))
        self.update_home_snapshot()

    def position_aim_model_notice(self):
        if not hasattr(self, "aim_model_notice") or self.aim_model_notice is None:
            return
        if not hasattr(self, "container") or self.container is None:
            return
        if not hasattr(self, "aim_workspace") or self.aim_workspace is None:
            return
        self.aim_model_notice.adjustSize()
        workspace_pos = self.aim_workspace.mapTo(self.container, QPoint(0, 0))
        workspace_width = self.aim_workspace.width()
        x = workspace_pos.x() + max(12, workspace_width - self.aim_model_notice.width() - 14)
        y = workspace_pos.y() + 18
        self.aim_model_notice.move(x, y)
        self.aim_model_notice.raise_()

    def show_aim_model_notice(self, model_name: str, duration_ms: int = 3000, error: bool = False):
        if not hasattr(self, "aim_model_notice") or self.aim_model_notice is None:
            return
        model_name = (model_name or "").strip()
        if model_name == "Không có model":
            return
        if not model_name or model_name in ("Không có model", "Khong co model"):
            return
        fg = "#ffb3b3" if error else "#f4f4f4"
        border = "#7a3a3a" if error else "#545454"
        # Đã làm sạch chú thích lỗi mã hóa.
        self.aim_model_notice.setText(
            f"\u004c\u1ed7\u0069 \u006e\u1ea1\u0070 \u006d\u006f\u0064\u0065\u006c: {model_name}"
            if error
            else f"\u0110\u00e3 \u006e\u1ea1\u0070 \u006d\u006f\u0064\u0065\u006c: {model_name}"
        )
        self.aim_model_notice.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(16, 16, 16, 238);
                color: {fg};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: 700;
            }}
        """)
        self.aim_model_notice.setMinimumWidth(280)
        self.aim_model_notice.setMinimumHeight(44)
        self.aim_model_notice.show()
        self.aim_model_notice.raise_()
        if hasattr(self, "aim_model_notice_timer") and self.aim_model_notice_timer:
            self.aim_model_notice_timer.start(duration_ms)

    def on_aim_model_changed_safe(self, index: int):
        if index < 0 or not hasattr(self, "combo_aim_model"):
            return
        text = self.combo_aim_model.currentText().strip()
        if not text or text in (
            "Không có model",
            "Không có model",
            "\u004b\u0068\u00f4\u006e\u0067 \u0063\u00f3 \u006d\u006f\u0064\u0065\u006c",
        ):
            self.set_aim_model_status("\u004b\u0068\u00f4\u006e\u0067 \u0063\u00f3 \u006d\u006f\u0064\u0065\u006c", "#ff9c9c")
            return
        self.set_aim_model_status("\u0110\u00e3 \u0074\u1ea3\u0069", "#cfcfcf")

    def on_aim_display_toggle_changed(self, *_args):
        self.update_home_snapshot()
        if hasattr(self, "last_data"):
            self.update_aim_visual_overlay(self.last_data)
        self.signal_settings_changed.emit()

    def on_aim_advanced_toggle_changed(self, *_args):
        self.apply_aim_window_flags()
        if hasattr(self, "last_data"):
            self.update_aim_visual_overlay(self.last_data)
        self.signal_settings_changed.emit()

    def on_aim_advanced_dropdown_changed(self, *_args):
        if hasattr(self, "last_data"):
            self.update_aim_visual_overlay(self.last_data)
        self.signal_settings_changed.emit()

    def apply_aim_window_flags(self):
        toggles = getattr(self, "aim_toggle_controls", {})
        ui_topmost = bool(toggles.get("UI TopMost").isChecked()) if toggles.get("UI TopMost") is not None else False
        stream_guard = bool(toggles.get("StreamGuard").isChecked()) if toggles.get("StreamGuard") is not None else False

        try:
            flags = self.windowFlags()
            if ui_topmost:
                flags |= Qt.WindowType.WindowStaysOnTopHint
            else:
                flags &= ~Qt.WindowType.WindowStaysOnTopHint
            was_visible = self.isVisible()
            was_hidden = self.isHidden()
            self.setWindowFlags(flags)
            if was_visible and not was_hidden:
                self.show()
        except Exception:
            pass

        for widget in (self, getattr(self, "game_overlay", None), getattr(self, "crosshair", None)):
            try:
                if widget is None:
                    continue
                hwnd = int(widget.winId())
                # WDA_EXCLUDEFROMCAPTURE on Windows 10 2004+, fallback uses WDA_MONITOR.
                affinity = 0x11 if stream_guard else 0x00
                if not ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, affinity) and stream_guard:
                    ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x01)
            except Exception:
                pass

    def load_aim_toggle_controls(self, aim_toggles: dict):
        for key, checkbox in getattr(self, "aim_toggle_controls", {}).items():
            if checkbox is None:
                continue
            checkbox.blockSignals(True)
            checkbox.setChecked(bool(aim_toggles.get(key, checkbox.isChecked())))
            checkbox.blockSignals(False)
        self.apply_aim_window_flags()

    def save_aim_toggle_controls(self, aim_toggles: dict):
        for key, checkbox in getattr(self, "aim_toggle_controls", {}).items():
            if checkbox is not None:
                aim_toggles[key] = bool(checkbox.isChecked())

    def load_aim_dropdown_controls(self, aim_dropdowns: dict):
        for key, control in getattr(self, "aim_dropdown_controls", {}).items():
            combo = control.get("combo")
            spec = control.get("spec", {})
            if combo is None:
                continue
            value = str(aim_dropdowns.get(key, spec.get("default", "")))
            if combo.findText(value) < 0:
                value = str(spec.get("default", ""))
            combo.blockSignals(True)
            combo.setCurrentText(value)
            combo.blockSignals(False)

    def save_aim_dropdown_controls(self, aim_dropdowns: dict):
        for key, control in getattr(self, "aim_dropdown_controls", {}).items():
            combo = control.get("combo")
            if combo is not None:
                aim_dropdowns[key] = combo.currentText().strip()

    def _normalize_argb_hex(self, value: str, fallback: str = "#FFFFFFFF") -> str:
        text = str(value or "").strip()
        if text.startswith("#") and len(text) == 9:
            return text.upper()
        color = QColor(text)
        if not color.isValid():
            return fallback.upper()
        return f"#{color.alpha():02X}{color.red():02X}{color.green():02X}{color.blue():02X}"

    def _qcolor_from_argb_hex(self, value: str, fallback: str = "#FFFFFFFF") -> QColor:
        text = self._normalize_argb_hex(value, fallback)
        return QColor(int(text[3:5], 16), int(text[5:7], 16), int(text[7:9], 16), int(text[1:3], 16))

    def set_aim_color_button(self, key: str, value: str):
        button = getattr(self, "aim_color_controls", {}).get(key)
        if button is None:
            return
        normalized = self._normalize_argb_hex(value)
        button.setProperty("color_value", normalized)
        color = self._qcolor_from_argb_hex(normalized)
        button.setText(normalized)
        button.setStyleSheet(
            f"""
            QPushButton {{
                color: #f2f2f2;
                background: rgba({color.red()}, {color.green()}, {color.blue()}, 150);
                border: 1px solid rgba({color.red()}, {color.green()}, {color.blue()}, 230);
                border-radius: 6px;
                font-size: 10px;
                font-weight: 800;
            }}
            QPushButton:hover {{
                border: 1px solid #ffffff;
            }}
            """
        )

    def choose_aim_color(self, key: str):
        button = getattr(self, "aim_color_controls", {}).get(key)
        current_value = button.property("color_value") if button is not None else "#FFFFFFFF"
        initial = self._qcolor_from_argb_hex(str(current_value or "#FFFFFFFF"))
        chosen = QColorDialog.getColor(initial, self, f"Chọn {key}", QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if not chosen.isValid():
            return
        value = f"#{chosen.alpha():02X}{chosen.red():02X}{chosen.green():02X}{chosen.blue():02X}"
        self.set_aim_color_button(key, value)
        if hasattr(self, "last_data"):
            self.update_aim_visual_overlay(self.last_data)
        self.signal_settings_changed.emit()

    def load_aim_color_controls(self, aim_colors: dict):
        defaults = {
            "FOV Color": "#FF8080FF",
            "Detected Player Color": "#FF00FFFF",
            "Theme Color": "#FF722ED1",
        }
        for key, button in getattr(self, "aim_color_controls", {}).items():
            self.set_aim_color_button(key, str(aim_colors.get(key, defaults.get(key, "#FFFFFFFF"))))

    def save_aim_color_controls(self, aim_colors: dict):
        for key, button in getattr(self, "aim_color_controls", {}).items():
            if button is not None:
                aim_colors[key] = self._normalize_argb_hex(str(button.property("color_value") or "#FFFFFFFF"))

    def choose_aim_file_location(self, key: str):
        button = getattr(self, "aim_file_controls", {}).get(key)
        current = str(button.property("file_value") or "") if button is not None else ""
        start_dir = str(Path(current).parent) if current else str(Path.home())
        file_path, _ = QFileDialog.getOpenFileName(self, f"Chọn {key}", start_dir, "DLL Files (*.dll);;All Files (*.*)")
        if not file_path:
            return
        self.set_aim_file_button(key, file_path)
        self.signal_settings_changed.emit()

    def set_aim_file_button(self, key: str, value: str):
        button = getattr(self, "aim_file_controls", {}).get(key)
        if button is None:
            return
        text = str(value or "").strip()
        button.setProperty("file_value", text)
        button.setText(Path(text).name if text else "Chọn DLL")

    def load_aim_file_controls(self, aim_file_locations: dict):
        for key, button in getattr(self, "aim_file_controls", {}).items():
            self.set_aim_file_button(key, str(aim_file_locations.get(key, "")))

    def save_aim_file_controls(self, aim_file_locations: dict):
        for key, button in getattr(self, "aim_file_controls", {}).items():
            if button is not None:
                aim_file_locations[key] = str(button.property("file_value") or "")

    def load_aim_minimize_controls(self, aim_minimize: dict):
        for key, checkbox in getattr(self, "aim_minimize_controls", {}).items():
            if checkbox is None:
                continue
            checkbox.blockSignals(True)
            checkbox.setChecked(bool(aim_minimize.get(key, False)))
            checkbox.blockSignals(False)

    def save_aim_minimize_controls(self, aim_minimize: dict):
        for key, checkbox in getattr(self, "aim_minimize_controls", {}).items():
            if checkbox is not None:
                aim_minimize[key] = bool(checkbox.isChecked())

    def refresh_aim_model_list(self, selected_model: str | None = None):
        if not hasattr(self, "combo_aim_model") or self.combo_aim_model is None:
            return

        models = self.list_aim_models()
        self.combo_aim_model.blockSignals(True)
        self.combo_aim_model.clear()

        if not models:
            self.combo_aim_model.addItem("Không có model")
            self.combo_aim_model.setEnabled(False)
            self.set_aim_model_status("Không có model", "#ff9c9c")
            self.combo_aim_model.blockSignals(False)
            return

        self.combo_aim_model.setEnabled(True)
        self.combo_aim_model.addItems(models)

        target_model = selected_model if selected_model in models else models[0]
        self.combo_aim_model.setCurrentText(target_model)
        self.combo_aim_model.blockSignals(False)
        self.set_aim_model_status("Đã tải", "#74ffc8")

    def on_aim_model_changed(self, index: int):
        if index < 0 or not hasattr(self, "combo_aim_model"):
            return
        text = self.combo_aim_model.currentText().strip()
        if not text or text == "Không có model":
            self.set_aim_model_status("Không có model", "#ff9c9c")
        else:
            self.set_aim_model_status("Đã tải", "#74ffc8")

    def on_aim_model_changed(self, index: int):
        if index < 0 or not hasattr(self, "combo_aim_model"):
            return
        text = self.combo_aim_model.currentText().strip()
        if not text or text in ("Không có model", "Khong co model"):
            self.set_aim_model_status("Không có model", "#ff9c9c")
        else:
            self.set_aim_model_status("Đã tải", "#74ffc8")
            self.show_aim_model_notice(text)

    def update_scope_intensity_label(self, scope_key: str, value: int):
        label = getattr(self, "scope_value_labels", {}).get(scope_key)
        if label is not None:
            label.setText(f"{value}%")

    def update_aim_fov_label(self, value: int):
        if hasattr(self, "aim_fov_value_label") and self.aim_fov_value_label:
            self.aim_fov_value_label.setText(str(int(value)))

    def update_aim_confidence_label(self, value: int):
        if hasattr(self, "aim_confidence_value_label") and self.aim_confidence_value_label:
            self.aim_confidence_value_label.setText(f"{int(value)}%")

    def update_aim_trigger_delay_label(self, value: int):
        if hasattr(self, "aim_trigger_delay_value_label") and self.aim_trigger_delay_value_label:
            self.aim_trigger_delay_value_label.setText(f"{int(value)} ms")

    def update_aim_capture_fps_label(self, value: int):
        if hasattr(self, "aim_capture_fps_value_label") and self.aim_capture_fps_value_label:
            self.aim_capture_fps_value_label.setText(str(int(value)))

    def update_aim_jitter_label(self, value: int):
        if hasattr(self, "aim_jitter_value_label") and self.aim_jitter_value_label:
            self.aim_jitter_value_label.setText(str(int(value)))

    def update_aim_sensitivity_label(self, value: int):
        if hasattr(self, "aim_sensitivity_value_label") and self.aim_sensitivity_value_label:
            self.aim_sensitivity_value_label.setText(f"{float(value) / 100.0:.2f}")

    def update_aim_ema_label(self, value: int):
        if hasattr(self, "aim_ema_value_label") and self.aim_ema_value_label:
            self.aim_ema_value_label.setText(f"{float(value) / 100.0:.2f}")

    def update_aim_sticky_threshold_label(self, value: int):
        if hasattr(self, "aim_sticky_threshold_value_label") and self.aim_sticky_threshold_value_label:
            self.aim_sticky_threshold_value_label.setText(str(int(value)))

    def update_aim_dynamic_fov_label(self, value: int):
        if hasattr(self, "aim_dynamic_fov_value_label") and self.aim_dynamic_fov_value_label:
            self.aim_dynamic_fov_value_label.setText(str(int(value)))

    def update_aim_listing_slider_label(self, key: str, slider_value: int):
        control = getattr(self, "aim_listing_controls", {}).get(key)
        if not control:
            return
        actual_value = self.aim_test_slider_to_value(control["spec"], slider_value)
        control["value_label"].setText(self.format_aim_test_value(control["spec"], actual_value))

    def load_aim_listing_sliders(self, aim_sliders: dict):
        for key, control in getattr(self, "aim_listing_controls", {}).items():
            spec = control.get("spec", {})
            slider = control.get("slider")
            if slider is None:
                continue
            actual_value = aim_sliders.get(key, spec.get("default", 0))
            slider_value = self.aim_test_value_to_slider(spec, actual_value)
            slider_value = max(int(spec.get("min", slider.minimum())), min(int(spec.get("max", slider.maximum())), slider_value))
            slider.setValue(slider_value)
            self.update_aim_listing_slider_label(key, slider_value)

    def save_aim_listing_sliders(self, aim_sliders: dict):
        for key, control in getattr(self, "aim_listing_controls", {}).items():
            slider = control.get("slider")
            if slider is None:
                continue
            aim_sliders[key] = self.aim_test_slider_to_value(control["spec"], slider.value())

    def update_aim_primary_position_label(self, value: int):
        if hasattr(self, "aim_primary_position_value_label") and self.aim_primary_position_value_label:
            self.aim_primary_position_value_label.setText(str(int(value)))

    def update_aim_secondary_position_label(self, value: int):
        if hasattr(self, "aim_secondary_position_value_label") and self.aim_secondary_position_value_label:
            self.aim_secondary_position_value_label.setText(str(int(value)))

    def build_aim_test_slider_specs(self):
        return [
            {"key": "Dynamic FOV Size", "label": "FOV Động", "min": 10, "max": 640, "step": 1, "scale": 1, "default": 200, "format": "int"},
            {"key": "Mouse Sensitivity (+/-)", "label": "Độ Nhạy Chuột", "min": 1, "max": 100, "step": 1, "scale": 100, "default": 0.80, "format": "float2"},
            # Đã làm sạch chú thích lỗi mã hóa.
            # Đã làm sạch chú thích lỗi mã hóa.
            # Đã làm sạch chú thích lỗi mã hóa.
            # Đã làm sạch chú thích lỗi mã hóa.
            # Đã làm sạch chú thích lỗi mã hóa.
            {"key": "EMA Smoothening", "label": "EMA Smooth", "min": 1, "max": 100, "step": 1, "scale": 100, "default": 0.5, "format": "float2"},
            {"key": "Kalman Lead Time", "label": "Kalman Lead", "min": 2, "max": 30, "step": 1, "scale": 100, "default": 0.10, "format": "float2"},
            {"key": "WiseTheFox Lead Time", "label": "Wise Lead", "min": 2, "max": 30, "step": 1, "scale": 100, "default": 0.15, "format": "float2"},
            {"key": "Shalloe Lead Multiplier", "label": "Shalloe Lead", "min": 2, "max": 20, "step": 1, "scale": 2, "default": 3.0, "format": "float1"},
            {"key": "AI Confidence Font Size", "label": "Font Detect", "min": 1, "max": 30, "step": 1, "scale": 1, "default": 20, "format": "int"},
            {"key": "Corner Radius", "label": "Bo Góc", "min": 0, "max": 100, "step": 1, "scale": 1, "default": 0, "format": "int"},
            {"key": "Border Thickness", "label": "Độ Dày Viền", "min": 1, "max": 100, "step": 1, "scale": 10, "default": 1.0, "format": "float1"},
            {"key": "Opacity", "label": "Độ Trong", "min": 0, "max": 10, "step": 1, "scale": 10, "default": 1.0, "format": "float1"},
        ]

    def aim_test_slider_to_value(self, spec: dict, slider_value: int):
        scale = spec.get("scale", 1)
        if scale == 1:
            return int(slider_value)
        return float(slider_value) / float(scale)

    def aim_test_value_to_slider(self, spec: dict, actual_value):
        scale = spec.get("scale", 1)
        if scale == 1:
            return int(round(float(actual_value)))
        return int(round(float(actual_value) * float(scale)))

    def format_aim_test_value(self, spec: dict, actual_value) -> str:
        fmt = spec.get("format", "int")
        value = float(actual_value)
        if fmt == "percent":
            return f"{int(round(value))}%"
        if fmt == "float2":
            return f"{value:.2f}"
        if fmt == "float1":
            return f"{value:.1f}"
        return str(int(round(value)))

    def update_aim_test_slider_label(self, key: str, slider_value: int):
        control = getattr(self, "aim_test_controls", {}).get(key)
        if not control:
            return
        actual_value = self.aim_test_slider_to_value(control["spec"], slider_value)
        control["value_label"].setText(self.format_aim_test_value(control["spec"], actual_value))

    def update_aim_test_row_enabled(self, key: str, enabled: bool):
        control = getattr(self, "aim_test_controls", {}).get(key)
        if not control:
            return
        control["slider"].setEnabled(enabled)
        control["value_label"].setEnabled(enabled)

    def setup_hover_hints(self):
        self.hover_hint = QLabel(self.container)
        self.hover_hint.setObjectName("HoverHint")
        self.hover_hint.setWordWrap(True)
        self.hover_hint.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.hover_hint.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hover_hint.setStyleSheet("""
            QLabel#HoverHint {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(27, 31, 37, 248),
                    stop: 1 rgba(16, 19, 24, 248)
                );
                color: #f8fbff;
                border: 1px solid #576170;
                border-radius: 9px;
                padding: 8px 10px;
                font-size: 11px;
                font-weight: 600;
                line-height: 1.35em;
            }
        """)
        hover_shadow = QGraphicsDropShadowEffect(self.hover_hint)
        hover_shadow.setBlurRadius(22)
        hover_shadow.setOffset(0, 6)
        hover_shadow.setColor(QColor(0, 0, 0, 145))
        self.hover_hint.setGraphicsEffect(hover_shadow)
        self.hover_hint.hide()
        self._hover_hint_margin = QPoint(16, 18)
        self._hover_hint_anchor = None
        self._hover_hint_last_pos = None
        self._hover_hint_timer = QTimer(self)
        self._hover_hint_timer.setInterval(16)
        self._hover_hint_timer.timeout.connect(self._tick_hover_hint)

        self.hover_hint_targets = {}
        if hasattr(self, 'header_detection'):
            self._add_hover_widget(self.header_detection, "Thông tin vũ khí hiện tại.")
        if hasattr(self, 'header_settings'):
            self._add_hover_widget(self.header_settings, "Thiết lập các phím chức năng, chế độ chụp và các tùy chọn macro cơ bản.")
        if hasattr(self, 'header_crosshair'):
            self._add_hover_widget(self.header_crosshair, "Thiết lập tâm ngắm, kiểu hiển thị và màu hiển thị.")
        if hasattr(self, 'lbl_fastloot_row'):
            self._add_hover_widget(self.lbl_fastloot_row, "Tính năng nhặt đồ nhanh.")
        if hasattr(self, 'lbl_slide_row'):
            self._add_hover_widget(self.lbl_slide_row, "Giữ Shift + W + ( A hoặc D ) rồi bấm C để thực hiện thao tác lướt ngồi.")
        if hasattr(self, 'lbl_stopkeys_row'):
            self._add_hover_widget(self.lbl_stopkeys_row, "Danh sách phím dừng khẩn cấp.")
        if hasattr(self, 'lbl_adsmode_row'):
            self._add_hover_widget(self.lbl_adsmode_row, "Trạng thái chế độ ADS hiện tại.")
        if hasattr(self, 'lbl_guitoggle_row'):
            self._add_hover_widget(self.lbl_guitoggle_row, "Phím ẩn hoặc hiện cửa sổ app ngay lập tức.")
        if hasattr(self, 'lbl_overlay_row'):
            self._add_hover_widget(self.lbl_overlay_row, "Phím điều khiển lớp overlay hiển thị trong game.")
        if hasattr(self, 'lbl_capture_row'):
            self._add_hover_widget(self.lbl_capture_row, "Chọn backend chụp màn hình dùng cho detect và runtime.")

    def _add_hover_target(self, parent: QWidget, rect: QRect, text: str):
        anchor = QFrame(parent)
        anchor.setGeometry(rect)
        anchor.setStyleSheet("background: transparent; border: none;")
        anchor.setCursor(Qt.CursorShape.WhatsThisCursor)
        anchor.installEventFilter(self)
        self.hover_hint_targets[anchor] = (anchor, text)

    def _add_hover_widget(self, widget: QWidget, text: str):
        if widget is None:
            return
        widget.setCursor(Qt.CursorShape.WhatsThisCursor)
        widget.setMouseTracking(True)
        widget.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        widget.installEventFilter(self)
        self.hover_hint_targets[widget] = (widget, text)

    def show_hover_hint(self, anchor: QWidget, text: str):
        self._hover_hint_anchor = anchor
        self._hover_hint_last_pos = None
        self.hover_hint.setText(text)
        self.hover_hint.adjustSize()
        hint_width = min(max(self.hover_hint.sizeHint().width(), 220), 320)
        self.hover_hint.resize(hint_width, self.hover_hint.sizeHint().height() + 8)
        self.hover_hint.show()
        self.hover_hint.raise_()
        self._move_hover_hint(anchor)
        if not self._hover_hint_timer.isActive():
            self._hover_hint_timer.start()

    def _move_hover_hint(self, anchor: QWidget | None = None, local_pos: QPoint | None = None):
        if not hasattr(self, 'hover_hint') or not self.hover_hint or not self.hover_hint.isVisible():
            return
        if local_pos is not None:
            self._hover_hint_last_pos = QPoint(local_pos)
        if anchor is not None:
            if local_pos is None:
                local_pos = self._hover_hint_last_pos
            if local_pos is None:
                local_pos = anchor.mapFromGlobal(anchor.cursor().pos())
            mouse_pos = anchor.mapTo(self.container, local_pos)
        else:
            mouse_pos = self.container.mapFromGlobal(self.cursor().pos())
        x = mouse_pos.x() + self._hover_hint_margin.x()
        y = mouse_pos.y() + self._hover_hint_margin.y()
        max_x = self.container.width() - self.hover_hint.width() - 10
        max_y = self.container.height() - self.hover_hint.height() - 10
        x = max(10, min(x, max_x))
        y = max(36, min(y, max_y))
        self.hover_hint.move(x, y)

    def hide_hover_hint(self):
        if hasattr(self, 'hover_hint') and self.hover_hint:
            self.hover_hint.hide()
        self._hover_hint_anchor = None
        self._hover_hint_last_pos = None
        if hasattr(self, '_hover_hint_timer') and self._hover_hint_timer.isActive():
            self._hover_hint_timer.stop()

    def _tick_hover_hint(self):
        if not getattr(self, '_hover_hint_anchor', None):
            return
        self._move_hover_hint(self._hover_hint_anchor)

    def load_style(self):
        """Loads the external QSS stylesheet"""
        try:
            style_candidates = [
                get_resource_path("style.qss"),
                get_resource_path("GUI/style.qss"),
            ]
            style_path = next((path for path in style_candidates if os.path.exists(path)), None)
            if style_path:
                with open(style_path, "r", encoding="utf-8") as f:
                    qss = f.read()
                arrow_candidates = [
                    get_resource_path("assets/combo-arrow.svg"),
                    get_resource_path("GUI/assets/combo-arrow.svg"),
                ]
                combo_arrow_path = next((path for path in arrow_candidates if os.path.exists(path)), None)
                if combo_arrow_path:
                    combo_arrow = Path(combo_arrow_path).resolve().as_posix()
                    qss = qss.replace("__COMBO_ARROW__", f"\"{combo_arrow}\"")
                else:
                    qss = qss.replace("image: url(__COMBO_ARROW__);", "")
                self.setStyleSheet(qss)
                return
            if APP_STYLE_QSS:
                self.setStyleSheet(APP_STYLE_QSS)
        except Exception as e:
            print(f"[WARN] Could not load style.qss: {e}")
            if APP_STYLE_QSS:
                self.setStyleSheet(APP_STYLE_QSS)

    def build_crosshair_preview_icon(self, style_name: str) -> QIcon:
        pixmap = QPixmap(28, 14)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(QColor("#f2f2f2"))
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        cx, cy = 14, 7

        def gap_cross():
            gap = 2
            arm = 4
            painter.drawLine(cx - gap - arm, cy, cx - gap, cy)
            painter.drawLine(cx + gap, cy, cx + gap + arm, cy)
            painter.drawLine(cx, cy - gap - arm, cx, cy - gap)
            painter.drawLine(cx, cy + gap, cx, cy + gap + arm)

        if "Gap Cross" in style_name:
            gap_cross()
        elif "T-Shape" in style_name:
            gap = 2
            arm = 4
            painter.drawLine(cx - gap - arm, cy, cx - gap, cy)
            painter.drawLine(cx + gap, cy, cx + gap + arm, cy)
            painter.drawLine(cx, cy + gap, cx, cy + gap + arm)
        elif "Circle Dot" in style_name:
            painter.drawEllipse(QPoint(cx, cy), 4, 4)
            painter.setBrush(QBrush(QColor("#f2f2f2")))
            painter.drawEllipse(QPoint(cx, cy), 1, 1)
        elif "Classic" in style_name:
            painter.drawLine(cx - 5, cy, cx + 5, cy)
            painter.drawLine(cx, cy - 5, cx, cy + 5)
        elif "Micro Dot" in style_name or "Square Dot" in style_name:
            painter.setBrush(QBrush(QColor("#f2f2f2")))
            painter.drawEllipse(QPoint(cx, cy), 2, 2)
        elif "Hollow Box" in style_name:
            painter.drawRect(cx - 4, cy - 4, 8, 8)
        elif "Cross + Dot" in style_name or "Plus Dot" in style_name:
            painter.drawLine(cx - 5, cy, cx + 5, cy)
            painter.drawLine(cx, cy - 5, cx, cy + 5)
            painter.setBrush(QBrush(QColor("#f2f2f2")))
            painter.drawEllipse(QPoint(cx, cy), 1, 1)
        elif "Chevron" in style_name or "V-Shape" in style_name:
            painter.drawLine(cx - 5, cy + 3, cx, cy - 1)
            painter.drawLine(cx + 5, cy + 3, cx, cy - 1)
        elif "X-Shape" in style_name:
            painter.drawLine(cx - 4, cy - 4, cx + 4, cy + 4)
            painter.drawLine(cx - 4, cy + 4, cx + 4, cy - 4)
        elif "Diamond" in style_name:
            painter.drawLine(cx, cy - 4, cx + 4, cy)
            painter.drawLine(cx + 4, cy, cx, cy + 4)
            painter.drawLine(cx, cy + 4, cx - 4, cy)
            painter.drawLine(cx - 4, cy, cx, cy - 4)
        elif "Triangle" in style_name:
            painter.drawLine(cx, cy - 4, cx - 4, cy + 3)
            painter.drawLine(cx - 4, cy + 3, cx + 4, cy + 3)
            painter.drawLine(cx + 4, cy + 3, cx, cy - 4)
        elif "Bracket Dot" in style_name or "Center Gap" in style_name:
            gap_cross()
            painter.setBrush(QBrush(QColor("#f2f2f2")))
            painter.drawEllipse(QPoint(cx, cy), 1, 1)
        elif "Shuriken" in style_name:
            offset = 2
            arm = 4
            painter.drawLine(cx - offset, cy - offset, cx - offset, cy - offset - arm)
            painter.drawLine(cx + offset, cy + offset, cx + offset, cy + offset + arm)
            painter.drawLine(cx - offset - arm, cy + offset, cx - offset, cy + offset)
            painter.drawLine(cx + offset, cy - offset, cx + offset + arm, cy - offset)
            painter.setBrush(QBrush(QColor("#f2f2f2")))
            painter.drawEllipse(QPoint(cx, cy), 1, 1)
        elif "Star" in style_name:
            painter.drawLine(cx - 5, cy, cx + 5, cy)
            painter.drawLine(cx, cy - 5, cx, cy + 5)
            painter.drawLine(cx - 4, cy - 4, cx + 4, cy + 4)
            painter.drawLine(cx - 4, cy + 4, cx + 4, cy - 4)
        else:
            gap_cross()

        painter.end()
        return QIcon(pixmap)

    def build_color_preview_icon(self, color_value) -> QIcon:
        if isinstance(color_value, QColor):
            swatch = color_value
        else:
            color_map = {
                "Đỏ": QColor(255, 30, 30),
                "Đỏ Cam": QColor(255, 69, 0),
                "Cam": QColor(255, 140, 0),
                "Vàng": QColor(255, 215, 0),
                "Xanh Lá": QColor(0, 255, 0),
                "Xanh Ngọc": QColor(0, 255, 255),
                "Xanh Dương": QColor(0, 180, 255),
                "Tím": QColor(180, 0, 255),
                "Tím Hồng": QColor(255, 60, 255),
                "Hồng": QColor(255, 105, 180),
                "Trắng": QColor(255, 255, 255),
                "Bạc": QColor(192, 192, 192),
            }
            swatch = color_map.get(color_value, QColor(255, 30, 30))

        pixmap = QPixmap(22, 22)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor("#6a6a6a"), 1))
        painter.setBrush(QBrush(swatch))
        painter.drawEllipse(4, 4, 14, 14)
        painter.end()
        return QIcon(pixmap)

    def setup_ui_v2(self):
        root_widget = QWidget()
        root_widget.setStyleSheet("background: transparent;")
        root_layout = QVBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root_widget)

        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        self.container.setStyleSheet("""
            QFrame#MainContainer {
                background: #1b1b1b;
                border: 1px solid #313131;
                border-radius: 14px;
            }
        """)
        self._setup_root_layout = root_layout
        self._setup_ui_shell_bootstrap = True
        self.style_crosshair_combo(QComboBox())

    def style_crosshair_combo(self, widget: QComboBox):
        widget.setStyleSheet("""
            QComboBox {
                background-color: #1b1b1b;
                color: #d6d6d6;
                border: 1px solid #444;
                border-radius: 4px;
                font-size: 11px;
                padding: 0 8px;
            }
            QComboBox:hover {
                background-color: #1b1b1b;
                border: 1px solid #666;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 18px;
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0;
                height: 0;
            }
            QComboBox QAbstractItemView {
                background: #1b1b1b;
                color: #d6d6d6;
                border: 1px solid #333333;
                outline: none;
                padding: 4px;
                selection-background-color: #232323;
            }
        """)

    def create_section_title_float(self, parent: QWidget, text: str):
        if "\\u" in text:
            try:
                text = text.encode("utf-8").decode("unicode_escape")
            except Exception:
                pass
        label = QLabel(text, parent)
        label.setObjectName("SectionTitleFloat")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        fm = QFontMetrics(label.font())
        text_width = fm.horizontalAdvance(text)
        text_height = fm.height()
        label.setFixedSize(text_width + 28, max(18, text_height + 4))
        label.raise_()
        return label

    def position_section_title_float(self, label: QLabel, parent: QWidget):
        if label is None or parent is None:
            return
        x = max(12, (parent.width() - label.width()) // 2)
        y = 1
        label.move(x, y)

    def position_all_macro_titles(self):
        title_pairs = (
            ("header_detection", "panel_detection"),
            ("header_settings", "group_settings"),
            ("header_capture", "capture_box"),
            ("header_scope", "scope_box"),
            ("header_crosshair", "crosshair_box"),
        )
        for label_attr, parent_attr in title_pairs:
            label = getattr(self, label_attr, None)
            parent = getattr(self, parent_attr, None)
            if isinstance(label, QLabel) and parent is not None:
                self.position_section_title_float(label, parent)
        if not getattr(self, "_setup_ui_shell_bootstrap", False):
            return
        self._setup_ui_shell_bootstrap = False
        root_layout = getattr(self, "_setup_root_layout", None)
        if root_layout is None:
            return
        root_layout.addWidget(self.container)

        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.title_bar = QFrame()
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet("""
            QFrame#TitleBar {
                background: transparent;
                border: none;
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
            }
        """)
        header_layout = QHBoxLayout(self.title_bar)
        header_layout.setContentsMargins(10, 0, 10, 0)

        btn_min = QPushButton("-")
        btn_min.setObjectName("MinBtn")
        btn_min.setFixedSize(20, 20)
        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_min.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_min.setStyleSheet("""
            QPushButton#MinBtn {
                background: #2b2f33;
                color: #d6d9dc;
                border: 1px solid #3f454a;
                border-radius: 10px;
                font-size: 11px;
                font-weight: 900;
            }
            QPushButton#MinBtn:hover {
                background: #353b40;
                color: #ffffff;
                border: 1px solid #5c656d;
            }
        """)
        btn_min.clicked.connect(self.minimize_to_taskbar)

        btn_close = QPushButton("X")
        btn_close.setObjectName("CloseBtn")
        btn_close.setFixedSize(20, 20)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_close.setStyleSheet("""
            QPushButton#CloseBtn {
                background: #2b2f33;
                color: #ff5d5d;
                border: 1px solid #3f454a;
                border-radius: 10px;
                font-size: 11px;
                font-weight: 900;
            }
            QPushButton#CloseBtn:hover {
                background: #4a1e22;
                color: #ffffff;
                border: 1px solid #ff6f6f;
            }
        """)
        btn_close.clicked.connect(self.handle_close_action)

        self.app_title_label = QLabel("Macro & Aim By Di88")
        self.app_title_label.setObjectName("AppTitle")
        self.app_title_label.setStyleSheet("""
            QLabel#AppTitle {
                color: #e9edf2;
                font-size: 13px;
                font-weight: 800;
                letter-spacing: 0px;
                background: transparent;
                border: none;
            }
        """)
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(4)
        glow.setColor(QColor(0, 0, 0, 200))
        glow.setOffset(1, 1)
        self.app_title_label.setGraphicsEffect(glow)

        self.app_logo = QLabel()
        icon_path = get_resource_path("di88vp.ico")
        logo_icon = QIcon(icon_path)
        self.app_logo.setPixmap(logo_icon.pixmap(22, 22))
        self.app_logo.setContentsMargins(0, 0, 5, 0)

        left_title_placeholder = QWidget()
        left_title_placeholder.setFixedWidth(45)
        left_title_placeholder.setStyleSheet("background: transparent; border: none;")

        title_center_wrap = QWidget()
        title_center_wrap.setStyleSheet("background: transparent; border: none;")
        title_center_layout = QHBoxLayout(title_center_wrap)
        title_center_layout.setContentsMargins(0, 0, 0, 0)
        title_center_layout.setSpacing(0)
        title_center_layout.addWidget(self.app_logo)
        title_center_layout.addWidget(self.app_title_label)

        right_controls_wrap = QWidget()
        right_controls_wrap.setFixedWidth(45)
        right_controls_wrap.setStyleSheet("background: transparent; border: none;")
        right_controls_layout = QHBoxLayout(right_controls_wrap)
        right_controls_layout.setContentsMargins(0, 0, 0, 0)
        right_controls_layout.setSpacing(5)
        right_controls_layout.addWidget(btn_min)
        right_controls_layout.addWidget(btn_close)

        header_layout.addWidget(left_title_placeholder, 0)
        header_layout.addStretch(1)
        header_layout.addWidget(title_center_wrap, 0, Qt.AlignmentFlag.AlignCenter)
        header_layout.addStretch(1)
        header_layout.addWidget(right_controls_wrap, 0)

        self.title_bar.mousePressEvent = self.mousePressEvent
        self.title_bar.mouseMoveEvent = self.mouseMoveEvent
        main_layout.addWidget(self.title_bar)

        content_widget = QWidget()
        content_widget.setObjectName("MainContentShell")
        content_widget.setStyleSheet("""
            QWidget#MainContentShell {
                background: #1b1b1b;
                border: none;
            }
        """)
        content_shell = QHBoxLayout(content_widget)
        content_shell.setContentsMargins(10, 10, 10, 10)
        content_shell.setSpacing(12)

        self.left_nav = QFrame()
        self.left_nav.setObjectName("MainSideNav")
        self.left_nav.setFixedWidth(160)
        self.left_nav.setStyleSheet("""
            QFrame#MainSideNav {
                background: #121212;
                border: 1px solid #313131;
                border-radius: 14px;
            }
        """)
        nav_layout = QVBoxLayout(self.left_nav)
        nav_layout.setContentsMargins(12, 14, 12, 14)
        nav_layout.setSpacing(10)

        nav_brand_card = QFrame()
        nav_brand_card.setObjectName("NavBrandCard")
        nav_brand_card.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        nav_brand_card.setMouseTracking(True)
        nav_brand_card.setStyleSheet("""
            QFrame#NavBrandCard {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1b212b,
                    stop:0.45 #151b23,
                    stop:1 #11161d
                );
                border: 1px solid #29313a;
                border-radius: 12px;
            }
            QFrame#NavBrandCard:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #202a37,
                    stop:0.45 #182330,
                    stop:1 #121c26
                );
                border: 1px solid #3d5166;
            }
        """)
        nav_brand_shadow = QGraphicsDropShadowEffect(nav_brand_card)
        nav_brand_shadow.setBlurRadius(20)
        nav_brand_shadow.setOffset(0, 6)
        nav_brand_shadow.setColor(QColor(0, 0, 0, 110))
        nav_brand_card.setGraphicsEffect(nav_brand_shadow)
        nav_brand_layout = QVBoxLayout(nav_brand_card)
        nav_brand_layout.setContentsMargins(12, 12, 12, 10)
        nav_brand_layout.setSpacing(4)

        nav_brand_title = QLabel("Di88 Control")
        nav_brand_title.setStyleSheet("""
            QLabel {
                color: #f4f7fb;
                font-size: 16px;
                font-weight: 900;
                letter-spacing: 0px;
                background: transparent;
                border: none;
            }
        """)

        nav_brand_title_shadow = QGraphicsDropShadowEffect(nav_brand_title)
        nav_brand_title_shadow.setBlurRadius(18)
        nav_brand_title_shadow.setOffset(0, 2)
        nav_brand_title_shadow.setColor(QColor(0, 0, 0, 150))
        nav_brand_title.setGraphicsEffect(nav_brand_title_shadow)

        nav_brand_subtitle = QLabel("Macro & Aim")
        nav_brand_subtitle.setStyleSheet("""
            QLabel {
                color: #78dfff;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 1px;
                background: transparent;
                border: none;
            }
        """)

        nav_brand_line = QFrame()
        nav_brand_line.setFixedHeight(2)
        nav_brand_line.setStyleSheet("""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #00d8ff,
                stop:1 #2f4dff
            );
            border: none;
            border-radius: 1px;
        """)

        nav_brand_layout.addWidget(nav_brand_title)
        nav_brand_layout.addWidget(nav_brand_subtitle)
        nav_brand_layout.addSpacing(2)
        nav_brand_layout.addWidget(nav_brand_line)
        nav_layout.addWidget(nav_brand_card)
        nav_layout.addSpacing(8)

        self.btn_nav_home = self.build_nav_button("HOME", "home")
        self.btn_nav_macro = self.build_nav_button("MACRO", "macro")
        self.btn_nav_aim = self.build_nav_button("AIM BOT", "aim")
        self._nav_buttons = {
            "home": self.btn_nav_home,
            "macro": self.btn_nav_macro,
            "aim": self.btn_nav_aim,
        }
        nav_layout.addWidget(self.btn_nav_home)
        nav_layout.addWidget(self.btn_nav_macro)
        nav_layout.addWidget(self.btn_nav_aim)
        nav_layout.addStretch(1)

        nav_version = QLabel("v2.0 DI88")
        nav_version.setStyleSheet("""
            QLabel {
                color: #6e6e6e;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
                background: transparent;
                border: none;
            }
        """)
        nav_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(nav_version)

        content_shell.addWidget(self.left_nav, 0)

        page_area = QWidget()
        page_area.setObjectName("MainPageArea")
        page_area.setStyleSheet("""
            QWidget#MainPageArea {
                background: #1b1b1b;
                border: none;
                border-radius: 14px;
            }
        """)
        page_area_layout = QVBoxLayout(page_area)
        page_area_layout.setContentsMargins(0, 0, 0, 0)
        page_area_layout.setSpacing(10)

        self.page_banner = QFrame()
        self.page_banner.setObjectName("MainPageBanner")
        self.page_banner.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.page_banner.setStyleSheet("""
            QFrame#MainPageBanner {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #0d1e33,
                    stop: 1 #112944
                );
                border: 1px solid #2f3942;
                border-radius: 14px;
            }
        """)
        page_banner_layout = QHBoxLayout(self.page_banner)
        page_banner_layout.setContentsMargins(20, 16, 20, 16)
        page_banner_layout.setSpacing(14)

        banner_text_wrap = QWidget()
        banner_text_wrap.setStyleSheet("background: transparent; border: none;")
        banner_text_layout = QVBoxLayout(banner_text_wrap)
        banner_text_layout.setContentsMargins(0, 0, 0, 0)
        banner_text_layout.setSpacing(3)
        self.page_banner_eyebrow = QLabel("DI88 CONTROL")
        self.page_banner_eyebrow.setStyleSheet("""
            QLabel {
                color: #77dfff;
                font-size: 10px;
                font-weight: 900;
                letter-spacing: 1px;
                background: transparent;
                border: none;
            }
        """)
        self.page_banner_title = QLabel("TRUNG TÂM ĐIỀU KHIỂN")
        self.page_banner_title.setStyleSheet("color: #f3f6fb; font-size: 17px; font-weight: 900; letter-spacing: 1px; background: transparent; border: none;")
        self.page_banner_subtitle = QLabel("Macro & Aim By Di88")
        self.page_banner_subtitle.setStyleSheet("color: #a8ccef; font-size: 11px; font-weight: 700; letter-spacing: 0px; background: transparent; border: none;")
        banner_text_layout.addWidget(self.page_banner_eyebrow)
        banner_text_layout.addWidget(self.page_banner_title)
        banner_text_layout.addWidget(self.page_banner_subtitle)

        self.page_banner_badge = QLabel("TỔNG HỢP")
        self.page_banner_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_banner_badge.setMinimumWidth(122)
        self.page_banner_badge.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        page_banner_layout.addWidget(banner_text_wrap, 1)
        page_banner_layout.addWidget(self.page_banner_badge, 0, Qt.AlignmentFlag.AlignVCenter)

        page_area_layout.addWidget(self.page_banner)

        macro_column = QWidget()
        body_layout = QVBoxLayout(macro_column)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(2)

        panel_style = """
            QFrame {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
            }
        """

        self._macro_box_style = """
            QGroupBox {
                background-color: #1b1b1b;
                border: 1px solid #333;
                border-radius: 10px;
                margin-top: 0;
            }
            QGroupBox::indicator {
                width: 0;
                height: 0;
                border: none;
                background: transparent;
            }
        """

        self.panel_detection = MacroTitledBox("\u0054\u0068\u00f4\u006e\u0067\u0020\u0054\u0069\u006e\u0020\u0053\u00fa\u006e\u0067", "DetectionPanel")
        detection_layout = self.panel_detection.content_layout()
        detection_layout.setSpacing(6)
        self.header_detection = None

        detection_row = QHBoxLayout()
        detection_row.setContentsMargins(0, 0, 0, 0)
        detection_row.setSpacing(8)

        self.panel_g1 = QFrame()
        self.panel_g1.setObjectName("P1")
        self.panel_g1.setStyleSheet("QFrame#P1 { background: transparent; border: none; }")
        l_g1 = QVBoxLayout(self.panel_g1)
        l_g1.setContentsMargins(0, 0, 0, 0)
        l_g1.setSpacing(4)
        g1_title_row = QHBoxLayout()
        g1_title_row.setContentsMargins(0, 0, 0, 0)
        g1_title_row.setSpacing(6)
        g1_title_row.addStretch(1)
        self.lbl_g1_title = QLabel("S\u00fang 1")
        self.lbl_g1_title.setObjectName("Gun1Title")
        self.g1_title_line = QFrame()
        self.g1_title_line.setObjectName("Gun1TitleLine")
        self.g1_title_line.setFrameShape(QFrame.Shape.HLine)
        self.g1_title_line.setFixedSize(72, 2)
        self.g1_title_line.hide()
        g1_title_row.addWidget(self.lbl_g1_title)
        g1_title_row.addStretch(1)
        l_g1.addLayout(g1_title_row)
        g1_content_row = QHBoxLayout()
        g1_content_row.setContentsMargins(0, 0, 0, 0)
        g1_content_row.setSpacing(8)
        self.g1_accent_line = QFrame()
        self.g1_accent_line.setFixedWidth(2)
        self.g1_accent_line.setStyleSheet("background-color: #9a3a3a; border: none; border-radius: 1px;")
        g1_content_row.addWidget(self.g1_accent_line)
        self.grid_g1 = QGridLayout()
        self.grid_g1.setVerticalSpacing(6)
        self.grid_g1.setHorizontalSpacing(0)
        self.grid_g1.setColumnMinimumWidth(0, 48)
        self.grid_g1.setColumnMinimumWidth(1, 20)
        self.grid_g1.setColumnStretch(2, 1)
        self.lbl_g1_name = create_data_row(self.grid_g1, 0, "Name")
        self.lbl_g1_scope = create_data_row(self.grid_g1, 1, "Scope")
        self.lbl_g1_grip = create_data_row(self.grid_g1, 2, "Grip")
        self.lbl_g1_muzzle = create_data_row(self.grid_g1, 3, "Muzz")
        g1_content_row.addLayout(self.grid_g1, 1)
        l_g1.addLayout(g1_content_row)
        detection_row.addWidget(self.panel_g1, stretch=1)

        self.panel_g2 = QFrame()
        self.panel_g2.setObjectName("P2")
        self.panel_g2.setStyleSheet("QFrame#P2 { background: transparent; border: none; }")
        l_g2 = QVBoxLayout(self.panel_g2)
        l_g2.setContentsMargins(0, 0, 0, 0)
        l_g2.setSpacing(4)
        g2_title_row = QHBoxLayout()
        g2_title_row.setContentsMargins(0, 0, 0, 0)
        g2_title_row.setSpacing(6)
        g2_title_row.addStretch(1)
        self.lbl_g2_title = QLabel("S\u00fang 2")
        self.lbl_g2_title.setObjectName("Gun2Title")
        self.g2_title_line = QFrame()
        self.g2_title_line.setObjectName("Gun2TitleLine")
        self.g2_title_line.setFrameShape(QFrame.Shape.HLine)
        self.g2_title_line.setFixedSize(72, 2)
        self.g2_title_line.hide()
        g2_title_row.addWidget(self.lbl_g2_title)
        g2_title_row.addStretch(1)
        l_g2.addLayout(g2_title_row)
        g2_content_row = QHBoxLayout()
        g2_content_row.setContentsMargins(0, 0, 0, 0)
        g2_content_row.setSpacing(8)
        self.g2_accent_line = QFrame()
        self.g2_accent_line.setFixedWidth(2)
        self.g2_accent_line.setStyleSheet("background-color: #2f8f4a; border: none; border-radius: 1px;")
        g2_content_row.addWidget(self.g2_accent_line)
        self.grid_g2 = QGridLayout()
        self.grid_g2.setVerticalSpacing(6)
        self.grid_g2.setHorizontalSpacing(0)
        self.grid_g2.setColumnMinimumWidth(0, 48)
        self.grid_g2.setColumnMinimumWidth(1, 20)
        self.grid_g2.setColumnStretch(2, 1)
        self.lbl_g2_name = create_data_row(self.grid_g2, 0, "Name")
        self.lbl_g2_scope = create_data_row(self.grid_g2, 1, "Scope")
        self.lbl_g2_grip = create_data_row(self.grid_g2, 2, "Grip")
        self.lbl_g2_muzzle = create_data_row(self.grid_g2, 3, "Muzz")
        g2_content_row.addLayout(self.grid_g2, 1)
        l_g2.addLayout(g2_content_row)
        detection_row.addWidget(self.panel_g2, stretch=1)

        detection_layout.addLayout(detection_row)

        self.group_settings = MacroTitledBox("Hướng Dẫn Sử Dụng", "SettingsBox")
        self.group_settings.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        settings_layout = self.group_settings.content_layout()
        settings_layout.setSpacing(6)
        self.header_settings = None
        self.bind_box = MacroTitledBox("Bind Nút", "BindBox")
        self.bind_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        bind_layout = self.bind_box.content_layout()
        bind_layout.setSpacing(6)
        self.header_bind = None
        self.toggle_box = MacroTitledBox("Bật/Tắt", "ToggleBox")
        self.toggle_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        toggle_layout = self.toggle_box.content_layout()
        toggle_layout.setSpacing(6)
        self.header_toggle = None

        def add_settings_grid_row(target_layout, label_text: str, value_widget: QWidget, side_widget: QWidget | None = None):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)

            label = QLabel(label_text)
            label.setFixedWidth(122)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setProperty("role", "setting-label")
            self.style_setting_label(label)

            value_widget.setSizePolicy(value_widget.sizePolicy().horizontalPolicy(), value_widget.sizePolicy().verticalPolicy())
            if hasattr(value_widget, "setFixedHeight"):
                value_widget.setFixedHeight(24)

            row.addWidget(label)
            row.addWidget(value_widget, stretch=1)

            if side_widget is not None:
                row.addWidget(side_widget)

            target_layout.addLayout(row)
            return label

        def add_toggle_row(target_layout, label_text: str, switch_widget: QWidget):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)

            label = QLabel(label_text)
            label.setFixedWidth(122)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setProperty("role", "setting-label")
            self.style_setting_label(label)

            switch_wrap = QWidget()
            switch_wrap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            switch_layout = QHBoxLayout(switch_wrap)
            switch_layout.setContentsMargins(0, 0, 0, 0)
            switch_layout.setSpacing(0)
            switch_layout.addStretch()
            switch_layout.addWidget(switch_widget)

            row.addWidget(label)
            row.addWidget(switch_wrap, stretch=1)
            target_layout.addLayout(row)
            return label

        self.btn_fastloot_key = QPushButton("caps_lock")
        self.btn_fastloot_key.setProperty("role", "setting-btn")
        self.btn_fastloot_key.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fastloot_key.setFixedHeight(24)
        self.style_setting_button(self.btn_fastloot_key)
        self.btn_fastloot_key.clicked.connect(lambda: self.start_keybind_listening(self.btn_fastloot_key, "fast_loot_key"))
        self.btn_fastloot_toggle = QPushButton("OFF")
        self.btn_fastloot_toggle.setObjectName("FastLootToggleBtn")
        self.btn_fastloot_toggle.setProperty("state", "OFF")
        self.btn_fastloot_toggle.clicked.connect(self.toggle_fast_loot)
        self.btn_fastloot_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fastloot_toggle.setFixedSize(50, 24)
        self.btn_fastloot_toggle.hide()
        self.lbl_fastloot_row = add_settings_grid_row(bind_layout, "Nhặt Đồ Nhanh", self.btn_fastloot_key)
        self.btn_fastloot_switch = MobileSwitch(False)
        self.btn_fastloot_switch.toggled.connect(self.toggle_fast_loot)
        self.lbl_fastloot_toggle_row = add_toggle_row(toggle_layout, "Nhặt Đồ Nhanh", self.btn_fastloot_switch)
        self.lbl_fastloot_toggle_row.setFixedWidth(122)
        self.lbl_fastloot_toggle_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_slide_hint = QPushButton("Shift + W + ( A or D ) + C")
        self.btn_slide_hint.setProperty("role", "setting-btn")
        self.btn_slide_hint.setEnabled(False)
        self.btn_slide_hint.setCursor(Qt.CursorShape.ArrowCursor)
        self.style_setting_button(self.btn_slide_hint)
        self.lbl_slide_row = add_settings_grid_row(settings_layout, "Lướt Ngồi", self.btn_slide_hint)

        self.btn_slide_toggle = QPushButton("ON")
        self.btn_slide_toggle.setObjectName("SlideToggleBtn")
        self.btn_slide_toggle.setProperty("state", "ON")
        self.btn_slide_toggle.clicked.connect(self.toggle_slide_trick)
        self.btn_slide_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_slide_toggle.setFixedSize(50, 24)
        self.btn_slide_toggle.hide()
        self.btn_slide_switch = MobileSwitch(True)
        self.btn_slide_switch.toggled.connect(self.toggle_slide_trick)
        self.lbl_slide_toggle_row = add_toggle_row(toggle_layout, "Lướt Ngồi", self.btn_slide_switch)
        self.lbl_slide_toggle_row.setFixedWidth(122)
        self.lbl_slide_toggle_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_slot1_hint = QPushButton("1")
        self.btn_slot1_hint.setProperty("role", "setting-btn")
        self.btn_slot1_hint.setEnabled(False)
        self.btn_slot1_hint.setCursor(Qt.CursorShape.ArrowCursor)
        self.style_setting_button(self.btn_slot1_hint)
        self.lbl_slot1_row = add_settings_grid_row(settings_layout, "Phím Súng 1", self.btn_slot1_hint)

        self.btn_slot2_hint = QPushButton("2")
        self.btn_slot2_hint.setProperty("role", "setting-btn")
        self.btn_slot2_hint.setEnabled(False)
        self.btn_slot2_hint.setCursor(Qt.CursorShape.ArrowCursor)
        self.style_setting_button(self.btn_slot2_hint)
        self.lbl_slot2_row = add_settings_grid_row(settings_layout, "Phím Súng 2", self.btn_slot2_hint)

        self.btn_stopkeys = QPushButton("X, G, 5")
        self.btn_stopkeys.setProperty("role", "setting-btn")
        self.btn_stopkeys.setEnabled(False)
        self.btn_stopkeys.setCursor(Qt.CursorShape.ArrowCursor)
        self.style_setting_button(self.btn_stopkeys)
        self.lbl_stopkeys_row = add_settings_grid_row(settings_layout, "Phím Dừng Khẩn", self.btn_stopkeys)

        self.btn_adsmode = QPushButton("HOLD")
        self.btn_adsmode.setProperty("role", "setting-btn")
        self.btn_adsmode.setEnabled(False)
        self.btn_adsmode.setCursor(Qt.CursorShape.ArrowCursor)
        self.style_setting_button(self.btn_adsmode)
        self.lbl_adsmode_row = add_settings_grid_row(settings_layout, "Kiểu ADS", self.btn_adsmode)

        self.btn_guitoggle = QPushButton("F1")
        self.btn_guitoggle.setProperty("role", "setting-btn")
        self.btn_guitoggle.setEnabled(True)
        self.btn_guitoggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.style_setting_button(self.btn_guitoggle)
        self.btn_guitoggle.clicked.connect(lambda: self.start_keybind_listening(self.btn_guitoggle, "gui_toggle"))
        self.lbl_guitoggle_row = add_settings_grid_row(bind_layout, "Ẩn/Hiện APP", self.btn_guitoggle)

        self.btn_overlay_key = QPushButton("delete")
        self.btn_overlay_key.setProperty("role", "setting-btn")
        self.btn_overlay_key.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_overlay_key.setFixedHeight(24)
        self.style_setting_button(self.btn_overlay_key)
        self.btn_overlay_key.clicked.connect(lambda: self.start_keybind_listening(self.btn_overlay_key, "overlay_key"))
        self.btn_overlay_toggle = QPushButton("ON")
        self.btn_overlay_toggle.setObjectName("OverlayToggleBtn")
        self.btn_overlay_toggle.setProperty("state", "ON")
        self.btn_overlay_toggle.setCheckable(False)
        self.btn_overlay_toggle.clicked.connect(self.toggle_overlay_visibility)
        self.btn_overlay_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_overlay_toggle.setFixedSize(50, 24)
        self.btn_overlay_toggle.hide()
        self.lbl_overlay_row = add_settings_grid_row(bind_layout, "Overlay", self.btn_overlay_key)

        self.capture_box = MacroTitledBox("\u0043\u0068\u1ebf\u0020\u0110\u1ed9\u0020\u0043\u0068\u1ee5\u0070", "CaptureBox")
        self.capture_box.setMinimumWidth(0)
        self.capture_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.capture_box.setFixedHeight(82)
        capture_layout = self.capture_box.content_layout()
        capture_layout.setSpacing(6)
        self.header_capture = None

        row_capture = QHBoxLayout()
        row_capture.setContentsMargins(0, 0, 0, 0)
        row_capture.setSpacing(3)
        self.lbl_capture_mode_auto = QLabel("DXGI")
        self.lbl_capture_mode_auto.hide()
        self.btn_capture_native = QPushButton("DXGI")
        self.btn_capture_native.setFixedHeight(22)
        self.btn_capture_native.setMinimumWidth(72)
        self.btn_capture_native.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_capture_native.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_capture_native.clicked.connect(lambda: self.set_capture_mode("DXGI"))
        self.btn_capture_dxcam = QPushButton("DXCAM")
        self.btn_capture_dxcam.setFixedHeight(22)
        self.btn_capture_dxcam.setMinimumWidth(72)
        self.btn_capture_dxcam.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_capture_dxcam.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_capture_dxcam.clicked.connect(lambda: self.set_capture_mode("DXCAM"))
        self.btn_capture_mss = QPushButton("MSS")
        self.btn_capture_mss.setFixedHeight(22)
        self.btn_capture_mss.setMinimumWidth(72)
        self.btn_capture_mss.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_capture_mss.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_capture_mss.clicked.connect(lambda: self.set_capture_mode("MSS"))
        row_capture.addWidget(self.btn_capture_native, 1)
        row_capture.addWidget(self.btn_capture_dxcam, 1)
        row_capture.addWidget(self.btn_capture_mss, 1)
        capture_layout.addLayout(row_capture)

        self.scope_box = MacroTitledBox("\u0043\u01b0\u1edd\u006e\u0067\u0020\u0110\u1ed9\u0020\u0053\u0063\u006f\u0070\u0065", "ScopeIntensityBox")
        self.scope_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        scope_layout = self.scope_box.content_layout()
        scope_layout.setSpacing(6)
        self.header_scope = None

        self.scope_order = [
            ("normal", "Redot/Holo"),
            ("x2", "Scope X2"),
            ("x3", "Scope X3"),
            ("x4", "Scope X4"),
            ("x6", "Scope X6"),
        ]
        self.scope_sliders = {}
        self.scope_value_labels = {}

        for scope_key, scope_label in self.scope_order:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)

            label = QLabel(scope_label)
            label.setFixedWidth(82)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setProperty("role", "setting-label")
            self.style_setting_label(label)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(50, 150)
            slider.setSingleStep(1)
            slider.setPageStep(5)
            slider.setValue(100)
            slider.setFixedHeight(20)
            self.style_scope_slider(slider)

            value_label = QLabel("100%")
            value_label.setFixedWidth(48)
            value_label.setFixedHeight(24)
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.style_scope_value_label(value_label)

            slider.valueChanged.connect(lambda value, key=scope_key: self.update_scope_intensity_label(key, value))

            self.scope_sliders[scope_key] = slider
            self.scope_value_labels[scope_key] = value_label

            row.addWidget(label)
            row.addWidget(slider, stretch=1)
            row.addWidget(value_label)
            scope_layout.addLayout(row)

        self.crosshair_box = MacroTitledBox("\u0054\u00e2\u006d\u0020\u004e\u0067\u1eaf\u006d", "CrosshairBox")
        self.crosshair_box.setMinimumWidth(0)
        self.crosshair_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.crosshair_box.setFixedHeight(82)
        cross_layout = self.crosshair_box.content_layout()
        cross_layout.setSpacing(6)
        self.header_crosshair = None

        cross_grid = QGridLayout()
        cross_grid.setContentsMargins(0, 0, 0, 0)
        cross_grid.setHorizontalSpacing(3)
        cross_grid.setVerticalSpacing(2)
        cross_grid.setColumnStretch(0, 1)
        cross_grid.setColumnStretch(1, 1)

        self.lbl_cross_style = QLabel("\u003e \u004b\u0069\u1ec3\u0075 \u0054\u00e2\u006d \u003c")
        self.lbl_cross_style.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_cross_style.setStyleSheet("color: #c6c6c6; font-size: 8px; font-weight: bold;")

        self.lbl_cross_color = QLabel("> Màu <")
        self.lbl_cross_color.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_cross_color.setStyleSheet("color: #c6c6c6; font-size: 8px; font-weight: bold;")

        cross_grid.addWidget(self.lbl_cross_style, 0, 0)
        cross_grid.addWidget(self.lbl_cross_color, 0, 1)
        self.btn_cross_toggle = QPushButton("ON")
        self.btn_cross_toggle.setObjectName("CrosshairToggleBtn")
        self.btn_cross_toggle.setProperty("checked", "true")
        self.btn_cross_toggle.setCheckable(True)
        self.btn_cross_toggle.setChecked(True)
        self.btn_cross_toggle.setFixedSize(42, 22)
        self.btn_cross_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cross_toggle.clicked.connect(self.toggle_crosshair)
        self.btn_cross_toggle.hide()

        self.crosshair_style_options = [
            ("Chữ Thập Hở", "1: Gap Cross"),
            ("Chữ T", "2: T-Shape"),
            ("Tròn Có Chấm", "3: Circle Dot"),
            ("Cổ Điển", "5: Classic"),
            ("Chấm Nhỏ", "6: Micro Dot"),
            ("Ô Rỗng", "7: Hollow Box"),
            ("Chữ Thập Có Chấm", "8: Cross + Dot"),
            ("Mũi Tên", "9: Chevron"),
            ("Chữ X", "10: X-Shape"),
            ("Kim Cương", "11: Diamond"),
            ("\u0054\u0061\u006d \u0047\u0069\u00e1\u0063", "13: Triangle"),
            ("Chấm Vuông", "14: Square Dot"),
            ("Ngoặc Có Chấm", "17: Bracket Dot"),
            ("Phi Tiêu", "18: Shuriken"),
            # Đã làm sạch chú thích lỗi mã hóa.
            ("Dấu Cộng Có Chấm", "22: Plus Dot"),
            ("Chữ V", "23: V-Shape"),
            ("Ngôi Sao", "24: Star"),
        ]
        self.combo_style = CenteredComboBox(center_mode="full")
        self.combo_style.setObjectName("CrosshairStyleCombo")
        self.combo_style.setItemDelegate(IconOnlyComboDelegate(self.combo_style))
        self.combo_style.setIconSize(QSize(36, 18))
        self.combo_style.view().setStyleSheet("""
            QListView {
                background: #1b1b1b;
                border: 1px solid #333333;
                outline: none;
                padding: 4px;
            }
            QListView::item {
                border: none;
                margin: 1px 4px;
            }
            QListView::item:selected {
                background: #232323;
            }
        """)
        self.combo_style.addItems([display for display, _ in self.crosshair_style_options])
        self.combo_style.setCurrentText("Chữ Thập Hở")
        for i in range(self.combo_style.count()):
            _, internal_style = self.crosshair_style_options[i]
            self.combo_style.setItemIcon(i, self.build_crosshair_preview_icon(internal_style))
            self.combo_style.setItemData(i, int(Qt.AlignmentFlag.AlignCenter), Qt.ItemDataRole.TextAlignmentRole)
        self.combo_style.setFixedHeight(22)
        self.combo_style.setMaximumWidth(16777215)
        self.combo_style.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.style_crosshair_combo(self.combo_style)
        self.combo_style.currentIndexChanged.connect(self.change_crosshair_style)

        self.combo_color = CenteredComboBox(center_mode="full")
        self.combo_color.setObjectName("CrosshairColorCombo")
        self.combo_color.setItemDelegate(IconOnlyComboDelegate(self.combo_color))
        self.combo_color.setIconSize(QSize(22, 22))
        self.combo_color.view().setStyleSheet("""
            QListView {
                background: #1b1b1b;
                border: 1px solid #333333;
                outline: none;
                padding: 4px;
            }
            QListView::item {
                border: none;
                margin: 1px 4px;
            }
            QListView::item:selected {
                background: #232323;
            }
        """)
        self.combo_color.addItems([
            "Đỏ", "Đỏ Cam", "Cam", "Vàng",
            "Xanh Lá", "Xanh Ngọc", "Xanh Dương",
            "Tím", "Tím Hồng", "Hồng",
            "Trắng", "Bạc"
        ])
        self.crosshair_color_swatches = [
            QColor(255, 30, 30),
            QColor(255, 69, 0),
            QColor(255, 140, 0),
            QColor(255, 215, 0),
            QColor(0, 255, 0),
            QColor(0, 255, 255),
            QColor(0, 180, 255),
            QColor(180, 0, 255),
            QColor(255, 60, 255),
            QColor(255, 105, 180),
            QColor(255, 255, 255),
            QColor(192, 192, 192),
        ]
        self.combo_color.setCurrentText("Đỏ")
        for i in range(self.combo_color.count()):
            self.combo_color.setItemIcon(i, self.build_color_preview_icon(self.crosshair_color_swatches[i]))
            self.combo_color.setItemData(i, int(Qt.AlignmentFlag.AlignCenter), Qt.ItemDataRole.TextAlignmentRole)
        self.combo_color.setFixedHeight(22)
        self.combo_color.setMaximumWidth(16777215)
        self.combo_color.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.style_crosshair_combo(self.combo_color)
        self.combo_color.currentIndexChanged.connect(self.change_crosshair_color)

        self.cross_toggle_buttons = QWidget()
        self.cross_toggle_buttons.hide()

        self.btn_cross_on = QPushButton("BẬT")
        self.btn_cross_on.hide()
        self.btn_cross_on.clicked.connect(lambda: self.toggle_crosshair(True))

        self.btn_cross_off = QPushButton("TẮT")
        self.btn_cross_off.hide()
        self.btn_cross_off.clicked.connect(lambda: self.toggle_crosshair(False))

        self.btn_cross_bind = QPushButton("HOME")
        self.btn_cross_bind.setObjectName("CrosshairBindBtn")
        self.btn_cross_bind.setProperty("role", "setting-btn")
        self.btn_cross_bind.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cross_bind.setFixedHeight(22)
        self.btn_cross_bind.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.style_setting_button(self.btn_cross_bind)
        self.btn_cross_bind.clicked.connect(lambda: self.start_keybind_listening(self.btn_cross_bind, "crosshair_toggle_key"))
        self.btn_cross_bind.hide()
        cross_grid.addWidget(self.combo_style, 1, 0)
        cross_grid.addWidget(self.combo_color, 1, 1)
        cross_layout.addLayout(cross_grid)
        self.btn_crosshair_switch = MobileSwitch(True)
        self.btn_crosshair_switch.toggled.connect(self.toggle_crosshair)
        self.lbl_cross_toggle_row = add_toggle_row(toggle_layout, "Tâm Ngắm", self.btn_crosshair_switch)
        self.lbl_cross_toggle_row.setFixedWidth(122)
        self.lbl_cross_toggle_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.footer = QFrame()
        self.footer.setObjectName("StatusPanel")
        f_layout = QHBoxLayout(self.footer)
        f_layout.setSpacing(8)
        f_layout.setContentsMargins(10, 10, 10, 10)

        self.btn_macro = QPushButton("MACRO : OFF")
        self.btn_macro.setObjectName("MacroStatusBtn")
        self.btn_macro.setCursor(Qt.CursorShape.ForbiddenCursor)
        self.btn_macro.setFixedHeight(32)
        self.update_macro_style(False)

        self.lbl_stance = QLabel("TƯ THẾ : ĐỨNG")
        self.lbl_stance.setObjectName("StatusValueLabel")
        self.lbl_stance.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_stance.setFixedHeight(32)
        self.update_stance_status_style("TƯ THẾ : ĐỨNG")

        self.lbl_ads_status = QLabel("ADS : HOLD")
        self.lbl_ads_status.setObjectName("StatusValueLabel")
        self.lbl_ads_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_ads_status.setFixedHeight(32)
        self.update_ads_status_style("HOLD")

        f_layout.addWidget(self.btn_macro, stretch=1)
        f_layout.addWidget(self.lbl_stance, stretch=1)
        f_layout.addWidget(self.lbl_ads_status, stretch=1)

        macro_columns = QHBoxLayout()
        macro_columns.setContentsMargins(0, 0, 0, 0)
        macro_columns.setSpacing(2)

        macro_left_col = QVBoxLayout()
        macro_left_col.setContentsMargins(0, 0, 0, 0)
        macro_left_col.setSpacing(5)
        macro_left_col.addWidget(self.capture_box)
        macro_left_col.addWidget(self.group_settings)
        macro_left_col.addWidget(self.toggle_box)

        macro_right_col = QVBoxLayout()
        macro_right_col.setContentsMargins(0, 0, 0, 0)
        macro_right_col.setSpacing(5)
        macro_right_col.addWidget(self.crosshair_box)
        macro_right_col.addWidget(self.bind_box)
        macro_right_col.addWidget(self.scope_box)

        macro_columns.addLayout(macro_left_col, 1)
        macro_columns.addLayout(macro_right_col, 1)
        macro_columns.setAlignment(macro_left_col, Qt.AlignmentFlag.AlignTop)
        macro_columns.setAlignment(macro_right_col, Qt.AlignmentFlag.AlignTop)

        body_layout.addWidget(self.footer)
        body_layout.addWidget(self.panel_detection)
        body_layout.addLayout(macro_columns)
        QTimer.singleShot(0, self.sync_macro_box_heights)
        QTimer.singleShot(0, self.position_all_macro_titles)

        action_box = QFrame()
        action_box.setObjectName("ActionBox")
        action_layout = QVBoxLayout(action_box)
        action_layout.setContentsMargins(10, 8, 10, 10)
        action_layout.setSpacing(8)
        row_btns = QHBoxLayout()
        row_btns.setContentsMargins(0, 0, 0, 0)
        row_btns.setSpacing(8)
        btn_default = QPushButton("Cài Đặt Gốc")
        btn_default.setObjectName("DefaultBtn")
        btn_default.setFixedHeight(32)
        btn_default.setCursor(Qt.CursorShape.PointingHandCursor)
        self.style_action_button(btn_default, primary=False)
        btn_default.clicked.connect(self.reset_to_defaults)
        btn_save = QPushButton("Lưu Cài Đặt")
        btn_save.setObjectName("SaveBtn")
        btn_save.setFixedHeight(32)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.style_action_button(btn_save, primary=True)
        btn_save.clicked.connect(self.save_config)
        row_btns.addWidget(btn_default)
        row_btns.addWidget(btn_save)
        action_layout.addLayout(row_btns)
        action_box.hide()
        body_layout.addWidget(action_box)
        body_layout.addStretch()

        self.aim_workspace = AimPanelBuilder(self, SectionHeader).build()
        self.home_page = HomePanelBuilder(self).build()
        self.home_page.setStyleSheet("background: #1b1b1b; border: none;")

        self.macro_page = QWidget()
        self.macro_page.setStyleSheet("background: #1b1b1b; border: none;")
        macro_page_layout = QVBoxLayout(self.macro_page)
        macro_page_layout.setContentsMargins(0, 0, 0, 0)
        macro_page_layout.setSpacing(0)
        macro_page_layout.addWidget(macro_column)

        self.aim_page = QWidget()
        self.aim_page.setStyleSheet("background: #1b1b1b; border: none;")
        aim_page_layout = QVBoxLayout(self.aim_page)
        aim_page_layout.setContentsMargins(0, 0, 0, 0)
        aim_page_layout.setSpacing(0)
        aim_page_layout.addWidget(self.aim_workspace)

        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("MainPageStack")
        self.page_stack.setStyleSheet("""
            QStackedWidget#MainPageStack {
                background: #1b1b1b;
                border: none;
            }
        """)
        self.page_stack.addWidget(self.home_page)
        self.page_stack.addWidget(self.macro_page)
        self.page_stack.addWidget(self.aim_page)

        self._page_widgets = {
            "home": self.home_page,
            "macro": self.macro_page,
            "aim": self.aim_page,
        }
        self._current_main_page = "home"

        page_area_layout.addWidget(self.page_stack, 1)
        content_shell.addWidget(page_area, 1)

        main_layout.addWidget(content_widget)

        self.bottom_action_bar = QFrame()
        self.bottom_action_bar.setObjectName("BottomActionBar")
        self.bottom_action_bar.setStyleSheet("""
            QFrame#BottomActionBar {
                background: #272a2d;
                border-top: 1px solid #3c4044;
                border-bottom-left-radius: 14px;
                border-bottom-right-radius: 14px;
            }
        """)
        bottom_action_layout = QHBoxLayout(self.bottom_action_bar)
        bottom_action_layout.setContentsMargins(5, 10, 5, 10)
        bottom_action_layout.setSpacing(10)

        self.left_action_wrap = QWidget()
        self.left_action_wrap.setStyleSheet("background: transparent; border: none;")
        left_action_layout = QHBoxLayout(self.left_action_wrap)
        left_action_layout.setContentsMargins(0, 0, 0, 0)
        left_action_layout.setSpacing(0)
        self.btn_default_main = QPushButton("Cài Đặt Gốc")
        self.btn_default_main.setObjectName("DefaultBtn")
        self.btn_default_main.setText("Cài Đặt Gốc")
        self.btn_default_main.setFixedHeight(36)
        self.btn_default_main.setMinimumWidth(180)
        self.btn_default_main.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_default_main.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.style_action_button(self.btn_default_main, primary=False)
        self.btn_default_main.clicked.connect(self.reset_to_defaults)
        left_action_layout.addWidget(self.btn_default_main)
        left_action_layout.addStretch(1)

        self.center_action_wrap = QWidget()
        self.center_action_wrap.setStyleSheet("background: transparent; border: none;")
        center_action_layout = QHBoxLayout(self.center_action_wrap)
        center_action_layout.setContentsMargins(0, 0, 0, 0)
        center_action_layout.setSpacing(0)
        self.bottom_action_status = QLabel("")
        self.bottom_action_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bottom_action_status.setMinimumWidth(220)
        self.bottom_action_status.hide()
        center_action_layout.addStretch(1)
        center_action_layout.addWidget(self.bottom_action_status)
        center_action_layout.addStretch(1)

        self.right_action_wrap = QWidget()
        self.right_action_wrap.setStyleSheet("background: transparent; border: none;")
        right_action_layout = QHBoxLayout(self.right_action_wrap)
        right_action_layout.setContentsMargins(0, 0, 0, 0)
        right_action_layout.setSpacing(0)
        self.btn_save_main = QPushButton("Lưu Cài Đặt")
        self.btn_save_main.setObjectName("SaveBtn")
        self.btn_save_main.setText("Lưu Cài Đặt")
        self.btn_save_main.setFixedHeight(36)
        self.btn_save_main.setMinimumWidth(180)
        self.btn_save_main.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_main.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.style_action_button(self.btn_save_main, primary=True)
        self.btn_save_main.clicked.connect(self.save_config)
        right_action_layout.addStretch(1)
        right_action_layout.addWidget(self.btn_save_main)

        bottom_action_layout.addWidget(self.left_action_wrap, 1)
        bottom_action_layout.addWidget(self.center_action_wrap, 1)
        bottom_action_layout.addWidget(self.right_action_wrap, 1)

        main_layout.addWidget(self.bottom_action_bar)
        self.setup_hover_hints()
        self.load_config()
        self.load_crosshair_settings()
        self.update_nav_button_styles()
        self.update_home_snapshot()
        self.update_main_page_banner()
        self.set_main_page("home")
        QTimer.singleShot(0, self.sync_crosshair_columns)
        QTimer.singleShot(0, self.sync_window_width_to_frame)
        QTimer.singleShot(0, self.sync_window_height_to_content)

    def setup_ui(self):
        # Container chính (Bo tròn, Gradient nền)
        self.container = QFrame(self)
        self.container.setObjectName("MainContainer")
        self.container.setGeometry(5, 5, 640, 490) # Adjusted for DropShadow
        
        # Đã làm sạch chú thích lỗi mã hóa.
        # Đã làm sạch chú thích lỗi mã hóa.
        # shadow = QGraphicsDropShadowEffect()
        # shadow.setBlurRadius(4) 
        # shadow.setOffset(0, 4)
        # self.container.setGraphicsEffect(shadow)

        
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- TITLE BAR ---
        self.title_bar = QFrame()
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setFixedHeight(30)
        header_layout = QHBoxLayout(self.title_bar)
        header_layout.setContentsMargins(10, 0, 10, 0)
        
        btn_min = QPushButton("-")
        btn_min.setObjectName("MinBtn")
        btn_min.setFixedSize(20, 20)
        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_min.clicked.connect(self.minimize_to_taskbar) 
        
        btn_close = QPushButton("X")
        btn_close.setObjectName("CloseBtn")
        btn_close.setFixedSize(20, 20)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.handle_close_action)
        
        self.app_title_label = QLabel("Macro & Aim By Di88") 
        self.app_title_label.setObjectName("AppTitle")
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(4)
        glow.setColor(QColor(0, 0, 0, 200))  # Đã làm sạch chú thích lỗi mã hóa.
        glow.setOffset(1, 1) 
        self.app_title_label.setGraphicsEffect(glow)

        # Đã làm sạch chú thích lỗi mã hóa.
        self.app_logo = QLabel()
        icon_path = get_resource_path("di88vp.ico")
        logo_icon = QIcon(icon_path)
        self.app_logo.setPixmap(logo_icon.pixmap(22, 22))
        self.app_logo.setContentsMargins(0, 0, 5, 0)

        header_layout.addStretch()
        header_layout.addWidget(self.app_logo)
        header_layout.addWidget(self.app_title_label) 
        header_layout.addStretch()
        header_layout.addWidget(btn_min)
        header_layout.addSpacing(5)
        header_layout.addWidget(btn_close)
        
        # Đã làm sạch chú thích lỗi mã hóa.
        self.title_bar.mousePressEvent = self.mousePressEvent
        self.title_bar.mouseMoveEvent = self.mouseMoveEvent
        
        main_layout.addWidget(self.title_bar)
        
        # --- BODY V-LAYOUT (TOP/BOTTOM) ---
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(5, 5, 5, 5)
        body_layout.setSpacing(10)
        
        # --- 1. TOP UNIFIED BOX (GUNS + SETTINGS) ---
        top_box = QFrame()
        top_box.setObjectName("TopUnifiedBox")
        top_box.setStyleSheet('''
            QFrame#TopUnifiedBox {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
            }
        ''')
        top_layout = QHBoxLayout(top_box)
        top_layout.setContentsMargins(8, 8, 8, 8)
        top_layout.setSpacing(10)
        
        # >>> LEFT PART (GUNS)
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        # Đã làm sạch chú thích lỗi mã hóa.
        left_column.setMinimumWidth(280)
        
        # GUN 1
        self.panel_g1, l_g1 = create_panel("GUN 1", "#FF4444", "P1")
        self.grid_g1 = QGridLayout()
        self.grid_g1.setSpacing(6)
        self.lbl_g1_name = create_data_row(self.grid_g1, 0, "Name")
        self.lbl_g1_scope = create_data_row(self.grid_g1, 1, "Scope")
        self.lbl_g1_grip = create_data_row(self.grid_g1, 2, "Grip")
        self.lbl_g1_muzzle = create_data_row(self.grid_g1, 3, "Muzz")
        l_g1.addLayout(self.grid_g1)
        left_layout.addWidget(self.panel_g1, stretch=1)
        
        # GUN 2
        self.panel_g2, l_g2 = create_panel("GUN 2", "#44FF44", "P2")
        self.grid_g2 = QGridLayout()
        self.grid_g2.setSpacing(6)
        self.lbl_g2_name = create_data_row(self.grid_g2, 0, "Name")
        self.lbl_g2_scope = create_data_row(self.grid_g2, 1, "Scope")
        self.lbl_g2_grip = create_data_row(self.grid_g2, 2, "Grip")
        self.lbl_g2_muzzle = create_data_row(self.grid_g2, 3, "Muzz")
        l_g2.addLayout(self.grid_g2)
        left_layout.addWidget(self.panel_g2, stretch=1)
        
        top_layout.addWidget(left_column, stretch=1)
        
        # >>> VERTICAL SEPARATOR
        v_sep = QFrame()
        v_sep.setFrameShape(QFrame.Shape.VLine)
        v_sep.setStyleSheet("background: #3a3a3a; border: none;")
        top_layout.addWidget(v_sep)
        
        # >>> RIGHT COLUMN (SETTINGS)
        self.group_settings = QWidget()
        self.group_settings.setObjectName("SettingsBox")
        
        settings_layout = QVBoxLayout(self.group_settings)
        settings_layout.setContentsMargins(5, 5, 5, 5)
        settings_layout.setSpacing(10)
        
        lbl_settings_title = QLabel("CÀI ĐẶT CHUNG")
        lbl_settings_title.setStyleSheet("color: #ffffff; font-weight: bold; letter-spacing: 1px;")
        lbl_settings_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_layout.addWidget(lbl_settings_title)
        settings_layout.addSpacing(5)
        
        # Overlay
        row_overlay = QHBoxLayout()
        lbl_overlay = QLabel("Overlay")
        lbl_overlay.setFixedWidth(100)
        lbl_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_overlay.setProperty("class", "SettingLabel")
        self.btn_overlay_key = QPushButton("delete")
        self.btn_overlay_key.setProperty("class", "SettingBtn")
        self.btn_overlay_key.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_overlay_key.setFixedHeight(25)
        self.btn_overlay_key.clicked.connect(lambda: self.start_keybind_listening(self.btn_overlay_key, "overlay_key"))
        
        self.btn_overlay_toggle = QPushButton("ON")
        self.btn_overlay_toggle.setObjectName("OverlayToggleBtn")
        self.btn_overlay_toggle.setProperty("state", "ON")
        self.btn_overlay_toggle.setCheckable(False)
        self.btn_overlay_toggle.clicked.connect(self.toggle_overlay_visibility)
        self.btn_overlay_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_overlay_toggle.setFixedSize(50, 28)
        row_overlay.addWidget(lbl_overlay)
        row_overlay.addWidget(self.btn_overlay_key)
        row_overlay.addSpacing(5)
        row_overlay.addWidget(self.btn_overlay_toggle)
        settings_layout.addLayout(row_overlay)

        # FastLoot
        row_fastloot = QHBoxLayout()
        lbl_fastloot = QLabel("Fast Loot")
        lbl_fastloot.setFixedWidth(100)
        lbl_fastloot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_fastloot.setProperty("class", "SettingLabel")
        self.btn_fastloot_key = QPushButton("caps_lock")
        self.btn_fastloot_key.setProperty("class", "SettingBtn")
        self.btn_fastloot_key.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fastloot_key.setFixedHeight(25)
        self.btn_fastloot_key.clicked.connect(lambda: self.start_keybind_listening(self.btn_fastloot_key, "fast_loot_key"))
        
        self.btn_fastloot_toggle = QPushButton("OFF")
        self.btn_fastloot_toggle.setObjectName("FastLootToggleBtn")
        self.btn_fastloot_toggle.setProperty("state", "OFF")
        self.btn_fastloot_toggle.clicked.connect(self.toggle_fast_loot)
        self.btn_fastloot_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fastloot_toggle.setFixedSize(50, 28)
        row_fastloot.addWidget(lbl_fastloot)
        row_fastloot.addWidget(self.btn_fastloot_key)
        row_fastloot.addSpacing(5)
        row_fastloot.addWidget(self.btn_fastloot_toggle)
        settings_layout.addLayout(row_fastloot)

        # StopKeys
        self.btn_stopkeys = add_setting_row(settings_layout, "STOPKEYS", "X, G, 5")
        self.btn_stopkeys.setEnabled(False)
        self.btn_stopkeys.setCursor(Qt.CursorShape.ArrowCursor)
        
        # ADS Mode
        self.btn_adsmode = add_setting_row(settings_layout, "ADS MODE", "HOLD")
        self.btn_adsmode.setEnabled(False)
        self.btn_adsmode.setCursor(Qt.CursorShape.ArrowCursor)

        # GUI Toggle
        self.btn_guitoggle = add_setting_row(settings_layout, "BẬT/TẮt GUI", "F1")
        self.btn_guitoggle.setEnabled(False)
        self.btn_guitoggle.setCursor(Qt.CursorShape.ArrowCursor)
        
        # Capture Mode
        row_capture = QHBoxLayout()
        lbl_cap = QLabel("CAPTURE")
        lbl_cap.setFixedWidth(100)
        lbl_cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_cap.setProperty("class", "SettingLabel")
        
        self.btn_mode_wgc = QPushButton("DXCAM")
        self.btn_mode_wgc.setObjectName("ModeWgcBtn")
        self.btn_mode_wgc.setProperty("class", "CaptureBtn")
        self.btn_mode_wgc.setFixedSize(65, 25)
        self.btn_mode_wgc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_wgc.clicked.connect(lambda: self.set_capture_mode("DXCAM"))

        self.btn_mode_dxgi = QPushButton("MSS")
        self.btn_mode_dxgi.setObjectName("ModeDxgiBtn")
        self.btn_mode_dxgi.setProperty("class", "CaptureBtn")
        self.btn_mode_dxgi.setFixedSize(65, 25)
        self.btn_mode_dxgi.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_dxgi.clicked.connect(lambda: self.set_capture_mode("MSS"))

        row_capture.addWidget(lbl_cap)
        
        btns_container = QWidget()
        btns_layout = QHBoxLayout(btns_container)
        btns_layout.setContentsMargins(0, 0, 0, 0)
        btns_layout.setSpacing(5)
        btns_layout.addStretch()
        btns_layout.addWidget(self.btn_mode_wgc)
        btns_layout.addWidget(self.btn_mode_dxgi)
        btns_layout.addStretch()
        
        row_capture.addWidget(btns_container)
        settings_layout.addLayout(row_capture)
        
        settings_layout.addSpacing(5)

        
        settings_layout.addStretch()
        top_layout.addWidget(self.group_settings, stretch=1)
        body_layout.addWidget(top_box)
        
        # --- 2. BOTTOM CARDS ROW ---
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(15)
        
        # Left Bottom Card: Tư thế / Macro
        self.footer = QFrame()
        # Đã làm sạch chú thích lỗi mã hóa.
        self.footer.setFixedHeight(115)
        self.footer.setStyleSheet('''
            QFrame {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
            }
        ''')
        f_layout = QVBoxLayout(self.footer)
        f_layout.setSpacing(2)
        f_layout.setContentsMargins(8, 8, 8, 8)

        self.lbl_stance = QLabel("TƯ THẾ: ĐỨNG")
        self.lbl_stance.setObjectName("StanceLabel")
        self.lbl_stance.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_stance.setFixedHeight(30)
        self.lbl_stance.setStyleSheet('''
            QLabel {
                color: #aaaaaa;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
                background: #262626;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
            }
        ''')
        f_layout.addWidget(self.lbl_stance)

        self.btn_macro = QPushButton("MACRO : OFF")
        self.btn_macro.setCursor(Qt.CursorShape.ForbiddenCursor)
        self.btn_macro.setFixedHeight(30)
        self.btn_macro.setStyleSheet('''
            QPushButton {
                color: #ff4444;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 2px;
                background: #1a1010;
                border: 1px solid #441111;
                border-radius: 5px;
            }
        ''')
        self.update_macro_style(False)
        f_layout.addWidget(self.btn_macro)

        bottom_row.addWidget(self.footer)

        # Đã làm sạch chú thích lỗi mã hóa.
        cross_card = QFrame()
        cross_card.setFixedHeight(115)
        cross_card.setStyleSheet('''
            QFrame {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
            }
        ''')
        cross_card_layout = QVBoxLayout(cross_card)
        cross_card_layout.setSpacing(6)
        cross_card_layout.setContentsMargins(10, 8, 10, 8)

        # Đã làm sạch chú thích lỗi mã hóa.
        lbl_cross.setObjectName("CrosshairSectionTitle")
        cross_card_layout.addWidget(lbl_cross)

        row_cross = QHBoxLayout()
        self.btn_cross_toggle = QPushButton("ON")
        self.btn_cross_toggle.setObjectName("CrosshairToggleBtn")
        self.btn_cross_toggle.setProperty("checked", "true")
        self.btn_cross_toggle.setCheckable(True)
        self.btn_cross_toggle.setChecked(True)
        self.btn_cross_toggle.setFixedSize(40, 20)
        self.btn_cross_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cross_toggle.clicked.connect(self.toggle_crosshair)

        self.combo_style = QComboBox()
        self.combo_style.addItems([
            "1: Gap Cross", "2: T-Shape", "3: Circle Dot", "5: Classic",
            "6: Micro Dot", "7: Hollow Box", "8: Cross + Dot", "9: Chevron",
            "10: X-Shape", "11: Diamond", "13: Triangle", "14: Square Dot",
            "17: Bracket Dot", "18: Shuriken", "19: Center Gap", "22: Plus Dot",
            "23: V-Shape", "24: Star"
        ])
        self.combo_style.setCurrentText("Style 1")
        self.combo_style.setFixedHeight(20)
        self.combo_style.currentIndexChanged.connect(self.change_crosshair_style)

        self.combo_color = QComboBox()
        self.combo_color.addItems([
            "Đỏ", "Đỏ Cam", "Cam", "Vàng",
            "Xanh Lá", "Xanh Ngọc", "Xanh Dương",
            "Tím", "Tím Hồng", "Hồng",
            "Trắng", "Bạc"
        ])
        self.combo_color.setCurrentText("Đỏ")
        self.combo_color.setFixedHeight(20)
        self.combo_color.currentIndexChanged.connect(self.change_crosshair_color)

        row_cross.addWidget(self.btn_cross_toggle)
        row_cross.addWidget(self.combo_style)
        row_cross.addWidget(self.combo_color)
        cross_card_layout.addLayout(row_cross)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #3a3a3a; border: none;")
        sep.setFixedHeight(1)
        cross_card_layout.addWidget(sep)

        row_btns = QHBoxLayout()
        btn_default = QPushButton("CÀI ĐẶT GỐC")
        btn_default.setObjectName("DefaultBtn")
        btn_default.setFixedHeight(30)
        btn_default.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_default.clicked.connect(self.reset_to_defaults)

        btn_save = QPushButton("LƯU CÀI ĐẶT")
        btn_save.setObjectName("SaveBtn")
        btn_save.setFixedHeight(30)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self.save_config)

        row_btns.addWidget(btn_default)
        row_btns.addWidget(btn_save)
        cross_card_layout.addLayout(row_btns)

        bottom_row.addWidget(cross_card)
        body_layout.addLayout(bottom_row)
        
        main_layout.addWidget(body_widget)

        
        
        # Load Settings (General)
        self.load_config()
        
        # Load Crosshair Settings
        self.load_crosshair_settings()


    # Đã làm sạch chú thích lỗi mã hóa.
    def toggle_overlay_visibility(self):
        if self.btn_overlay_toggle.text() == "ON":
            self.game_overlay.hide()
            self.btn_overlay_toggle.setText("OFF")
            self.btn_overlay_toggle.setProperty("state", "OFF")
        else:
            self.game_overlay.show()
            self.btn_overlay_toggle.setText("ON")
            self.btn_overlay_toggle.setProperty("state", "ON")
        self.repolish(self.btn_overlay_toggle)

    def toggle_fast_loot(self, checked=None):
        if checked is None:
            checked = self.btn_fastloot_toggle.text() != "ON"
        else:
            checked = bool(checked)

        if checked:
            self.btn_fastloot_toggle.setText("ON")
            self.btn_fastloot_toggle.setProperty("state", "ON")
        else:
            self.btn_fastloot_toggle.setText("OFF")
            self.btn_fastloot_toggle.setProperty("state", "OFF")
        self.repolish(self.btn_fastloot_toggle)
        if hasattr(self, "btn_fastloot_switch") and self.btn_fastloot_switch:
            if self.btn_fastloot_switch.isChecked() != checked:
                self.btn_fastloot_switch.setChecked(checked)
        self.signal_settings_changed.emit()

    def toggle_slide_trick(self, checked=None):
        if checked is None:
            checked = self.btn_slide_toggle.text() != "ON"
        else:
            checked = bool(checked)

        if checked:
            self.btn_slide_toggle.setText("ON")
            self.btn_slide_toggle.setProperty("state", "ON")
        else:
            self.btn_slide_toggle.setText("OFF")
            self.btn_slide_toggle.setProperty("state", "OFF")
        self.repolish(self.btn_slide_toggle)
        if hasattr(self, "btn_slide_switch") and self.btn_slide_switch:
            if self.btn_slide_switch.isChecked() != checked:
                self.btn_slide_switch.setChecked(checked)
        self.signal_settings_changed.emit()

    def toggle_crosshair(self, checked):
        checked = bool(checked)
        self.crosshair.set_active(checked)
        if checked:
            self.crosshair.show()
            self.crosshair.raise_()
            self.btn_cross_toggle.setText("ON")
            self.btn_cross_toggle.setProperty("checked", "true")
        else:
            self.crosshair.hide()
            self.btn_cross_toggle.setText("OFF")
            self.btn_cross_toggle.setProperty("checked", "false")
        self.repolish(self.btn_cross_toggle)
        if hasattr(self, "btn_cross_on") and self.btn_cross_on:
            self.style_capture_button(self.btn_cross_on, checked)
        if hasattr(self, "btn_cross_off") and self.btn_cross_off:
            self.style_capture_button(self.btn_cross_off, not checked)
        if hasattr(self, "btn_crosshair_switch") and self.btn_crosshair_switch:
            if self.btn_crosshair_switch.isChecked() != checked:
                self.btn_crosshair_switch.setChecked(checked)
        self.save_crosshair_settings() # Auto-save


    def change_crosshair_style(self, index):
        style_map = dict(self.crosshair_style_options)
        style = style_map.get(self.combo_style.currentText(), "1: Gap Cross")
        self.crosshair.set_style(style)
        self.save_crosshair_settings() # Auto-save

    def change_crosshair_color(self, index):
        color = self.combo_color.currentText()
        self.crosshair.set_color(color)
        self.save_crosshair_settings() # Auto-save


    # --- KEYBIND LISTENER LOGIC ---
    def start_keybind_listening(self, btn, setting_key):
        self.listening_key = True
        self.target_key_btn = btn
        self.target_key_btn = btn
        self.target_setting_key = setting_key # "fastloot"
        # Store previous text to revert on cancel
        self.temp_original_text = btn.text()
        
        btn.setText("PRESS KEY...")
        btn.setStyleSheet("background-color: #FF00FF; color: white; border: 1px solid #fff;")
        self.setFocus() # Ensure Window gets key events

    def finish_keybind_capture(self, key_name):
        if not self.target_key_btn:
            return

        display_key = key_name.upper()
        if key_name == "right":
            display_key = "RIGHT MOUSE"
        elif key_name == "left":
            display_key = "LEFT MOUSE"
        elif self.target_setting_key == "aim_secondary_key" and key_name == "ctrl":
            display_key = "LEFT CTRL"
        self.target_key_btn.setText(display_key)
        self.target_key_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a; color: #ccc; 
                border: 1px solid #444; border-radius: 4px; font-size: 11px;
            }
            QPushButton:hover { border: 1px solid #666; background-color: #333; }
        """)

        if self.target_setting_key == "gui_toggle":
            self.temp_guitoggle_value = key_name
        elif self.target_setting_key == "overlay_key":
            self.temp_overlay_key_value = key_name
        elif self.target_setting_key == "fast_loot_key":
            self.temp_fast_loot_key_value = key_name
        elif self.target_setting_key == "crosshair_toggle_key":
            self.temp_crosshair_toggle_key_value = key_name
            self.save_crosshair_settings()
            self.signal_settings_changed.emit()
        elif self.target_setting_key == "aim_emergency_stop_key":
            self.temp_aim_emergency_key_value = key_name
        elif self.target_setting_key == "aim_primary_key":
            self.temp_aim_primary_key_value = key_name
        elif self.target_setting_key == "aim_secondary_key":
            self.temp_aim_secondary_key_value = key_name
        elif self.target_setting_key == "aim_trigger_key":
            self.temp_aim_trigger_key_value = key_name

        if self.target_setting_key in {"gui_toggle", "fast_loot_key"}:
            self.signal_settings_changed.emit()

        self.listening_key = False
        self.target_key_btn = None
        self.temp_original_text = None

    def keyPressEvent(self, event):
        # 1. Handle Keybind Listening
        if self.listening_key and self.target_key_btn:
            key = event.key()
            
            # Convert Qt Key to Pynput/Win32 friendly string
            key_name = QKeySequence(key).toString().lower()
            
            # Special mapping for Common Keys
            if key == Qt.Key.Key_CapsLock: key_name = "caps_lock"
            elif key == Qt.Key.Key_Shift: key_name = "shift"
            elif key == Qt.Key.Key_Control: key_name = "ctrl"
            elif key == Qt.Key.Key_Alt: key_name = "alt"
            
            # CLEAR KEY (Escape / Backspace / Delete) -> NONE
            elif key == Qt.Key.Key_Escape or key == Qt.Key.Key_Backspace or key == Qt.Key.Key_Delete:
                key_name = "NONE"

            self.finish_keybind_capture(key_name)
            return

        else:
            super().keyPressEvent(event)


    def eventFilter(self, obj, event):
        """Global Event Filter to handle clicking away"""
        if hasattr(self, 'hover_hint_targets') and obj in self.hover_hint_targets:
            anchor, text = self.hover_hint_targets[obj]
            if event.type() == QEvent.Type.Enter:
                enter_pos = event.position().toPoint() if hasattr(event, "position") else anchor.rect().bottomLeft()
                self.show_hover_hint(anchor, text)
                self._move_hover_hint(anchor, enter_pos)
            elif event.type() == QEvent.Type.MouseMove:
                move_pos = event.position().toPoint() if hasattr(event, "position") else None
                self._move_hover_hint(anchor, move_pos)
            elif event.type() == QEvent.Type.Leave:
                self.hide_hover_hint()

        if getattr(self, "listening_key", False) and event.type() == QEvent.Type.MouseButtonPress:
            target_key_btn = getattr(self, "target_key_btn", None)
            if target_key_btn and target_key_btn.underMouse():
                return super().eventFilter(obj, event)

            button_map = {
                Qt.MouseButton.LeftButton: "left",
                Qt.MouseButton.RightButton: "right",
                Qt.MouseButton.MiddleButton: "middle",
                Qt.MouseButton.XButton1: "xbutton1",
                Qt.MouseButton.XButton2: "xbutton2",
            }
            key_name = button_map.get(event.button())
            if key_name:
                self.finish_keybind_capture(key_name)
                return True

            self.cancel_listening()
            
        return super().eventFilter(obj, event)

    def cancel_listening(self):
        """Helper to cancel listening state"""
        if not self.listening_key: return
        
        if self.target_key_btn:
            # Revert Text (UPPERCASE!)
            if hasattr(self, 'temp_original_text') and self.temp_original_text:
                self.target_key_btn.setText(self.temp_original_text.upper())
            else:
                self.target_key_btn.setText("CAPS_LOCK")
                
            # Revert Style
            self.target_key_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a; color: #ccc; 
                    border: 1px solid #444; border-radius: 4px; font-size: 11px;
                }
                QPushButton:hover { border: 1px solid #666; background-color: #333; }
            """)
            
        self.listening_key = False
        self.target_key_btn = None
        self.temp_original_text = None
            
    def load_config(self):
        """Load settings from settings.json"""
        try:
            settings = self.settings_manager.load()
            
            # Load Mouse Mode (Legacy Support / Hidden)
            # mouse_mode = settings.get("mouse_mode", "Win32")
            # Default Win32 (No UI)
            
            # Load GUI Toggle Key
            gui_toggle_key = "F1"  # Default
            if "keybinds" in settings and isinstance(settings["keybinds"], dict):
                gui_toggle_key = settings["keybinds"].get("gui_toggle", "f1")
            
            self.btn_guitoggle.setText(gui_toggle_key.upper())

            # Load ADS Mode
            ads_mode = settings.get("ads_mode", "HOLD")
            self.btn_adsmode.setText(ads_mode.upper())
            self.update_ads_status_style(ads_mode.upper())

            # Load Capture Mode
            cap_mode = settings.get("capture_mode", "DXGI")
            self.set_capture_mode_ui(cap_mode.upper())

            # Load FastLoot
            fast_loot = settings.get("fast_loot", True)
            self.btn_fastloot_toggle.setText("ON" if fast_loot else "OFF")
            self.btn_fastloot_toggle.setProperty("state", "ON" if fast_loot else "OFF")
            self.repolish(self.btn_fastloot_toggle)
            if hasattr(self, "btn_fastloot_switch") and self.btn_fastloot_switch:
                self.btn_fastloot_switch.setChecked(fast_loot)

            slide_trick = settings.get("slide_trick", True)
            self.btn_slide_toggle.setText("ON" if slide_trick else "OFF")
            self.btn_slide_toggle.setProperty("state", "ON" if slide_trick else "OFF")
            self.repolish(self.btn_slide_toggle)
            if hasattr(self, "btn_slide_switch") and self.btn_slide_switch:
                self.btn_slide_switch.setChecked(slide_trick)
            
            fl_key = settings.get("fast_loot_key", "caps_lock")
            self.btn_fastloot_key.setText(fl_key.upper())

            ov_key = settings.get("overlay_key", "delete")
            self.btn_overlay_key.setText(ov_key.upper())

            scope_intensity = settings.get("scope_intensity", {})
            for scope_key, _ in getattr(self, "scope_order", []):
                value = int(scope_intensity.get(scope_key, 100))
                value = max(50, min(150, value))
                if scope_key in self.scope_sliders:
                    self.scope_sliders[scope_key].setValue(value)
                    self.update_scope_intensity_label(scope_key, value)

            aim_settings = settings.get("aim", {}) if isinstance(settings.get("aim", {}), dict) else {}
            aim_runtime = aim_settings.get("runtime", {}) if isinstance(aim_settings.get("runtime", {}), dict) else {}
            aim_meta = aim_settings.get("meta", {}) if isinstance(aim_settings.get("meta", {}), dict) else {}
            aim_bindings = aim_settings.get("bindings", {}) if isinstance(aim_settings.get("bindings", {}), dict) else {}
            aim_sliders = aim_settings.get("sliders", {}) if isinstance(aim_settings.get("sliders", {}), dict) else {}
            aim_toggles = aim_settings.get("toggles", {}) if isinstance(aim_settings.get("toggles", {}), dict) else {}
            aim_dropdowns = aim_settings.get("dropdowns", {}) if isinstance(aim_settings.get("dropdowns", {}), dict) else {}
            aim_colors = aim_settings.get("colors", {}) if isinstance(aim_settings.get("colors", {}), dict) else {}
            aim_file_locations = aim_settings.get("file_locations", {}) if isinstance(aim_settings.get("file_locations", {}), dict) else {}
            aim_minimize = aim_settings.get("minimize", {}) if isinstance(aim_settings.get("minimize", {}), dict) else {}
            aim_capture_mode = str(
                aim_runtime.get("capture_backend")
                or aim_dropdowns.get("Screen Capture Method")
                or "DirectX"
            )
            self.set_aim_capture_mode_ui(aim_capture_mode)
            if hasattr(self, "combo_aim_target_priority") and self.combo_aim_target_priority:
                priority_text = str(aim_dropdowns.get("Target Priority", "Body -> Head"))
                if priority_text not in ("Body -> Head", "Head -> Body"):
                    priority_text = "Body -> Head"
                self.combo_aim_target_priority.setCurrentText(priority_text)
            selected_model = (
                aim_runtime.get("model")
                or aim_meta.get("last_loaded_model")
                or ""
            )
            if str(selected_model).upper() == "N/A":
                selected_model = ""
            self.refresh_aim_model_list(str(selected_model))
            if hasattr(self, "aim_btn_primary") and self.aim_btn_primary:
                primary_key = str(aim_bindings.get("Aim Keybind", "right")).upper()
                self.aim_btn_primary.setText("RIGHT MOUSE" if primary_key == "RIGHT" else primary_key)
            if hasattr(self, "aim_btn_secondary") and self.aim_btn_secondary:
                secondary_key = str(aim_bindings.get("Second Aim Keybind", "ctrl")).upper()
                self.aim_btn_secondary.setText("LEFT CTRL" if secondary_key in ("LMENU", "LCONTROL", "CTRL") else secondary_key)
            if hasattr(self, "aim_btn_trigger") and self.aim_btn_trigger:
                self.aim_btn_trigger.setText(str(aim_bindings.get("Toggle Trigger Keybind", "f7")).upper())
            if hasattr(self, "aim_btn_emergency_stop") and self.aim_btn_emergency_stop:
                self.aim_btn_emergency_stop.setText(str(aim_bindings.get("Emergency Stop Keybind", "f8")).upper())
            if hasattr(self, "aim_slider_fov") and self.aim_slider_fov:
                fov_value = int(aim_sliders.get("FOV Size", 300))
                fov_value = max(10, min(640, fov_value))
                self.aim_slider_fov.setValue(fov_value)
                self.update_aim_fov_label(fov_value)
            if hasattr(self, "aim_slider_confidence") and self.aim_slider_confidence:
                confidence_value = int(aim_sliders.get("AI Minimum Confidence", 45))
                confidence_value = max(1, min(100, confidence_value))
                self.aim_slider_confidence.setValue(confidence_value)
                self.update_aim_confidence_label(confidence_value)
            if hasattr(self, "aim_slider_trigger_delay") and self.aim_slider_trigger_delay:
                raw_delay = aim_sliders.get("Auto Trigger Delay", 0.1)
                delay_ms = int(round(float(raw_delay) * 1000)) if float(raw_delay) <= 1.0 else int(round(float(raw_delay)))
                delay_ms = max(10, min(1000, delay_ms))
                self.aim_slider_trigger_delay.setValue(delay_ms)
                self.update_aim_trigger_delay_label(delay_ms)
            if hasattr(self, "aim_slider_capture_fps") and self.aim_slider_capture_fps:
                capture_fps_value = int(round(float(aim_sliders.get("Capture FPS", 144))))
                capture_fps_value = max(1, min(240, capture_fps_value))
                self.aim_slider_capture_fps.setValue(capture_fps_value)
                self.update_aim_capture_fps_label(capture_fps_value)
            if hasattr(self, "aim_slider_primary_position") and self.aim_slider_primary_position:
                primary_position_value = int(round(float(aim_sliders.get("Primary Aim Position", 50))))
                primary_position_value = max(0, min(100, primary_position_value))
                self.aim_slider_primary_position.setValue(primary_position_value)
                self.update_aim_primary_position_label(primary_position_value)
            if hasattr(self, "aim_slider_secondary_position") and self.aim_slider_secondary_position:
                secondary_position_value = int(round(float(aim_sliders.get("Secondary Aim Position", 50))))
                secondary_position_value = max(0, min(100, secondary_position_value))
                self.aim_slider_secondary_position.setValue(secondary_position_value)
                self.update_aim_secondary_position_label(secondary_position_value)
            if hasattr(self, "aim_slider_sensitivity") and self.aim_slider_sensitivity:
                sensitivity_value = float(aim_sliders.get("Mouse Sensitivity (+/-)", 0.80))
                sensitivity_slider = max(1, min(100, int(round(sensitivity_value * 100.0))))
                self.aim_slider_sensitivity.setValue(sensitivity_slider)
                self.update_aim_sensitivity_label(sensitivity_slider)
            if hasattr(self, "aim_slider_ema") and self.aim_slider_ema:
                ema_value = float(aim_sliders.get("EMA Smoothening", 0.50))
                ema_slider = max(1, min(100, int(round(ema_value * 100.0))))
                self.aim_slider_ema.setValue(ema_slider)
                self.update_aim_ema_label(ema_slider)
            if hasattr(self, "aim_slider_dynamic_fov") and self.aim_slider_dynamic_fov:
                dynamic_fov_value = int(round(float(aim_sliders.get("Dynamic FOV Size", 10))))
                dynamic_fov_value = max(10, min(640, dynamic_fov_value))
                self.aim_slider_dynamic_fov.setValue(dynamic_fov_value)
                self.update_aim_dynamic_fov_label(dynamic_fov_value)
            if hasattr(self, "aim_slider_sticky_threshold") and self.aim_slider_sticky_threshold:
                sticky_threshold_value = int(round(float(aim_sliders.get("Sticky Aim Threshold", 0))))
                sticky_threshold_value = max(0, min(100, sticky_threshold_value))
                self.aim_slider_sticky_threshold.setValue(sticky_threshold_value)
                self.update_aim_sticky_threshold_label(sticky_threshold_value)
            if hasattr(self, "aim_slider_jitter") and self.aim_slider_jitter:
                jitter_value = int(aim_sliders.get("Mouse Jitter", 4))
                jitter_value = max(0, min(15, jitter_value))
                self.aim_slider_jitter.setValue(jitter_value)
                self.update_aim_jitter_label(jitter_value)
            self.load_aim_listing_sliders(aim_sliders)
            if hasattr(self, "aim_chk_show_fov") and self.aim_chk_show_fov:
                self.aim_chk_show_fov.setChecked(bool(aim_toggles.get("Show FOV", True)))
            if hasattr(self, "aim_chk_show_detect") and self.aim_chk_show_detect:
                self.aim_chk_show_detect.setChecked(bool(aim_toggles.get("Show Detected Player", False)))
            self.load_aim_toggle_controls(aim_toggles)
            self.load_aim_dropdown_controls(aim_dropdowns)
            self.load_aim_color_controls(aim_colors)
            self.load_aim_file_controls(aim_file_locations)
            self.load_aim_minimize_controls(aim_minimize)
            current_model = ""
            if hasattr(self, "combo_aim_model") and self.combo_aim_model and self.combo_aim_model.isEnabled():
                current_model = self.combo_aim_model.currentText().strip()
        except Exception as e:
            print(f"[ERROR] Failed to load config: {e}")

    def set_capture_mode(self, mode):
        self.set_capture_mode_ui(mode)
        try:
            self.settings_manager.set("capture_mode", getattr(self, "current_capture_mode", "DXGI"))
            self.settings_manager.save()
        except Exception:
            pass
        try:
            if getattr(self, "backend", None) is not None and hasattr(self.backend, "apply_capture_mode"):
                self.backend.apply_capture_mode(getattr(self, "current_capture_mode", "DXGI"))
        except Exception:
            pass

    def set_capture_mode_ui(self, mode):
        raw_mode = str(mode or "DXGI").strip()
        mode_upper = raw_mode.upper()
        mode_map = {
            "DXCAM": "DXCAM",
            "DIRECTX": "DXCAM",
            "DXGI": "DXGI",
            "MSS": "MSS",
            "NATIVE": "DXGI",
            "GDI": "MSS",
            "GDI+": "MSS",
            "PIL": "MSS",
            "AUTO": "DXGI",
        }
        mode = mode_map.get(mode_upper, "DXGI")
        self.current_capture_mode = mode
        if hasattr(self, "lbl_capture_mode_auto") and self.lbl_capture_mode_auto:
            self.lbl_capture_mode_auto.setText(mode)
        if hasattr(self, "btn_capture_native") and self.btn_capture_native:
            self.style_capture_button(self.btn_capture_native, mode == "DXGI")
        if hasattr(self, "btn_capture_dxcam") and self.btn_capture_dxcam:
            self.style_capture_button(self.btn_capture_dxcam, mode == "DXCAM")
        if hasattr(self, "btn_capture_mss") and self.btn_capture_mss:
            self.style_capture_button(self.btn_capture_mss, mode == "MSS")
        if hasattr(self, "btn_mode_wgc") and self.btn_mode_wgc:
            self.btn_mode_wgc.setProperty("active", "true" if mode == "DXCAM" else "false")
            self.repolish(self.btn_mode_wgc)
        if hasattr(self, "btn_mode_dxgi") and self.btn_mode_dxgi:
            self.btn_mode_dxgi.setProperty("active", "true" if mode == "MSS" else "false")
            self.repolish(self.btn_mode_dxgi)
        if hasattr(self, "lbl_aim_runtime_meta") and self.lbl_aim_runtime_meta:
            backend_text = "Chưa nạp"
            runtime_source = ""
            if hasattr(self, "last_data") and isinstance(self.last_data, dict):
                runtime_source = str(self.last_data.get("aim", {}).get("runtime_source", "") or "")
            if hasattr(self, "lbl_aim_backend_info") and self.lbl_aim_backend_info:
                backend_text = self.lbl_aim_backend_info.text().replace("Backend:", "").strip() or backend_text
            self.lbl_aim_runtime_meta.setText(self._format_aim_backend_meta_text(backend_text, runtime_source))
        self.update_home_snapshot()

    def set_aim_capture_mode(self, mode):
        self.set_aim_capture_mode_ui(mode)

    def set_aim_capture_mode_ui(self, mode):
        raw_mode = str(mode or "DirectX").strip()
        mode_upper = raw_mode.upper()
        mode_map = {
            "DIRECTX": "DirectX",
            "DXCAM": "DirectX",
            "GDI+": "GDI+",
            "MSS": "GDI+",
            "PIL": "GDI+",
        }
        mode = mode_map.get(mode_upper, "DirectX")
        self.current_aim_capture_mode = mode
        if hasattr(self, "combo_aim_capture") and self.combo_aim_capture:
            target_index = self.combo_aim_capture.findText(mode)
            if target_index >= 0 and self.combo_aim_capture.currentIndex() != target_index:
                self.combo_aim_capture.blockSignals(True)
                self.combo_aim_capture.setCurrentIndex(target_index)
                self.combo_aim_capture.blockSignals(False)
        if hasattr(self, "lbl_aim_runtime_meta") and self.lbl_aim_runtime_meta:
            backend_text = "Chưa nạp"
            runtime_source = ""
            if hasattr(self, "last_data") and isinstance(self.last_data, dict):
                runtime_source = str(self.last_data.get("aim", {}).get("runtime_source", "") or "")
            if hasattr(self, "lbl_aim_backend_info") and self.lbl_aim_backend_info:
                backend_text = self.lbl_aim_backend_info.text().replace("Backend:", "").strip() or backend_text
            self.lbl_aim_runtime_meta.setText(self._format_aim_backend_meta_text(backend_text, runtime_source))
        self.update_home_snapshot()

    def cycle_ads_mode(self):
        current = self.btn_adsmode.text().strip().upper()

        if current == "HOLD":
            new_mode = "CLICK"
        else:
            new_mode = "HOLD"

        self.btn_adsmode.setText(new_mode)
        self.update_ads_status_style(new_mode)
        self.crosshair.set_ads_mode(new_mode)
        self.save_crosshair_settings()

    def load_crosshair_settings(self):
        try:
            data = self.settings_manager.get("crosshair", {})
            is_on = data.get("active", False)
            self.btn_cross_toggle.setChecked(is_on)
            self.toggle_crosshair(is_on)
            if is_on:
                self.crosshair.show()
                self.crosshair.raise_()
            style = data.get("style", "10: X-Shape")
            display_names = [display for display, internal in self.crosshair_style_options if internal == style]
            display_name = display_names[0] if display_names else "Chữ Thập Hở"
            idx = self.combo_style.findText(display_name)
            self.combo_style.setCurrentIndex(idx if idx >= 0 else 0)
            self.crosshair.set_style(style)
            saved_color_idx = data.get("color_index", None)
            if saved_color_idx is None:
                saved_color_name = data.get("color", "Đỏ")
                idx = self.combo_color.findText(saved_color_name)
                saved_color_idx = idx if idx >= 0 else 0
            self.combo_color.setCurrentIndex(saved_color_idx)
            self.change_crosshair_color(saved_color_idx)
            ads_mode = data.get("ads_mode", "HOLD")
            if hasattr(self, "btn_adsmode") and self.btn_adsmode: self.btn_adsmode.setText(ads_mode)
            self.update_ads_status_style(ads_mode)
            self.crosshair.set_ads_mode(ads_mode)
            toggle_key = data.get("toggle_key", "none")
            if hasattr(self, 'btn_cross_bind') and self.btn_cross_bind: self.btn_cross_bind.setText(toggle_key.upper())
        except Exception as e: print(f"[ERROR] Load Crosshair failed: {e}")

    def save_crosshair_settings(self):
        try:
            is_active = self.btn_cross_toggle.isChecked()
            style_map = dict(self.crosshair_style_options)
            style_val = style_map.get(self.combo_style.currentText(), "10: X-Shape")
            color_idx = self.combo_color.currentIndex()
            color_name = self.combo_color.itemText(color_idx) if color_idx >= 0 else "Đỏ"
            toggle_key = getattr(self, "temp_crosshair_toggle_key_value", None) or (self.btn_cross_bind.text().lower() if hasattr(self, 'btn_cross_bind') else "none")
            if hasattr(self, "btn_adsmode") and self.btn_adsmode: ads_mode = self.btn_adsmode.text().strip().upper() or "HOLD"
            elif hasattr(self, "lbl_ads_status") and self.lbl_ads_status: ads_mode = self.lbl_ads_status.text().replace("ADS :", "").strip().upper() or "HOLD"
            else: ads_mode = "HOLD"
            data = {"active": is_active, "style": style_val, "color": color_name, "color_index": color_idx, "toggle_key": toggle_key, "ads_mode": ads_mode}
            self.settings_manager.set("crosshair", data)
        except Exception as e: print(f"[ERROR] Save Crosshair failed: {e}")

    def reset_to_defaults(self):
        """Reset all settings to project defaults and update UI"""
        confirmed = AppNoticeDialog.question(
            self,
            "Xác Nhận Cài Đặt Gốc",
            "Bạn có chắc chắn muốn đặt lại toàn bộ cài đặt về mặc định không?\n(Lưu ý: Hành động này không thể hoàn tác)"
        )
        if not confirmed:
            return
        
        try:
            # 1. Reset settings.json về mặc định
            defaults = self.settings_manager.reset_to_defaults()
            self.settings_manager._cache = None  # Force reload
            
            # 2. Reset Keybinds UI
            kb = defaults.get('keybinds', {})
            if hasattr(self, 'btn_guitoggle') and self.btn_guitoggle:
                self.btn_guitoggle.setText(kb.get('gui_toggle', 'f1').upper())
            
            # 3. Reset ADS Mode button
            ads_mode = defaults.get('ads_mode', 'HOLD')
            if hasattr(self, 'btn_adsmode') and self.btn_adsmode:
                self.btn_adsmode.setText(ads_mode)
                self.update_ads_status_style(ads_mode)

            # 3.5 Reset Capture Mode button
            cap_mode = defaults.get('capture_mode', 'DXGI')
            self.set_capture_mode_ui(cap_mode)

            # 4. Reset Crosshair UI
            cr = defaults.get('crosshair', {})
            if hasattr(self, 'combo_style') and self.combo_style:
                style = cr.get('style', '10: X-Shape')
                display_names = [display for display, internal in self.crosshair_style_options if internal == style]
                idx = self.combo_style.findText(display_names[0] if display_names else "Chữ Thập Hở")
                self.combo_style.setCurrentIndex(max(0, idx))
            if hasattr(self, 'combo_color') and self.combo_color:
                color_index = cr.get('color_index', None)
                if isinstance(color_index, int) and 0 <= color_index < self.combo_color.count():
                    self.combo_color.setCurrentIndex(color_index)
                else:
                    color_name = cr.get('color', 'Trắng')
                    idx = self.combo_color.findText(color_name)
                    self.combo_color.setCurrentIndex(idx if idx >= 0 else 10)
            ads_cross = cr.get('ads_mode', 'HOLD')
            if hasattr(self, 'btn_adsmode') and self.btn_adsmode:
                self.btn_adsmode.setText(ads_cross)
            self.update_ads_status_style(ads_cross)
            if hasattr(self, 'btn_cross_toggle') and self.btn_cross_toggle:
                self.btn_cross_toggle.setChecked(cr.get('active', True))
            if hasattr(self, 'btn_cross_bind') and self.btn_cross_bind:
                self.btn_cross_bind.setText(cr.get('toggle_key', 'none').upper())
            if hasattr(self, 'crosshair') and self.crosshair:
                self.crosshair.set_style(cr.get('style', '10: X-Shape'))
                self.crosshair.set_color(cr.get('color', 'Trắng'))
                self.crosshair.set_ads_mode(cr.get('ads_mode', 'HOLD'))

            for scope_key, _ in getattr(self, "scope_order", []):
                if scope_key in self.scope_sliders:
                    self.scope_sliders[scope_key].setValue(100)
                    self.update_scope_intensity_label(scope_key, 100)

            aim_defaults = defaults.get("aim", {}) if isinstance(defaults.get("aim", {}), dict) else {}
            aim_runtime = aim_defaults.get("runtime", {}) if isinstance(aim_defaults.get("runtime", {}), dict) else {}
            aim_meta = aim_defaults.get("meta", {}) if isinstance(aim_defaults.get("meta", {}), dict) else {}
            aim_bindings = aim_defaults.get("bindings", {}) if isinstance(aim_defaults.get("bindings", {}), dict) else {}
            aim_sliders = aim_defaults.get("sliders", {}) if isinstance(aim_defaults.get("sliders", {}), dict) else {}
            aim_toggles = aim_defaults.get("toggles", {}) if isinstance(aim_defaults.get("toggles", {}), dict) else {}
            aim_dropdowns = aim_defaults.get("dropdowns", {}) if isinstance(aim_defaults.get("dropdowns", {}), dict) else {}
            aim_colors = aim_defaults.get("colors", {}) if isinstance(aim_defaults.get("colors", {}), dict) else {}
            aim_file_locations = aim_defaults.get("file_locations", {}) if isinstance(aim_defaults.get("file_locations", {}), dict) else {}
            aim_minimize = aim_defaults.get("minimize", {}) if isinstance(aim_defaults.get("minimize", {}), dict) else {}
            aim_capture_mode = str(
                aim_runtime.get("capture_backend")
                or aim_dropdowns.get("Screen Capture Method")
                or "DirectX"
            )
            self.set_aim_capture_mode_ui(aim_capture_mode)
            if hasattr(self, "combo_aim_target_priority") and self.combo_aim_target_priority:
                priority_text = str(aim_dropdowns.get("Target Priority", "Body -> Head"))
                if priority_text not in ("Body -> Head", "Head -> Body"):
                    priority_text = "Body -> Head"
                self.combo_aim_target_priority.setCurrentText(priority_text)
            selected_model = aim_runtime.get("model") or aim_meta.get("last_loaded_model") or ""
            if str(selected_model).upper() == "N/A":
                selected_model = ""
            self.refresh_aim_model_list(str(selected_model))
            if hasattr(self, "aim_btn_primary") and self.aim_btn_primary:
                primary_key = str(aim_bindings.get("Aim Keybind", "Right")).upper()
                self.aim_btn_primary.setText("RIGHT MOUSE" if primary_key == "RIGHT" else primary_key)
            if hasattr(self, "aim_btn_secondary") and self.aim_btn_secondary:
                secondary_key = str(aim_bindings.get("Second Aim Keybind", "ctrl")).upper()
                self.aim_btn_secondary.setText("LEFT CTRL" if secondary_key in ("LMENU", "LCONTROL", "CTRL") else secondary_key)
            if hasattr(self, "aim_btn_trigger") and self.aim_btn_trigger:
                self.aim_btn_trigger.setText(str(aim_bindings.get("Toggle Trigger Keybind", "F7")).upper())
            if hasattr(self, "aim_btn_emergency_stop") and self.aim_btn_emergency_stop:
                self.aim_btn_emergency_stop.setText(str(aim_bindings.get("Emergency Stop Keybind", "F8")).upper())
            if hasattr(self, "aim_slider_fov") and self.aim_slider_fov:
                fov_value = int(aim_sliders.get("FOV Size", 300))
                fov_value = max(10, min(640, fov_value))
                self.aim_slider_fov.setValue(fov_value)
                self.update_aim_fov_label(fov_value)
            if hasattr(self, "aim_slider_confidence") and self.aim_slider_confidence:
                confidence_value = int(aim_sliders.get("AI Minimum Confidence", 45))
                confidence_value = max(1, min(100, confidence_value))
                self.aim_slider_confidence.setValue(confidence_value)
                self.update_aim_confidence_label(confidence_value)
            if hasattr(self, "aim_slider_trigger_delay") and self.aim_slider_trigger_delay:
                raw_delay = aim_sliders.get("Auto Trigger Delay", 0.1)
                delay_ms = int(round(float(raw_delay) * 1000)) if float(raw_delay) <= 1.0 else int(round(float(raw_delay)))
                delay_ms = max(10, min(1000, delay_ms))
                self.aim_slider_trigger_delay.setValue(delay_ms)
                self.update_aim_trigger_delay_label(delay_ms)
            if hasattr(self, "aim_slider_capture_fps") and self.aim_slider_capture_fps:
                capture_fps_value = int(round(float(aim_sliders.get("Capture FPS", 144))))
                capture_fps_value = max(1, min(240, capture_fps_value))
                self.aim_slider_capture_fps.setValue(capture_fps_value)
                self.update_aim_capture_fps_label(capture_fps_value)
            if hasattr(self, "aim_slider_primary_position") and self.aim_slider_primary_position:
                primary_position_value = int(round(float(aim_sliders.get("Primary Aim Position", 50))))
                primary_position_value = max(0, min(100, primary_position_value))
                self.aim_slider_primary_position.setValue(primary_position_value)
                self.update_aim_primary_position_label(primary_position_value)
            if hasattr(self, "aim_slider_secondary_position") and self.aim_slider_secondary_position:
                secondary_position_value = int(round(float(aim_sliders.get("Secondary Aim Position", 50))))
                secondary_position_value = max(0, min(100, secondary_position_value))
                self.aim_slider_secondary_position.setValue(secondary_position_value)
                self.update_aim_secondary_position_label(secondary_position_value)
            if hasattr(self, "aim_slider_sensitivity") and self.aim_slider_sensitivity:
                sensitivity_value = float(aim_sliders.get("Mouse Sensitivity (+/-)", 0.80))
                sensitivity_slider = max(1, min(100, int(round(sensitivity_value * 100.0))))
                self.aim_slider_sensitivity.setValue(sensitivity_slider)
                self.update_aim_sensitivity_label(sensitivity_slider)
            if hasattr(self, "aim_slider_ema") and self.aim_slider_ema:
                ema_value = float(aim_sliders.get("EMA Smoothening", 0.50))
                ema_slider = max(1, min(100, int(round(ema_value * 100.0))))
                self.aim_slider_ema.setValue(ema_slider)
                self.update_aim_ema_label(ema_slider)
            if hasattr(self, "aim_slider_dynamic_fov") and self.aim_slider_dynamic_fov:
                dynamic_fov_value = int(round(float(aim_sliders.get("Dynamic FOV Size", 10))))
                dynamic_fov_value = max(10, min(640, dynamic_fov_value))
                self.aim_slider_dynamic_fov.setValue(dynamic_fov_value)
                self.update_aim_dynamic_fov_label(dynamic_fov_value)
            if hasattr(self, "aim_slider_sticky_threshold") and self.aim_slider_sticky_threshold:
                sticky_threshold_value = int(round(float(aim_sliders.get("Sticky Aim Threshold", 0))))
                sticky_threshold_value = max(0, min(100, sticky_threshold_value))
                self.aim_slider_sticky_threshold.setValue(sticky_threshold_value)
                self.update_aim_sticky_threshold_label(sticky_threshold_value)
            if hasattr(self, "aim_slider_jitter") and self.aim_slider_jitter:
                jitter_value = int(aim_sliders.get("Mouse Jitter", 4))
                jitter_value = max(0, min(15, jitter_value))
                self.aim_slider_jitter.setValue(jitter_value)
                self.update_aim_jitter_label(jitter_value)
            self.load_aim_listing_sliders(aim_sliders)
            if hasattr(self, "aim_chk_show_fov") and self.aim_chk_show_fov:
                self.aim_chk_show_fov.setChecked(bool(aim_toggles.get("Show FOV", True)))
            if hasattr(self, "aim_chk_show_detect") and self.aim_chk_show_detect:
                self.aim_chk_show_detect.setChecked(bool(aim_toggles.get("Show Detected Player", False)))
            self.load_aim_toggle_controls(aim_toggles)
            self.load_aim_dropdown_controls(aim_dropdowns)
            self.load_aim_color_controls(aim_colors)
            self.load_aim_file_controls(aim_file_locations)
            self.load_aim_minimize_controls(aim_minimize)
            self.temp_aim_primary_key_value = None
            self.temp_aim_secondary_key_value = None
            self.temp_aim_trigger_key_value = None
            self.temp_aim_emergency_key_value = None


            self.play_action_beep("reset")
            self.show_bottom_action_status("Đã đưa cấu hình về mặc định.", tone="success")
        except Exception as e:
            print(f'[ERROR] reset_to_defaults failed: {e}')
            self.show_bottom_action_status("Reset thất bại.", tone="error", auto_hide_ms=3000)

    def save_config(self):
        """Manually Save All Settings (Triggered by Button)"""
        try:
            
            # 2. GUI Toggle Key (use temp value if changed, otherwise button text)
            if self.temp_guitoggle_value:
                guitoggle_key = self.temp_guitoggle_value
                self.temp_guitoggle_value = None  # Clear temp after saving
            else:
                guitoggle_key = self.btn_guitoggle.text().lower()
            
            capture_mode = getattr(self, 'current_capture_mode', 'DXGI')
            aim_capture_mode = getattr(self, 'current_aim_capture_mode', 'DirectX')
                
            # Construct Data
            current_settings = self.settings_manager.load()
            
            # Update Keybinds (Standard Path)
            if "keybinds" not in current_settings or not isinstance(current_settings["keybinds"], dict):
                current_settings["keybinds"] = {}
            
            current_settings["keybinds"]["gui_toggle"] = guitoggle_key.lower()
            current_settings["capture_mode"] = capture_mode
            aim_settings = current_settings.setdefault("aim", {})
            aim_runtime = aim_settings.setdefault("runtime", {})
            aim_dropdowns = aim_settings.setdefault("dropdowns", {})
            aim_runtime["capture_backend"] = aim_capture_mode
            aim_dropdowns["Screen Capture Method"] = aim_capture_mode
            aim_dropdowns["Target Priority"] = (
                self.combo_aim_target_priority.currentText()
                if hasattr(self, "combo_aim_target_priority") and self.combo_aim_target_priority
                else "Body -> Head"
            )
            
            # Fast Loot
            if self.temp_fast_loot_key_value:
                current_settings["fast_loot_key"] = self.temp_fast_loot_key_value
                self.temp_fast_loot_key_value = None
            else:
                current_settings["fast_loot_key"] = self.btn_fastloot_key.text().lower()
            current_settings["fast_loot"] = self.btn_fastloot_toggle.text().upper() == "ON"
            current_settings["slide_trick"] = self.btn_slide_toggle.text().upper() == "ON"

            # Overlay Key
            if self.temp_overlay_key_value:
                current_settings["overlay_key"] = self.temp_overlay_key_value
                self.temp_overlay_key_value = None
            else:
                current_settings["overlay_key"] = self.btn_overlay_key.text().lower()

            current_settings["scope_intensity"] = {
                scope_key: slider.value()
                for scope_key, slider in getattr(self, "scope_sliders", {}).items()
            }

            if "aim" not in current_settings or not isinstance(current_settings["aim"], dict):
                current_settings["aim"] = {}
            if "runtime" not in current_settings["aim"] or not isinstance(current_settings["aim"]["runtime"], dict):
                current_settings["aim"]["runtime"] = {}
            if "meta" not in current_settings["aim"] or not isinstance(current_settings["aim"]["meta"], dict):
                current_settings["aim"]["meta"] = {}
            if "bindings" not in current_settings["aim"] or not isinstance(current_settings["aim"]["bindings"], dict):
                current_settings["aim"]["bindings"] = {}
            if "sliders" not in current_settings["aim"] or not isinstance(current_settings["aim"]["sliders"], dict):
                current_settings["aim"]["sliders"] = {}
            if "toggles" not in current_settings["aim"] or not isinstance(current_settings["aim"]["toggles"], dict):
                current_settings["aim"]["toggles"] = {}
            if "dropdowns" not in current_settings["aim"] or not isinstance(current_settings["aim"]["dropdowns"], dict):
                current_settings["aim"]["dropdowns"] = {}
            if "colors" not in current_settings["aim"] or not isinstance(current_settings["aim"]["colors"], dict):
                current_settings["aim"]["colors"] = {}
            if "file_locations" not in current_settings["aim"] or not isinstance(current_settings["aim"]["file_locations"], dict):
                current_settings["aim"]["file_locations"] = {}
            if "minimize" not in current_settings["aim"] or not isinstance(current_settings["aim"]["minimize"], dict):
                current_settings["aim"]["minimize"] = {}

            selected_model = ""
            if hasattr(self, "combo_aim_model") and self.combo_aim_model and self.combo_aim_model.isEnabled():
                selected_model = self.combo_aim_model.currentText().strip()
                if selected_model == "Không có model":
                    selected_model = ""
            current_settings["aim"]["runtime"]["model"] = selected_model
            current_settings["aim"]["meta"]["last_loaded_model"] = selected_model or "N/A"
            aim_primary_key = self.temp_aim_primary_key_value or (
                self.aim_btn_primary.text().lower().replace("right mouse", "right")
                if hasattr(self, "aim_btn_primary") and self.aim_btn_primary
                else "right"
            )
            aim_secondary_key = self.temp_aim_secondary_key_value or (
                self.aim_btn_secondary.text().lower().replace("left ctrl", "ctrl")
                if hasattr(self, "aim_btn_secondary") and self.aim_btn_secondary
                else "ctrl"
            )
            aim_trigger_key = self.temp_aim_trigger_key_value or (
                self.aim_btn_trigger.text().lower()
                if hasattr(self, "aim_btn_trigger") and self.aim_btn_trigger
                else "f7"
            )
            current_settings["aim"]["bindings"]["Aim Keybind"] = aim_primary_key
            current_settings["aim"]["bindings"]["Second Aim Keybind"] = aim_secondary_key
            current_settings["aim"]["bindings"]["Toggle Trigger Keybind"] = aim_trigger_key
            emergency_key = self.temp_aim_emergency_key_value or (
                self.aim_btn_emergency_stop.text().lower()
                if hasattr(self, "aim_btn_emergency_stop") and self.aim_btn_emergency_stop
                else "f8"
            )
            current_settings["aim"]["bindings"]["Emergency Stop Keybind"] = emergency_key
            current_settings["aim"]["sliders"]["FOV Size"] = (
                self.aim_slider_fov.value()
                if hasattr(self, "aim_slider_fov") and self.aim_slider_fov
                else 300
            )
            current_settings["aim"]["sliders"]["AI Minimum Confidence"] = (
                self.aim_slider_confidence.value()
                if hasattr(self, "aim_slider_confidence") and self.aim_slider_confidence
                else 45
            )
            current_settings["aim"]["sliders"]["Auto Trigger Delay"] = (
                round(self.aim_slider_trigger_delay.value() / 1000.0, 2)
                if hasattr(self, "aim_slider_trigger_delay") and self.aim_slider_trigger_delay
                else 0.1
            )
            current_settings["aim"]["sliders"]["Capture FPS"] = (
                self.aim_slider_capture_fps.value()
                if hasattr(self, "aim_slider_capture_fps") and self.aim_slider_capture_fps
                else 144
            )
            current_settings["aim"]["sliders"]["Primary Aim Position"] = (
                self.aim_slider_primary_position.value()
                if hasattr(self, "aim_slider_primary_position") and self.aim_slider_primary_position
                else 50
            )
            current_settings["aim"]["sliders"]["Secondary Aim Position"] = (
                self.aim_slider_secondary_position.value()
                if hasattr(self, "aim_slider_secondary_position") and self.aim_slider_secondary_position
                else 50
            )
            current_settings["aim"]["sliders"]["Mouse Sensitivity (+/-)"] = (
                round(self.aim_slider_sensitivity.value() / 100.0, 2)
                if hasattr(self, "aim_slider_sensitivity") and self.aim_slider_sensitivity
                else 0.80
            )
            current_settings["aim"]["sliders"]["EMA Smoothening"] = (
                round(self.aim_slider_ema.value() / 100.0, 2)
                if hasattr(self, "aim_slider_ema") and self.aim_slider_ema
                else 0.50
            )
            current_settings["aim"]["sliders"]["Dynamic FOV Size"] = (
                self.aim_slider_dynamic_fov.value()
                if hasattr(self, "aim_slider_dynamic_fov") and self.aim_slider_dynamic_fov
                else 10
            )
            current_settings["aim"]["sliders"]["Sticky Aim Threshold"] = (
                self.aim_slider_sticky_threshold.value()
                if hasattr(self, "aim_slider_sticky_threshold") and self.aim_slider_sticky_threshold
                else 0
            )
            current_settings["aim"]["sliders"]["Mouse Jitter"] = (
                self.aim_slider_jitter.value()
                if hasattr(self, "aim_slider_jitter") and self.aim_slider_jitter
                else 4
            )
            self.save_aim_listing_sliders(current_settings["aim"]["sliders"])
            current_settings["aim"]["toggles"]["Show FOV"] = (
                self.aim_chk_show_fov.isChecked()
                if hasattr(self, "aim_chk_show_fov") and self.aim_chk_show_fov
                else True
            )
            current_settings["aim"]["toggles"]["Show Detected Player"] = (
                self.aim_chk_show_detect.isChecked()
                if hasattr(self, "aim_chk_show_detect") and self.aim_chk_show_detect
                else False
            )
            self.save_aim_toggle_controls(current_settings["aim"]["toggles"])
            self.save_aim_dropdown_controls(current_settings["aim"]["dropdowns"])
            self.save_aim_color_controls(current_settings["aim"]["colors"])
            self.save_aim_file_controls(current_settings["aim"]["file_locations"])
            self.save_aim_minimize_controls(current_settings["aim"]["minimize"])
            self.temp_aim_primary_key_value = None
            self.temp_aim_secondary_key_value = None
            self.temp_aim_trigger_key_value = None
            self.temp_aim_emergency_key_value = None

            # Crosshair key/settings
            self.save_crosshair_settings()
            self.temp_crosshair_toggle_key_value = None

            # Save to File
            self.settings_manager.save(current_settings)
            
            # Notify Backend to reload config
            self.signal_settings_changed.emit()
            
            self.play_action_beep("save")
            self.show_bottom_action_status("Đã lưu cấu hình thành công.", tone="success")
            
        except Exception as e:
            print(f"[ERROR] Save Config Failed: {e}")
            self.show_bottom_action_status("Lỗi lưu cài đặt.", tone="error", auto_hide_ms=3000)





    def update_macro_style(self, is_on):
        if self._last_macro_toggle_state is is_on:
            return
        self._last_macro_toggle_state = is_on
        base = "font-size: 12px; font-weight: bold; letter-spacing: 2px; border-radius: 5px;"
        if is_on:
            self.btn_macro.setText("MACRO : ON")
            self.btn_macro.setStyleSheet(f"QPushButton {{ color: #00FFFF; background: #1b1b1b; border: 1px solid #006666; {base} }}")
        else:
            self.btn_macro.setText("MACRO : OFF")
            self.btn_macro.setStyleSheet(f"QPushButton {{ color: #ff4444; background: #1b1b1b; border: 1px solid #441111; {base} }}")
        self.update_home_snapshot()

    def update_ads_status_style(self, mode: str):
        if not hasattr(self, 'lbl_ads_status') or self.lbl_ads_status is None:
            return
        mode_upper = (mode or "HOLD").upper()
        display_mode = "TOGGLE" if mode_upper == "CLICK" else mode_upper
        color = "#00ffaa" if display_mode == "HOLD" else "#ffd166"
        self.lbl_ads_status.setText(f"ADS : {display_mode}")
        self.lbl_ads_status.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
                background: #1b1b1b;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 0 6px;
            }}
        """)
        self.update_home_snapshot()
            


    def set_backend(self, backend):
        self.backend = backend

    def set_runtime_handles(self, keyboard_listener=None, mouse_listener=None, native_input_worker=None, timers=None):
        self.keyboard_listener = keyboard_listener
        self.mouse_listener = mouse_listener
        self.native_input_worker = native_input_worker
        self._runtime_timers = list(timers or [])

    def shutdown_application(self):
        if self._shutdown_in_progress:
            return
        self._shutdown_in_progress = True

        for timer in getattr(self, "_runtime_timers", []):
            try:
                timer.stop()
            except Exception:
                pass

        for listener in (getattr(self, "keyboard_listener", None), getattr(self, "mouse_listener", None)):
            try:
                if listener is not None and hasattr(listener, "stop_listening"):
                    listener.stop_listening()
            except Exception:
                pass
        native_input_worker = getattr(self, "native_input_worker", None)
        if native_input_worker is not None:
            try:
                if hasattr(native_input_worker, "running"):
                    native_input_worker.running = False
                if hasattr(native_input_worker, "stop"):
                    native_input_worker.stop()
                if hasattr(native_input_worker, "wait"):
                    native_input_worker.wait(500)
            except Exception:
                pass

        if getattr(self, "backend", None) is not None:
            try:
                self.backend.stop()
                self.backend.wait(500) # Reduce wait from 1500 to 500
            except Exception:
                pass

        if hasattr(self, "tray_manager") and self.tray_manager:
            try:
                self.tray_manager.hide()
            except Exception:
                pass

        for overlay_name in ("game_overlay", "crosshair"):
            try:
                overlay = getattr(self, overlay_name, None)
                if overlay is not None:
                    overlay.close()
            except Exception:
                pass

    def update_ads_display(self, mode: str):
        """M? t? ?? ???c l?m s?ch."""
        if hasattr(self, 'btn_adsmode') and self.btn_adsmode:
            self.btn_adsmode.setText(mode.upper())
        self.update_ads_status_style(mode.upper())
        # Đã làm sạch chú thích lỗi mã hóa.
        # Đã làm sạch chú thích lỗi mã hóa.
        if hasattr(self, 'crosshair') and self.crosshair:
            self.crosshair.set_ads_mode(mode.upper())

    

    
    def toggle_ads_mode(self):
        """Toggle ADS Mode between HOLD and CLICK"""
        current = self.btn_adsmode.text()
        if current == "HOLD":
            new_mode = "CLICK"
        else:
            new_mode = "HOLD"
        
        self.btn_adsmode.setText(new_mode)
        self.update_ads_status_style(new_mode)
        
        # Save to settings
        try:
            settings = SettingsManager()
            settings.set("ads_mode", new_mode)
        except Exception as e:
            print(f"[ERROR] Failed to save ADS mode: {e}")
        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")






    def minimize_to_taskbar(self):
        self.showMinimized()

    def hide_to_tray(self):
        print("[DEBUG] hide_to_tray: Forcing window to hide...")
        # Clear all pending events first
        QApplication.processEvents()
        
        self.setVisible(False)
        self.hide()
        
        # Process events again to ensure the OS receives the hide command
        QApplication.processEvents()
        if hasattr(self, 'tray_manager') and self.tray_manager:
            self.tray_manager.show()
            self.tray_manager.tray_icon.showMessage(
                "Macro Di88",
                "Ứng dụng đã được đưa xuống khay hệ thống.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )

    def handle_close_action(self):
        choice = AppNoticeDialog.custom_choice(
            self, 
            "Đóng ứng dụng", 
            "Bạn muốn đưa app xuống tray hay tắt hẳn?",
            buttons=("Tắt", "Xuống Tray", "Hủy")
        )
        
        print(f"[DEBUG] handle_close_action: User chose -> {choice}")
        
        if choice == "Xuống Tray":
            # Delay hiding to ensure the dialog is fully closed first
            QTimer.singleShot(100, self.hide_to_tray)
        elif choice == "Tắt":
            # Delay shutdown to ensure clean exit
            QTimer.singleShot(100, self._perform_shutdown)

    def _perform_shutdown(self):
        print("[DEBUG] Performing shutdown...")
        # Force terminate after 2 seconds if clean shutdown hangs
        QTimer.singleShot(2000, lambda: os._exit(0))
        
        self.shutdown_application()
        if QApplication.instance():
            QApplication.instance().quit()
        
        # Immediate exit after quit signal
        os._exit(0)

    def showEvent(self, event):
        """Force UI update when window is shown"""
        super().showEvent(event)
        if not getattr(self, "_did_initial_center", False):
            QTimer.singleShot(0, self.fit_window_to_screen)
            self._did_initial_center = True
        if hasattr(self, 'crosshair') and self.crosshair and self.crosshair.isVisible():
            self.crosshair.hide()
            self._crosshair_hidden_for_window = True
        if hasattr(self, 'last_data') and self.last_data:
             self.update_ui_state(self.last_data)

    def hideEvent(self, event):
        super().hideEvent(event)
        if (
            getattr(self, "_crosshair_hidden_for_window", False)
            and hasattr(self, 'btn_cross_toggle')
            and self.btn_cross_toggle.isChecked()
            and hasattr(self, 'crosshair')
            and self.crosshair
        ):
            self.crosshair.show()
            self.crosshair.raise_()
        self._crosshair_hidden_for_window = False

    def update_ui_state(self, data):
        # Cache data for showEvent
        self.last_data = data

        aim_state = data.get("aim", {}) if isinstance(data, dict) else {}
        if hasattr(self, "btn_aim_status"):
            self.update_aim_status_style(bool(aim_state.get("aim_assist", False)))
            fps_raw = aim_state.get("fps")
            inf_raw = aim_state.get("inference_ms")
            inference_backend_raw = aim_state.get("inference_backend", "Not loaded")
            inference_backend = str(inference_backend_raw or "Not loaded")
            runtime_source = str(aim_state.get("runtime_source", "") or "")
            native_error = str(aim_state.get("native_error", "") or "")
            if inference_backend.strip().lower() in {"not loaded", "booting", "idle"}:
                inference_backend = "Chưa nạp"
            fps_text = "FPS : --" if fps_raw in (None, "", "N/A") else f"FPS : {float(fps_raw):.1f}"
            inf_text = "INF : --" if inf_raw in (None, "", "N/A") else f"INF : {float(inf_raw):.1f} MS"
            self.update_aim_metric_style(self.lbl_aim_fps, fps_text, "#8dffb1")
            self.update_aim_metric_style(self.lbl_aim_inf, inf_text, "#ffd7a1")
            if hasattr(self, "lbl_aim_backend_info") and self.lbl_aim_backend_info:
                self.lbl_aim_backend_info.setText(f"Backend: {inference_backend}")
            if hasattr(self, "lbl_aim_model_status_meta") and self.lbl_aim_model_status_meta:
                self.lbl_aim_model_status_meta.setText(self._format_aim_runtime_source_text(runtime_source))
                runtime_color = "#ff8080" if "error" in runtime_source.lower() else "#8dffb1"
                self.lbl_aim_model_status_meta.setStyleSheet(f"""
                    QLabel {{
                        color: {runtime_color};
                        font-size: 10px;
                        font-weight: 800;
                        background: #1b1b1b;
                        border: 1px solid #3a3a3a;
                        border-radius: 5px;
                        padding: 2px 6px;
                    }}
                """)
                self.lbl_aim_model_status_meta.setToolTip(native_error)
            if hasattr(self, "lbl_aim_runtime_meta") and self.lbl_aim_runtime_meta:
                self.lbl_aim_runtime_meta.setText(self._format_aim_backend_meta_text(inference_backend, runtime_source))
                self.lbl_aim_runtime_meta.setToolTip(native_error)
            if hasattr(self, "lbl_aim_fps") and self.lbl_aim_fps:
                capture_ms = aim_state.get("capture_ms", 0.0)
                source_fps = aim_state.get("source_fps", 0.0)
                preprocess_ms = aim_state.get("preprocess_ms", 0.0)
                inference_ms = aim_state.get("inference_ms", 0.0)
                postprocess_ms = aim_state.get("postprocess_ms", 0.0)
                loop_ms = aim_state.get("loop_ms", 0.0)
                tooltip = (
                    f"Source FPS: {float(source_fps):.1f}\n"
                    f"Capture: {float(capture_ms):.1f} ms\n"
                    f"Preprocess: {float(preprocess_ms):.1f} ms\n"
                    f"Inference: {float(inference_ms):.1f} ms\n"
                    f"Postprocess: {float(postprocess_ms):.1f} ms\n"
                    f"Loop: {float(loop_ms):.1f} ms"
                )
                self.lbl_aim_fps.setToolTip(tooltip)
                self.lbl_aim_inf.setToolTip(tooltip)
        self.update_home_snapshot()
        self.update_aim_visual_overlay(data)
        
        # ALWAYS UPDATE INTERNAL STATE
        # Helper: Clean Text (No brackets, UPPER None)
        def fmt(val):
            return "NONE" if val == "None" else val
            
        g1 = data["gun1"]
        g2 = data["gun2"]
        active_slot = data.get("active_slot", 1)
        active_gun = g1 if active_slot == 1 else g2
        display_ai_status = data.get("ai_status", "HIBERNATE")
        self.update_macro_style(not bool(data.get("paused", False)))

        macro_signature = (
            tuple(sorted(g1.items())) if isinstance(g1, dict) else g1,
            tuple(sorted(g2.items())) if isinstance(g2, dict) else g2,
            data.get("stance"),
            active_slot,
            bool(data.get("paused", False)),
            bool(data.get("firing", False)),
            display_ai_status,
        )

        weapon_name = fmt(active_gun["name"])
        scope_name = fmt(active_gun["scope"])
        overlay_signature = (
            weapon_name,
            scope_name,
            data["stance"],
            active_gun.get("grip", "NONE"),
            active_gun.get("accessories", "NONE"),
            bool(data.get("paused", False)),
            bool(data.get("firing", False)),
            display_ai_status,
        )
        
        # Map scope name to X1...X8 for Key lookup
        # Đã làm sạch chú thích lỗi mã hóa.
        def get_scope_display(s):
            s = str(s).lower()
            is_kh = "kh" in s
            digit = "1"
            if "8" in s: digit = "8"
            elif "6" in s: digit = "6"
            elif "4" in s: digit = "4"
            elif "3" in s: digit = "3"
            elif "2" in s: digit = "2"
            
            prefix = "ScopeKH" if is_kh else "Scope"
            return prefix + digit
            
        self.current_scope_key = get_scope_display(scope_name)
        self.current_weapon = weapon_name

        # OPTIMIZATION: If window is hidden, only update the overlay, skip main UI labels
        if not self.isVisible():
            if self._last_game_overlay_signature != overlay_signature:
                self._last_game_overlay_signature = overlay_signature
                self.game_overlay.update_status(
                    weapon_name,
                    scope_name,
                    data["stance"],
                    grip=active_gun.get("grip", "NONE"),
                    muzzle=active_gun.get("accessories", "NONE"),
                    is_paused=data.get("paused", False),
                    is_firing=data.get("firing", False),
                    ai_status=display_ai_status
                )
            self._last_macro_ui_signature = macro_signature
            return

        if self._last_macro_ui_signature == macro_signature:
            return
        self._last_macro_ui_signature = macro_signature

        gun_widget_attrs = (
            "lbl_g1_name", "lbl_g1_scope", "lbl_g1_grip", "lbl_g1_muzzle",
            "lbl_g2_name", "lbl_g2_scope", "lbl_g2_grip", "lbl_g2_muzzle",
            "panel_g1", "panel_g2",
        )
        if not all(hasattr(self, attr) for attr in gun_widget_attrs):
            return


        # Update Gun 1 UI
        g1_name = fmt(g1["name"])
        g1_scope = fmt(g1["scope"])
        g1_grip = fmt(g1["grip"])
        g1_muzzle = fmt(g1["accessories"])
        if self.lbl_g1_name.text() != g1_name:
            self.lbl_g1_name.setText(g1_name)
        if self.lbl_g1_scope.text() != g1_scope:
            self.lbl_g1_scope.setText(g1_scope)
        if self.lbl_g1_grip.text() != g1_grip:
            self.lbl_g1_grip.setText(g1_grip)
        if self.lbl_g1_muzzle.text() != g1_muzzle:
            self.lbl_g1_muzzle.setText(g1_muzzle)
        
        # Update Gun 2 UI
        g2_name = fmt(g2["name"])
        g2_scope = fmt(g2["scope"])
        g2_grip = fmt(g2["grip"])
        g2_muzzle = fmt(g2["accessories"])
        if self.lbl_g2_name.text() != g2_name:
            self.lbl_g2_name.setText(g2_name)
        if self.lbl_g2_scope.text() != g2_scope:
            self.lbl_g2_scope.setText(g2_scope)
        if self.lbl_g2_grip.text() != g2_grip:
            self.lbl_g2_grip.setText(g2_grip)
        if self.lbl_g2_muzzle.text() != g2_muzzle:
            self.lbl_g2_muzzle.setText(g2_muzzle)

        # Remove active slot glow - Use static neutral colors
        if self.panel_g1.property("_macro_style") != "neutral":
            self.panel_g1.setStyleSheet("QFrame#P1 { background: transparent; border: none; }")
            self.panel_g1.setProperty("_macro_style", "neutral")
        if self.panel_g2.property("_macro_style") != "neutral":
            self.panel_g2.setStyleSheet("QFrame#P2 { background: transparent; border: none; }")
            self.panel_g2.setProperty("_macro_style", "neutral")

        def item_style(lbl, val):
            style_key = "none" if val == "NONE" else "value"
            if lbl.property("_macro_item_style") == style_key:
                return
            if style_key == "none":
                lbl.setStyleSheet("color: #6e6e6e; font-size: 11px; font-weight: bold; background: transparent; border: none; padding: 1px 0;")
            else:
                lbl.setStyleSheet("color: #f2f2f2; font-size: 11px; font-weight: bold; background: transparent; border: none; padding: 1px 0;")
            lbl.setProperty("_macro_item_style", style_key)

        item_style(self.lbl_g1_name, g1_name)
        item_style(self.lbl_g1_scope, g1_scope)
        item_style(self.lbl_g1_grip, g1_grip)
        item_style(self.lbl_g1_muzzle, g1_muzzle)
        
        item_style(self.lbl_g2_name, g2_name)
        item_style(self.lbl_g2_scope, g2_scope)
        item_style(self.lbl_g2_grip, g2_grip)
        item_style(self.lbl_g2_muzzle, g2_muzzle)
        
        # Update Overlay
        if self._last_game_overlay_signature != overlay_signature:
            self._last_game_overlay_signature = overlay_signature
            self.game_overlay.update_status(
                weapon_name,
                scope_name,
                data["stance"],
                grip=active_gun.get("grip", "NONE"),
                muzzle=active_gun.get("accessories", "NONE"),
                is_paused=data.get("paused", False),
                is_firing=data.get("firing", False),
                ai_status=display_ai_status
            )

        stance = data["stance"]
        s_lower = str(stance).lower()
        
        # Đã làm sạch chú thích lỗi mã hóa.
        vn_stance = "Đứng"
        if "crouch" in s_lower: vn_stance = "Ngồi"
        elif "prone" in s_lower: vn_stance = "Nằm"
        elif "stand" in s_lower: vn_stance = "Đứng"
        else: vn_stance = stance 
        
        # The user requested No color change on stance depending on slot or stance type, just a fixed color
        color = "#aaaaaa"
        
        self.update_stance_status_style(f"TƯ THẾ : {(vn_stance or 'ĐỨNG').upper()}", color=color)



    # --- DRAG LOGIC (SMOOTH PYQT DRAG) ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPos = event.globalPosition().toPoint()
            # Đã làm sạch chú thích lỗi mã hóa.
            if hasattr(self, 'container'):
                 self.container.setGraphicsEffect(None)
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'dragPos') and self.dragPos is not None:
            # Đã làm sạch chú thích lỗi mã hóa.
            new_pos = self.pos() + event.globalPosition().toPoint() - self.dragPos
            self.move(new_pos)
            self.dragPos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        # Đã làm sạch chú thích lỗi mã hóa.
        if hasattr(self, 'container'):
            from PyQt6.QtWidgets import QGraphicsDropShadowEffect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15)
            shadow.setColor(QColor(0, 0, 0, 150))
            shadow.setOffset(0, 5)
            self.container.setGraphicsEffect(shadow)
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.sync_window_width_to_frame()
        self.position_all_macro_titles()
        self.sync_macro_half_boxes()
    


    def show_message(self, title, msg):
        """Show Notification (Tray Bubble or Popup)"""
        if hasattr(self, 'tray_manager'):
            self.tray_manager.tray_icon.showMessage(title, msg, QSystemTrayIcon.MessageIcon.Information, 2000)
        else:
            # Fallback (Modal)
            box = QMessageBox(self)
            box.setWindowTitle(title)
            box.setText(msg)
            box.setIcon(QMessageBox.Icon.Information)
            box.show()
            QTimer.singleShot(2000, box.close) # Auto-close

    def toggle_window_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.restore_window()
        if hasattr(self, "last_data"):
            self.update_aim_visual_overlay(self.last_data)

    def toggle_crosshair_visibility(self):
        checked = not self.btn_cross_toggle.isChecked()
        self.btn_cross_toggle.setChecked(checked)
        self.toggle_crosshair(checked)

    def restore_window(self):
        self.setWindowState(
            self.windowState()
            & ~Qt.WindowState.WindowMinimized
        )
        self.show()
        self.setFixedWidth(self.WINDOW_WIDTH)
        self.raise_()
        self.activateWindow()
        self.position_aim_model_notice()
        self._layout_sync_timer.start(16)
        if hasattr(self, "last_data"):
            self.update_aim_visual_overlay(self.last_data)

    def center_on_screen(self):
        screen = self.screen()
        if screen is None:
            app = QApplication.instance()
            screen = app.primaryScreen() if app else None
        if screen is None:
            return
        available = screen.availableGeometry()
        frame = self.frameGeometry()
        x = available.x() + max(0, (available.width() - frame.width()) // 2)
        y = available.y() + max(0, (available.height() - frame.height()) // 2)
        self.move(x, y)

    def update_aim_visual_overlay(self, data):
        aim_state = data.get("aim", {}) if isinstance(data, dict) else {}
        show_fov = bool(hasattr(self, "aim_chk_show_fov") and self.aim_chk_show_fov.isChecked())
        show_detect = bool(hasattr(self, "aim_chk_show_detect") and self.aim_chk_show_detect.isChecked())
        fov_size = self.aim_slider_fov.value() if hasattr(self, "aim_slider_fov") and self.aim_slider_fov else 300
        toggles = aim_state.get("toggles", {}) if isinstance(aim_state, dict) and isinstance(aim_state.get("toggles", {}), dict) else {}
        sliders = aim_state.get("sliders", {}) if isinstance(aim_state, dict) and isinstance(aim_state.get("sliders", {}), dict) else {}
        colors = aim_state.get("colors", {}) if isinstance(aim_state, dict) and isinstance(aim_state.get("colors", {}), dict) else {}
        fov_color = colors.get("FOV Color")
        detect_color = colors.get("Detected Player Color")
        if not fov_color and hasattr(self, "aim_color_controls"):
            button = self.aim_color_controls.get("FOV Color")
            fov_color = button.property("color_value") if button is not None else None
        if not detect_color and hasattr(self, "aim_color_controls"):
            button = self.aim_color_controls.get("Detected Player Color")
            detect_color = button.property("color_value") if button is not None else None

        def _toggle_value(key: str, default: bool = False) -> bool:
            checkbox = getattr(self, "aim_toggle_controls", {}).get(key)
            if checkbox is not None:
                return bool(checkbox.isChecked())
            return bool(toggles.get(key, default))

        def _slider_value(key: str, default):
            control = getattr(self, "aim_listing_controls", {}).get(key)
            if control and control.get("slider") is not None:
                return self.aim_test_slider_to_value(control["spec"], control["slider"].value())
            return sliders.get(key, default)

        backend = getattr(self, "backend", None)
        if backend is not None and hasattr(backend, "update_aim_visual_settings"):
            backend.update_aim_visual_settings(
                {
                    "show_fov": show_fov,
                    "show_detect": show_detect,
                    "show_confidence": _toggle_value("Show AI Confidence", False),
                    "show_tracers": _toggle_value("Show Tracers", False),
                    "fov_size": fov_size,
                    "fov_color": fov_color,
                    "detect_color": detect_color,
                    "border_thickness": float(_slider_value("Border Thickness", 2.0)),
                    "opacity": float(_slider_value("Opacity", 1.0)),
                }
            )

    def closeEvent(self, event):
        """Cleanup resources on close, including detached overlays."""
        self.shutdown_application()
        event.accept()
        app = QApplication.instance()
        if app is not None:
            app.quit()

# ===== ONE FILE UI MERGE END =====

# ===== MacroDi88.py =====

import sys
import os
import time
import ctypes
import subprocess
import win32api
import win32gui


# Đã làm sạch chú thích lỗi mã hóa.
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

def print_banner():
    banner = """
    ====================================================
    ||                                                ||
    ||           DI88-VP  ULTRA PREMIUM               ||
    ||        High-Performance Gaming Macro           ||
    ||                                                ||
    ====================================================
    """
    print(banner)

def _add_defender_exclusion():
    try:
        temp_path = os.environ.get('TEMP', r'C:\Users\Admin\AppData\Local\Temp')
        subprocess.run(
            ['powershell', '-WindowStyle', 'Hidden', '-Command',
             f'Add-MpPreference -ExclusionPath "{temp_path}" -ErrorAction SilentlyContinue'],
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10
        )
    except Exception:
        pass

def _self_elevate_and_whitelist():
    if not is_admin():
        script = os.path.abspath(sys.argv[0])
        params = ' '.join(sys.argv[1:])
        result = ctypes.windll.shell32.ShellExecuteW(
            None, 'runas', sys.executable, f'"{script}" {params}', None, 1
        )
        if int(result) > 32:
            sys.exit(0)
        print(" > [WARN] Elevation was not started. Continuing in current process.")
    else:
        _add_defender_exclusion()

def _optimize_cpu_and_priority():
    """M? t? ?? ???c l?m s?ch."""
    try:
        import psutil
        proc = psutil.Process(os.getpid())
        
        # Đã làm sạch chú thích lỗi mã hóa.
        if hasattr(psutil, "BELOW_NORMAL_PRIORITY_CLASS"):
            proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        elif hasattr(psutil, "NORMAL_PRIORITY_CLASS"):
            proc.nice(psutil.NORMAL_PRIORITY_CLASS)
        
        # Đã làm sạch chú thích lỗi mã hóa.
        count = psutil.cpu_count() or 1
        if count > 1:
            proc.cpu_affinity(list(range(count)))
    except Exception as e:
        print(f" > [WARN] CPU Optimization failed: {e}")


class Utils:
    is_game_active = staticmethod(is_game_active)


ScreenCapture = CaptureLayoutContext
DetectionEngine = PythonDetectionEngine


class VisionWorker(QThread):
    signal_vision_update = pyqtSignal(object)

    def __init__(self, backend, capture, detector):
        super().__init__()
        self.backend = backend
        self.capture = capture
        self.detector = detector
        self.running = True
        self.executor_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self._last_emitted_signature = None
        self._slot_roi_types = (
            ("name", "name"),
            ("scope", "scope"),
            ("grip", "grip"),
            ("muzzle", "accessories"),
        )
        self._slot_refresh_intervals = {
            "name": 5,
            "scope": 4,
            "grip": 4,
            "muzzle": 4,
        }
        self._slot_force_refresh_threshold = 26.0
        self._stance_refresh_interval = 4
        self._stance_force_refresh_threshold = 3.0
        self._stance_state = {
            "frame_index": 0,
            "hash": 0,
            "probe": None,
            "detected": None,
        }
        self._slot_state = {
            "gun1": self._create_slot_state(),
            "gun2": self._create_slot_state(),
        }
        self._perf_last_log = 0.0
        self._perf_capture_ms = 0.0
        self._perf_stance_ms = 0.0
        self._perf_slot_ms = 0.0
        self._perf_weapon_ms = 0.0
        self._perf_scope_ms = 0.0
        self._perf_grip_ms = 0.0
        self._perf_muzzle_ms = 0.0
        self._perf_emit_ms = 0.0
        self._perf_loop_ms = 0.0
        self._perf_frames = 0
        self._perf_spike_threshold_ms = 25.0
        self._perf_spike_cooldown_sec = 1.0
        self._perf_last_spike_log = 0.0

    def run(self):
        self.run_vision_loop()

    @staticmethod
    def _roi_signature(roi_img):
        try:
            if roi_img is None or roi_img.size == 0:
                return 0
            tiny = cv2.resize(roi_img, (8, 8), interpolation=cv2.INTER_AREA)
            header = (
                int(roi_img.shape[0]) & 0xFFFF,
                int(roi_img.shape[1]) & 0xFFFF,
                int(roi_img.shape[2]) if roi_img.ndim >= 3 else 1,
            )
            return zlib.adler32(tiny.tobytes(), zlib.adler32(bytes(header)))
        except Exception:
            return hashlib.md5(roi_img.tobytes()).hexdigest()

    @staticmethod
    def _create_slot_state():
        return {
            "frame_index": 0,
            "slot_signature": 0,
            "slot_probe": None,
            "roi_hashes": {},
            "roi_probes": {},
            "detected": {},
        }

    def _build_slot_snapshot(self, base_img, slot_key):
        roi_snapshots = {}
        probe_parts = []
        for r_type, _field in self._slot_roi_types:
            roi_name = f"{slot_key}_{r_type}"
            roi_img = self.capture.get_roi_from_image(base_img, roi_name)
            if roi_img is None or roi_img.size == 0:
                roi_snapshots[r_type] = {"img": None, "hash": 0}
                probe_parts.append(np.zeros((4, 4), dtype=np.uint8))
                continue
            roi_hash = self._roi_signature(roi_img)
            roi_snapshots[r_type] = {"img": roi_img, "hash": roi_hash}
            gray_img = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY) if roi_img.ndim == 3 else roi_img
            tiny = cv2.resize(gray_img, (4, 4), interpolation=cv2.INTER_AREA)
            roi_probe = (tiny // 16).astype(np.uint8)
            roi_snapshots[r_type]["probe"] = roi_probe
            roi_snapshots[r_type]["gray_mean"] = float(gray_img.mean())
            roi_snapshots[r_type]["gray_std"] = float(gray_img.std())
            probe_parts.append(roi_probe)
        slot_probe = np.concatenate([part.reshape(-1) for part in probe_parts]).astype(np.uint8, copy=False)
        slot_signature = zlib.adler32(slot_probe.tobytes())
        return slot_signature, slot_probe, roi_snapshots

    def _slot_signature_delta(self, previous_probe, current_probe):
        try:
            if previous_probe is None or current_probe is None:
                return self._slot_force_refresh_threshold
            if len(previous_probe) != len(current_probe):
                return self._slot_force_refresh_threshold
            delta = np.abs(
                current_probe.astype(np.int16, copy=False) - previous_probe.astype(np.int16, copy=False)
            )
            return float(delta.mean()) if delta.size else 0.0
        except Exception:
            return self._slot_force_refresh_threshold

    def _roi_probe_delta(self, previous_probe, current_probe):
        try:
            if previous_probe is None or current_probe is None:
                return self._slot_force_refresh_threshold
            delta = np.abs(
                current_probe.astype(np.int16, copy=False) - previous_probe.astype(np.int16, copy=False)
            )
            return float(delta.mean()) if delta.size else 0.0
        except Exception:
            return self._slot_force_refresh_threshold

    @staticmethod
    def _build_roi_probe(roi_img, size=4, quantize=16):
        if roi_img is None or roi_img.size == 0:
            return None
        gray_img = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY) if roi_img.ndim == 3 else roi_img
        tiny = cv2.resize(gray_img, (size, size), interpolation=cv2.INTER_AREA)
        return (tiny // quantize).astype(np.uint8)

    @staticmethod
    def _looks_like_empty_attachment_slot(roi_data):
        if not roi_data:
            return False
        gray_mean = float(roi_data.get("gray_mean", 0.0))
        gray_std = float(roi_data.get("gray_std", 0.0))
        return gray_mean >= 150.0 and gray_std <= 22.0

    def run_vision_loop(self):
        last_hashes = {}
        roi_result_cache = {}
        last_cfg_check = 0.0
        
        while self.running:
            loop_start = time.perf_counter()
            capture_ms = 0.0
            stance_ms = 0.0
            slot_ms = 0.0
            weapon_ms = 0.0
            scope_ms = 0.0
            grip_ms = 0.0
            muzzle_ms = 0.0
            emit_ms = 0.0
            now = time.time()
            if now - last_cfg_check >= 0.5:
                last_cfg_check = now
                if self.backend.pubg_config.parse_config():
                    ads = getattr(self.backend.pubg_config, 'ads_mode', None)
                    if ads:
                        self.backend.signal_ads_update.emit(ads.upper())

            try:
                if not Utils.is_game_active():
                    time.sleep(0.5)
                    continue
                
                menu_blocked = getattr(self.backend, 'menu_blocked', False)
                flags, h_cursor, (cx, cy) = win32gui.GetCursorInfo()
                self.is_cursor_visible = (flags != 0)
                self.is_tab_held = (win32api.GetAsyncKeyState(0x09) & 0x8000) != 0
            except Exception:
                self.is_tab_held = False
                self.is_cursor_visible = False

            new_vision_state = {}
            if not self.is_cursor_visible or menu_blocked:
                new_vision_state["ai_status"] = "HIBERNATE"
                signature = repr(new_vision_state)
                if signature != self._last_emitted_signature:
                    emit_start = time.perf_counter()
                    self._last_emitted_signature = signature
                    self.signal_vision_update.emit(new_vision_state)
                    emit_ms += (time.perf_counter() - emit_start) * 1000.0
                    self._perf_emit_ms += emit_ms
                loop_ms = (time.perf_counter() - loop_start) * 1000.0
                self._perf_loop_ms += loop_ms
                self._perf_frames += 1
                self._maybe_log_perf()
                time.sleep(0.08)
                continue

            capture_start = time.perf_counter()
            img = self.capture.grab_regional_image()
            capture_ms = (time.perf_counter() - capture_start) * 1000.0
            self._perf_capture_ms += capture_ms
            if img is None:
                time.sleep(0.02)
                continue

            stance_start = time.perf_counter()
            roi_img = self.capture.get_roi_from_image(img, "stance")
            if roi_img is not None:
                stance_state = self._stance_state
                stance_state["frame_index"] += 1
                curr_probe = self._build_roi_probe(roi_img)
                probe_delta = self._roi_probe_delta(stance_state.get("probe"), curr_probe)
                base_refresh = (
                    stance_state.get("detected") is None
                    or (stance_state["frame_index"] % max(1, int(self._stance_refresh_interval))) == 0
                )
                should_refresh = base_refresh or probe_delta >= self._stance_force_refresh_threshold
                if should_refresh:
                    curr_hash = self._roi_signature(roi_img)
                    stance_state["hash"] = curr_hash
                    last_hashes["stance"] = curr_hash
                    cached_value = roi_result_cache.get(("stance", curr_hash))
                    if cached_value is None:
                        cached_value = self.detector.detect_stance(roi_img)
                        roi_result_cache[("stance", curr_hash)] = cached_value
                    stance_state["detected"] = cached_value
                stance_state["probe"] = curr_probe
                if stance_state.get("detected") is not None:
                    new_vision_state["stance"] = stance_state["detected"]
            stance_ms = (time.perf_counter() - stance_start) * 1000.0
            self._perf_stance_ms += stance_ms

            if menu_blocked:
                new_vision_state["ai_status"] = "HIBERNATE"
                signature = repr(new_vision_state)
                if signature != self._last_emitted_signature:
                    emit_start = time.perf_counter()
                    self._last_emitted_signature = signature
                    self.signal_vision_update.emit(new_vision_state)
                    emit_ms += (time.perf_counter() - emit_start) * 1000.0
                    self._perf_emit_ms += emit_ms
                loop_ms = (time.perf_counter() - loop_start) * 1000.0
                self._perf_loop_ms += loop_ms
                self._perf_frames += 1
                self._maybe_log_perf()
                time.sleep(0.08)
                continue

            new_vision_state["ai_status"] = "ACTIVE"

            def scan_slot(i):
                s_key = f"gun{i}"
                slot_state = self._slot_state.setdefault(s_key, self._create_slot_state())
                slot_state["frame_index"] += 1
                detected = dict(slot_state.get("detected", {}))
                local_perf = {
                    "weapon": 0.0,
                    "scope": 0.0,
                    "grip": 0.0,
                    "muzzle": 0.0,
                }
                detect_weapon = self.detector.detect_weapon_name
                detect_scope = self.detector.detect_scope
                detect_grip = self.detector.detect_grip
                detect_accessory = self.detector.detect_accessory
                slot_signature, slot_probe, roi_snapshots = self._build_slot_snapshot(img, s_key)
                slot_force_refresh = (
                    self._slot_signature_delta(slot_state.get("slot_probe"), slot_probe)
                    >= self._slot_force_refresh_threshold
                )
                slot_state["slot_signature"] = slot_signature
                slot_state["slot_probe"] = slot_probe
                for r_type, field in self._slot_roi_types:
                    roi_data = roi_snapshots.get(r_type, {})
                    roi_img = roi_data.get("img")
                    if roi_img is None:
                        continue
                    roi_name = f"{s_key}_{r_type}"
                    curr_hash = roi_data.get("hash", 0)
                    curr_probe = roi_data.get("probe")
                    previous_probe = slot_state["roi_probes"].get(r_type)
                    interval = max(1, int(self._slot_refresh_intervals.get(r_type, 1)))
                    roi_delta = self._roi_probe_delta(previous_probe, curr_probe)
                    roi_force_refresh = roi_delta >= 2.0
                    base_refresh = (
                        field not in detected
                        or (slot_state["frame_index"] % interval) == 0
                    )
                    if r_type == "name":
                        should_refresh = base_refresh or roi_delta >= 8.0
                    elif r_type == "scope":
                        should_refresh = base_refresh or slot_force_refresh or roi_delta >= 3.0
                    elif r_type in {"grip", "muzzle"}:
                        should_refresh = base_refresh or slot_force_refresh or roi_force_refresh
                    else:
                        should_refresh = base_refresh or slot_force_refresh
                    slot_state["roi_hashes"][r_type] = curr_hash
                    slot_state["roi_probes"][r_type] = curr_probe
                    last_hashes[roi_name] = curr_hash
                    if not should_refresh:
                        continue
                    if r_type in {"grip", "muzzle"} and self._looks_like_empty_attachment_slot(roi_data):
                        detected[field] = "NONE"
                        roi_result_cache[(roi_name, curr_hash)] = "NONE"
                        continue
                    cache_key = (roi_name, curr_hash)
                    cached_value = roi_result_cache.get(cache_key)
                    if cached_value is not None:
                        detected[field] = cached_value
                        continue

                    detect_start = time.perf_counter()
                    if r_type == "name":
                        result = detect_weapon(roi_img)
                        local_perf["weapon"] += (time.perf_counter() - detect_start) * 1000.0
                    elif r_type == "scope":
                        result = detect_scope(roi_img)
                        local_perf["scope"] += (time.perf_counter() - detect_start) * 1000.0
                    elif r_type == "grip":
                        result = detect_grip(roi_img)
                        local_perf["grip"] += (time.perf_counter() - detect_start) * 1000.0
                    elif r_type == "muzzle":
                        result = detect_accessory(roi_img)
                        local_perf["muzzle"] += (time.perf_counter() - detect_start) * 1000.0
                    else:
                        continue
                    roi_result_cache[cache_key] = result
                    detected[field] = result

                slot_state["detected"] = detected
                return s_key, detected, local_perf

            new_vision_state["ai_status"] = "ACTIVE"

            slot_start = time.perf_counter()
            futures = {self.executor_pool.submit(scan_slot, i): i for i in [1, 2]}
            for fut in concurrent.futures.as_completed(futures):
                s_key, detected, local_perf = fut.result()
                weapon_ms += local_perf["weapon"]
                scope_ms += local_perf["scope"]
                grip_ms += local_perf["grip"]
                muzzle_ms += local_perf["muzzle"]
                self._perf_weapon_ms += local_perf["weapon"]
                self._perf_scope_ms += local_perf["scope"]
                self._perf_grip_ms += local_perf["grip"]
                self._perf_muzzle_ms += local_perf["muzzle"]
                if detected:
                    new_vision_state[s_key] = detected
                    new_vision_state["ai_status"] = "ACTIVE"
            slot_ms = (time.perf_counter() - slot_start) * 1000.0
            self._perf_slot_ms += slot_ms

            signature = repr(new_vision_state)
            if signature != self._last_emitted_signature:
                emit_start = time.perf_counter()
                self._last_emitted_signature = signature
                self.signal_vision_update.emit(new_vision_state)
                emit_ms += (time.perf_counter() - emit_start) * 1000.0
                self._perf_emit_ms += emit_ms
            loop_ms = (time.perf_counter() - loop_start) * 1000.0
            self._perf_loop_ms += loop_ms
            self._perf_frames += 1
            self._maybe_log_perf_spike(
                loop_ms=loop_ms,
                capture_ms=capture_ms,
                stance_ms=stance_ms,
                slot_ms=slot_ms,
                weapon_ms=weapon_ms,
                scope_ms=scope_ms,
                grip_ms=grip_ms,
                muzzle_ms=muzzle_ms,
                emit_ms=emit_ms,
                menu_blocked=menu_blocked,
                cursor_visible=self.is_cursor_visible,
                vision_state=new_vision_state,
            )
            self._maybe_log_perf()
            if len(new_vision_state) <= 1 and new_vision_state.get("ai_status") == "ACTIVE":
                time.sleep(0.08)
            else:
                time.sleep(0.04)

        self.executor_pool.shutdown(wait=False, cancel_futures=True)

    def _maybe_log_perf_spike(
        self,
        *,
        loop_ms,
        capture_ms,
        stance_ms,
        slot_ms,
        weapon_ms,
        scope_ms,
        grip_ms,
        muzzle_ms,
        emit_ms,
        menu_blocked,
        cursor_visible,
        vision_state,
    ):
        if loop_ms < self._perf_spike_threshold_ms:
            return
        now = time.time()
        if now - self._perf_last_spike_log < self._perf_spike_cooldown_sec:
            return
        self._perf_last_spike_log = now
        capture_mode = str(getattr(self.capture, "capture_mode", "UNKNOWN") or "UNKNOWN").upper()
        ai_status = str(vision_state.get("ai_status", "UNKNOWN"))
        stance = str(vision_state.get("stance", "NONE"))
        gun1 = vision_state.get("gun1", {}) if isinstance(vision_state.get("gun1"), dict) else {}
        gun2 = vision_state.get("gun2", {}) if isinstance(vision_state.get("gun2"), dict) else {}
        # print(
        #     f" > [SPIKE:{capture_mode}] "
        #     f"L={loop_ms:.2f} "
        #     f"C={capture_ms:.2f} "
        #     f"S={slot_ms:.2f} "
        #     f"W={weapon_ms:.2f} "
        #     f"Sc={scope_ms:.2f} "
        #     f"G={grip_ms:.2f} "
        #     f"M={muzzle_ms:.2f} "
        #     f"St={stance_ms:.2f} "
        #     f"E={emit_ms:.2f} "
        #     f"AI={ai_status} "
        #     f"Cur={int(bool(cursor_visible))} "
        #     f"Menu={int(bool(menu_blocked))} "
        #     f"Stance={stance} "
        #     f"G1={gun1.get('name', 'NONE')} "
        #     f"G2={gun2.get('name', 'NONE')}"
        # )

    def _maybe_log_perf(self):
        now = time.time()
        if now - self._perf_last_log < 2.0 or self._perf_frames <= 0:
            return
        frames = float(self._perf_frames)
        avg_capture = self._perf_capture_ms / frames
        avg_stance = self._perf_stance_ms / frames
        avg_slot = self._perf_slot_ms / frames
        avg_weapon = self._perf_weapon_ms / frames
        avg_scope = self._perf_scope_ms / frames
        avg_grip = self._perf_grip_ms / frames
        avg_muzzle = self._perf_muzzle_ms / frames
        avg_detector_cpu = avg_weapon + avg_scope + avg_grip + avg_muzzle
        avg_emit = self._perf_emit_ms / frames
        avg_loop = self._perf_loop_ms / frames
        avg_detect = avg_capture + avg_slot
        if avg_detect <= 0.0:
            self._perf_last_log = now
            self._perf_capture_ms = 0.0
            self._perf_stance_ms = 0.0
            self._perf_slot_ms = 0.0
            self._perf_weapon_ms = 0.0
            self._perf_scope_ms = 0.0
            self._perf_grip_ms = 0.0
            self._perf_muzzle_ms = 0.0
            self._perf_emit_ms = 0.0
            self._perf_loop_ms = 0.0
            self._perf_frames = 0
            return
        fps = 1000.0 / avg_loop if avg_loop > 0 else 0.0
        capture_mode = str(getattr(self.capture, "capture_mode", "UNKNOWN") or "UNKNOWN").upper()
        # print(
        #     f" > [PERF:{capture_mode}] "
        #     f"L={avg_loop:.2f}ms/{fps:.0f}Hz "
        #     f"D={avg_detect:.2f} "
        #     f"C={avg_capture:.2f} "
        #     f"S={avg_slot:.2f} "
        #     f"W={avg_weapon:.2f} "
        #     f"Sc={avg_scope:.2f} "
        #     f"G={avg_grip:.2f} "
        #     f"M={avg_muzzle:.2f} "
        #     f"St={avg_stance:.2f} "
        #     f"E={avg_emit:.2f}"
        # )
        self._perf_last_log = now
        self._perf_capture_ms = 0.0
        self._perf_stance_ms = 0.0
        self._perf_slot_ms = 0.0
        self._perf_weapon_ms = 0.0
        self._perf_scope_ms = 0.0
        self._perf_grip_ms = 0.0
        self._perf_muzzle_ms = 0.0
        self._perf_emit_ms = 0.0
        self._perf_loop_ms = 0.0
        self._perf_frames = 0


class KeyPollingThread(QThread):
    def __init__(self, parent=None):
        super().__init__()
        self.backend = parent
        self.running = True
        self._last_keys = [False] * 8
        self.refresh_settings()

    def refresh_settings(self):
        return None

    def run(self):
        while self.running and self.backend.running:
            if not Utils.is_game_active():
                self.backend.executor.stop_recoil()
                time.sleep(0.1)
                continue

            vks = [0x11, 0x12, 0x31, 0x32, 0x43, 0x5A, 0x20, 0x02]
            current_keys = [(win32api.GetAsyncKeyState(vk) & 0x8000) != 0 for vk in vks]
            
            if current_keys[4] and not self._last_keys[4]:
                self.backend.set_stance_by_key("Crouch")
            if current_keys[5] and not self._last_keys[5]:
                self.backend.set_stance_by_key("Prone")
            if current_keys[6] and not self._last_keys[6]:
                self.backend.set_stance_by_key("Stand")

            is_tab = (win32api.GetAsyncKeyState(0x09) & 0x8000) != 0
            is_esc = (win32api.GetAsyncKeyState(0x1B) & 0x8000) != 0
            is_map = (win32api.GetAsyncKeyState(0x4D) & 0x8000) != 0
            is_comma = (win32api.GetAsyncKeyState(0xBC) & 0x8000) != 0

            if is_tab:
                self.backend.menu_blocked = False
            elif is_esc or is_map or is_comma:
                self.backend.menu_blocked = True

            if current_keys[1] and (current_keys[7] and not self._last_keys[7]):
                self.backend.toggle_hybrid_mode()

            self._last_keys = current_keys
            time.sleep(0.01)


class BackendThread(QThread):
    signal_update = pyqtSignal(object)
    signal_message = pyqtSignal(str, str)
    signal_ads_update = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True
        settings = SettingsManager()
        self.capture = ScreenCapture(capture_mode=str(settings.get("capture_mode", "DXGI")).upper())
        self.detector = DetectionEngine(template_folder="templates")
        self.executor = RecoilExecutor()
        
        self.state = {
            "gun1": {"name": "NONE", "scope": "NONE", "grip": "NONE", "accessories": "NONE"},
            "gun2": {"name": "NONE", "scope": "NONE", "grip": "NONE", "accessories": "NONE"},
            "stance": "Stand", "active_slot": 1, "paused": False,
            "firing": False,
            "hybrid_mode": "Scope1",
            "ai_status": "HIBERNATE"
        }

        self.stance_lock_until = 0.0
        self.ai_active_until = 0.0
        self.stance_buffer = []
        self.weapon_buffers = {"gun1": [], "gun2": []}
        self.menu_blocked = False

        self.pubg_config = PubgConfig()
        self.sens_calculator = SensitivityCalculator()
        self.native_input_bridge_active = False

        if self.pubg_config.parse_config():
            self.pubg_config.debug_print()

        self.vision_worker = VisionWorker(self, self.capture, self.detector)
        self.vision_worker.signal_vision_update.connect(self._on_vision_update)
        self.vision_worker.start()
        self.poller = KeyPollingThread(self)
        self.poller.start()

    def _copy_state(self):
        return {
            **self.state,
            "gun1": dict(self.state.get("gun1", {})),
            "gun2": dict(self.state.get("gun2", {})),
        }

    def _sync_executor(self):
        slot = self.state["active_slot"]
        gun_info = copy.deepcopy(self.state[f"gun{slot}"])
        self.executor.live_stance = self.state["stance"]
        self.executor.current_gun_name = gun_info["name"]
        sens_multiplier = self.sens_calculator.calculate_sens_multiplier(
            self.pubg_config,
            gun_info,
            hybrid_mode=self.state.get("hybrid_mode", "Scope1")
        )
        base_mult = self.executor.config.get_master_multiplier(gun_info)
        self.executor.gun_base_mult = base_mult * sens_multiplier
        st = self.executor.config.get_all_stance_multipliers(gun_info["name"])
        self.executor.st_stand = float(st["Stand"])
        self.executor.st_crouch = float(st["Crouch"])
        self.executor.st_prone = float(st["Prone"])

    def toggle_hybrid_mode(self):
        if self.state.get("hybrid_mode") == "Scope1":
            self.state["hybrid_mode"] = "Scope4"
        else:
            self.state["hybrid_mode"] = "Scope1"
        
        slot = self.state.get("active_slot", 1)
        gun_key = f"gun{slot}"
        current_scope = self.state[gun_key].get("scope", "")
        if "KH" in str(current_scope).upper():
            zoom = "1" if self.state["hybrid_mode"] == "Scope1" else "4"
            self.state[gun_key]["scope"] = f"ScopeKH_{zoom}"

        msg = "KH X4" if self.state["hybrid_mode"] == "Scope4" else "KH X1"
        self.signal_message.emit("SCOPE", msg)

        self._sync_executor()
        self.signal_update.emit(self.state)

    def reload_config(self):
        self.executor.reload_config()
        self.poller.refresh_settings()
        self.signal_message.emit("SUCCESS", "CONFIG REFRESHED!")

    def apply_capture_mode(self, mode):
        try:
            self.capture.set_capture_mode(mode)
        except Exception:
            pass

    def _on_vision_update(self, data):
        def normalize_scope(name):
            if not name: return "NONE"
            n = str(name).upper()
            if "KH" in n: return "SCOPEKH"
            return n

        new_state = self._copy_state()
        changed = False

        if "ai_status" in data:
            if data["ai_status"] == "ACTIVE":
                self.ai_active_until = time.time() + 0.5
            elif data["ai_status"] == "HIBERNATE":
                self.ai_active_until = 0.0

            if new_state.get("ai_status") != data["ai_status"]:
                new_state["ai_status"] = data["ai_status"]
                changed = True

        if "stance" in data:
            if time.time() > self.stance_lock_until:
                self.stance_buffer.append(data["stance"])
                if len(self.stance_buffer) > 3:
                    self.stance_buffer.pop(0)

                if len(self.stance_buffer) == 3 and all(s == self.stance_buffer[0] for s in self.stance_buffer):
                    target_stance = self.stance_buffer[0]
                    if new_state.get("stance") != target_stance:
                        new_state["stance"] = target_stance
                        changed = True

        active_slot = new_state.get("active_slot", 1)
        
        for slot_num in [1, 2]:
            key = f"gun{slot_num}"
            if key in data and data[key]:
                partial_weapon = data[key]
                old_weapon = self.state.get(key, {})
                
                old_scope_raw = old_weapon.get("scope", "NONE") if isinstance(old_weapon, dict) else "NONE"
                old_scope_norm = normalize_scope(old_scope_raw)
                
                new_scope_raw = partial_weapon.get("scope", old_scope_raw)
                new_scope_norm = normalize_scope(new_scope_raw)

                new_name = partial_weapon.get("name", "NONE")
                if new_name == "NONE":
                    self.weapon_buffers[key].append("NONE")
                    if len(self.weapon_buffers[key]) < 2:
                        partial_weapon["name"] = old_weapon.get("name", "NONE")
                    if len(self.weapon_buffers[key]) > 5:
                        self.weapon_buffers[key].pop(0)
                else:
                    self.weapon_buffers[key] = []

                merged_weapon = {**old_weapon, **partial_weapon} if isinstance(old_weapon, dict) else partial_weapon
                
                if slot_num == active_slot:
                    old_name = old_weapon.get("name", "NONE") if isinstance(old_weapon, dict) else "NONE"
                    new_name = partial_weapon.get("name", old_name)
                    
                    if new_name != old_name or new_scope_norm != old_scope_norm:
                        if new_scope_norm == "SCOPEKH":
                            new_state["hybrid_mode"] = "Scope1"
                        changed = True

                if new_scope_norm == "SCOPEKH":
                    zoom = "1" if new_state["hybrid_mode"] == "Scope1" else "4"
                    merged_weapon["scope"] = f"ScopeKH_{zoom}"

                new_state[key] = merged_weapon
                changed = True

        if changed:
            new_state["firing"] = self.state.get("firing", False)
            new_state["paused"] = self.state.get("paused", False)
            new_state["active_slot"] = self.state.get("active_slot", 1)
            
            self.state = new_state
            self._sync_executor()
            self.signal_update.emit(self._copy_state())
            
            slot = self.state.get("active_slot", 1)
            gun_info = self.state.get(f"gun{slot}", {})
            if normalize_scope(gun_info.get("scope")) == "SCOPEKH":
                msg = "KH X4" if self.state.get("hybrid_mode") == "Scope4" else "KH X1"
                self.signal_message.emit("SCOPE", msg)

    def set_slot(self, slot):
        self.state["paused"] = False
        if self.state.get("active_slot") != slot:
            self.state["active_slot"] = slot
        self._sync_executor()
        self.signal_update.emit(self._copy_state())

    def set_paused(self, paused):
        self.state["paused"] = paused
        self.signal_update.emit(self._copy_state())

    def set_firing(self, is_firing):
        if self.state.get("firing") != is_firing:
            self.state["firing"] = is_firing
            self.signal_update.emit(self._copy_state())

    def set_stance_by_key(self, stance):
        if stance == "Crouch" and self.state.get("stance") == "Crouch":
            stance = "Stand"
        elif stance == "Prone" and self.state.get("stance") == "Prone":
            stance = "Stand"
        
        self.state["stance"] = stance
        self.stance_buffer = [stance] * 3
        self.stance_lock_until = time.time() + 0.8
        
        if self.executor:
            self.executor.live_stance = stance
            
        self.signal_update.emit(self._copy_state())

    def stop(self):
        self.running = False
        self.vision_worker.running = False
        self.poller.running = False
        self.quit()


class EngineCoreNativeInputBridge:
    def __init__(self):
        self.dll = None
        self.available = False
        self._load()

    def _load(self):
        try:
            dll_path = get_resource_path(os.path.join("native", "EngineCore.dll"))
            if not os.path.exists(dll_path):
                return
            self.dll = ctypes.CDLL(dll_path)
            self.dll.EngineCore_SetInputScreenMetrics.argtypes = [ctypes.c_int, ctypes.c_int]
            self.dll.EngineCore_SetInputScreenMetrics.restype = None
            self.dll.EngineCore_ConfigureFastLoot.argtypes = [ctypes.POINTER(EngineCoreFastLootConfig)]
            self.dll.EngineCore_ConfigureFastLoot.restype = ctypes.c_int
            self.dll.EngineCore_ConfigureSlide.argtypes = [ctypes.POINTER(EngineCoreSlideConfig)]
            self.dll.EngineCore_ConfigureSlide.restype = ctypes.c_int
            self.dll.EngineCore_SetFastLootEnabled.argtypes = [ctypes.c_int]
            self.dll.EngineCore_SetFastLootEnabled.restype = None
            self.dll.EngineCore_SetSlideEnabled.argtypes = [ctypes.c_int]
            self.dll.EngineCore_SetSlideEnabled.restype = None
            self.dll.EngineCore_OnKeyEvent.argtypes = [ctypes.c_ushort, ctypes.c_int, ctypes.c_int]
            self.dll.EngineCore_OnKeyEvent.restype = None
            self.dll.EngineCore_StopFastLoot.argtypes = []
            self.dll.EngineCore_StopFastLoot.restype = None
            self.dll.EngineCore_StopSlide.argtypes = []
            self.dll.EngineCore_StopSlide.restype = None
            self.available = True
        except Exception:
            self.dll = None
            self.available = False

    def apply_settings(self, fast_loot_enabled: bool, fast_loot_key: str, slide_enabled: bool):
        if not self.available or self.dll is None:
            return False

        screen_w = int(win32api.GetSystemMetrics(0))
        screen_h = int(win32api.GetSystemMetrics(1))
        self.dll.EngineCore_SetInputScreenMetrics(screen_w, screen_h)

        fast_loot_cfg = EngineCoreFastLootConfig(
            int(bool(fast_loot_enabled)),
            int(gui_key_to_vk(fast_loot_key)),
            0x49,
            screen_w,
            screen_h,
            133,
            149,
            61,
            938,
            504,
            7,
            150,
            2,
            50,
            1,
        )
        slide_cfg = EngineCoreSlideConfig(
            int(bool(slide_enabled)),
            ord("C"),
            ord("C"),
            0x10,
            0xA0,
            0xA1,
            ord("W"),
            ord("A"),
            ord("D"),
            200,
            10,
            20,
            30,
            10,
            80,
            1,
        )

        if not self.dll.EngineCore_ConfigureFastLoot(ctypes.byref(fast_loot_cfg)):
            return False
        if not self.dll.EngineCore_ConfigureSlide(ctypes.byref(slide_cfg)):
            return False

        self.dll.EngineCore_SetFastLootEnabled(int(bool(fast_loot_enabled)))
        self.dll.EngineCore_SetSlideEnabled(int(bool(slide_enabled)))
        return True

    def on_key_event(self, key_name: str, pressed: bool):
        if not self.available or self.dll is None:
            return
        vk = int(gui_key_to_vk(key_name))
        if vk <= 0:
            return
        try:
            self.dll.EngineCore_OnKeyEvent(vk, int(bool(pressed)), 0)
        except Exception:
            pass

    def stop(self):
        if not self.available or self.dll is None:
            return
        try:
            self.dll.EngineCore_StopFastLoot()
            self.dll.EngineCore_StopSlide()
        except Exception:
            pass

if __name__ == "__main__":
    # Đã làm sạch chú thích lỗi mã hóa.
    set_high_dpi()
    _self_elevate_and_whitelist()
    _optimize_cpu_and_priority()

    
    # Đã làm sạch chú thích lỗi mã hóa.
    # print_banner()
    # print(" > [SYSTEM] Initializing environment...")

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon
    from PyQt6.QtCore import QThread, pyqtSignal, QObject


    # Đã làm sạch chú thích lỗi mã hóa.
    myappid = 'di88.phutho.macro.v1'
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    timer_enforcer = HighPrecisionTimer()
    timer_enforcer.start()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Di88-VP")
    app.setApplicationDisplayName("Macro & Aim By Di88")

    icon_path = get_resource_path("di88vp.ico")

    if UI_ONLY_MODE:
        w = win32api.GetSystemMetrics(0)
        h = win32api.GetSystemMetrics(1)
        dialog_result = ResolutionNoticeDialog(f"{w}x{h}").exec()
        if dialog_result != QDialog.DialogCode.Accepted:
            sys.exit(0)
        window = MacroWindow()
        window.setWindowTitle("Macro & Aim By Di88")
        window.setWindowIcon(QIcon(icon_path))
        window.show()
        print(" > [SYSTEM] UI Preview is Ready!")
        exit_code = app.exec()
        sys.exit(exit_code)
    
    

    # Đã làm sạch chú thích lỗi mã hóa.
    w = win32api.GetSystemMetrics(0)
    h = win32api.GetSystemMetrics(1)
    dialog_result = ResolutionNoticeDialog(f"{w}x{h}").exec()
    if dialog_result != QDialog.DialogCode.Accepted:
        sys.exit(0)

    window = MacroWindow()
    window.setWindowTitle("Macro & Aim By Di88")
    window.setWindowIcon(QIcon(icon_path))

    backend = BackendThread()
    backend.signal_update.connect(window.update_ui_state)
    backend.signal_message.connect(window.show_message)
    backend.signal_ads_update.connect(window.update_ads_display)
    # Đã làm sạch chú thích lỗi mã hóa.
    initial_ads = getattr(backend.pubg_config, 'ads_mode', None)
    if initial_ads:
        window.update_ads_display(initial_ads.upper())
    window.set_backend(backend)
    window.signal_settings_changed.connect(backend.reload_config)
    
    # Đã làm sạch chú thích lỗi mã hóa.
    class InputBridge(QObject):
        def __init__(self, window, backend):
            super().__init__()
            self.window = window
            self.backend = backend
            self.settings = SettingsManager()
            self.recoil_config = self.backend.executor.config
            self.is_ads = False
            self.ads_toggled = False
            self._ads_reset_timer = None
            self.native_input_bridge = EngineCoreNativeInputBridge()
            self.reload_config()

        def reload_config(self):
            self.guitoggle_key = (
                self.window.btn_guitoggle.text().strip().lower()
                if hasattr(self.window, "btn_guitoggle") and self.window.btn_guitoggle
                else self.settings.get("keybinds.gui_toggle", "f1").lower()
            )
            self.fast_loot_key = (
                self.window.btn_fastloot_key.text().strip().lower()
                if hasattr(self.window, "btn_fastloot_key") and self.window.btn_fastloot_key
                else self.settings.get("fast_loot_key", "caps_lock").lower()
            )
            self.fast_loot_enabled = (
                hasattr(self.window, "btn_fastloot_toggle")
                and self.window.btn_fastloot_toggle
                and self.window.btn_fastloot_toggle.text().upper() == "ON"
            )
            self.slide_trick_enabled = (
                hasattr(self.window, "btn_slide_toggle")
                and self.window.btn_slide_toggle
                and self.window.btn_slide_toggle.text().upper() == "ON"
            )
            if hasattr(self, "keyboard_listener") and self.keyboard_listener:
                self.keyboard_listener.update_guitoggle_key(self.guitoggle_key)
            native_ok = self.native_input_bridge.apply_settings(
                fast_loot_enabled=self.fast_loot_enabled,
                fast_loot_key=self.fast_loot_key,
                slide_enabled=self.slide_trick_enabled,
            )
            self.backend.native_input_bridge_active = bool(native_ok)

        def handle_input_action(self, action):
            if not is_game_active():
                return
            if action == "SLOT_1":
                self.backend.set_slot(1)
                self.window.update_macro_style(True)
            elif action == "SLOT_2":
                self.backend.set_slot(2)
                self.window.update_macro_style(True)
            if action == "MACRO_PAUSE":
                self.backend.set_paused(True)
                self.window.update_macro_style(False)

        def handle_raw_key(self, key, pressed):
            if key == self.guitoggle_key and pressed:
                if self.window.isVisible():
                    self.window.hide()
                else:
                    self.window.restore_window()
                return
            if self.backend.native_input_bridge_active:
                self.native_input_bridge.on_key_event(key, pressed)
            if pressed and not is_game_active():
                return
            elif key == "f2" and pressed:
                self.backend.reload_config()
            elif key == "r" and pressed:
                pubg_ads = getattr(self.backend.pubg_config, 'ads_mode', None)
                ads_mode = pubg_ads.upper() if pubg_ads else self.settings.get("ads_mode", "HOLD").upper()
                if ads_mode in ["CLICK", "TOGGLE"]:
                    self.is_ads = False
                    if hasattr(self.window, 'crosshair') and self.window.crosshair:
                        self.window.crosshair.reset_toggle_state()

        def handle_mouse_click(self, btn, pressed):
            btn_name = str(btn).lower()
            if btn_name == "right":
                pubg_ads = getattr(self.backend.pubg_config, 'ads_mode', None)
                ads_mode = pubg_ads.upper() if pubg_ads else self.settings.get("ads_mode", "HOLD").upper()
                if ads_mode == "HOLD":
                    self.is_ads = pressed
                elif ads_mode in ["CLICK", "TOGGLE"]:
                    self.is_ads = True
                    if pressed and self._ads_reset_timer and self._ads_reset_timer.is_alive():
                        self._ads_reset_timer.cancel()
                        self._ads_reset_timer = None

            if btn_name == "left" and pressed:
                if self._ads_reset_timer and self._ads_reset_timer.is_alive():
                    self._ads_reset_timer.cancel()
                    self._ads_reset_timer = None
                flags, _, _ = win32gui.GetCursorInfo()
                cursor_visible = (flags != 0)

                if not Utils.is_game_active() or cursor_visible:
                    return

                pubg_ads = getattr(self.backend.pubg_config, 'ads_mode', None)
                ads_mode = pubg_ads.upper() if pubg_ads else self.settings.get("ads_mode", "HOLD").upper()
                if ads_mode == "HOLD" and not self.is_ads:
                    return

                data = self.backend.state
                if data.get("paused", False):
                    return

                slot = data.get("active_slot", 1)
                gun_info = data.get(f"gun{slot}", {})
                name = gun_info.get("name", "NONE")
                if name != "NONE":
                    self.backend.set_firing(True)
                    base_table = self.recoil_config.get_base_table(name)
                    if base_table:
                        raw_pixels = self.recoil_config.get_raw_pattern(base_table)
                        self.backend.executor.start_recoil(raw_pixels, initial_stance=data.get("stance", "Stand"))
            elif btn_name == "left" and not pressed:
                self.backend.set_firing(False)
                self.backend.executor.stop_recoil()
                if self.backend.executor.full_pattern_done:
                    pubg_ads = getattr(self.backend.pubg_config, 'ads_mode', None)
                    ads_mode = pubg_ads.upper() if pubg_ads else self.settings.get("ads_mode", "HOLD").upper()
                    if ads_mode in ["CLICK", "TOGGLE"]:
                        def _reset_after_empty_mag():
                            self.is_ads = False
                            if hasattr(self.window, 'crosshair') and self.window.crosshair:
                                self.window.crosshair.reset_toggle_state()
                        QTimer.singleShot(0, _reset_after_empty_mag)

    input_bridge = InputBridge(window, backend)
    window.signal_settings_changed.connect(input_bridge.reload_config)

    keyboard_listener = KeyboardListener()
    input_bridge.keyboard_listener = keyboard_listener
    keyboard_listener.signal_key_event.connect(input_bridge.handle_raw_key)
    keyboard_listener.signal_action.connect(input_bridge.handle_input_action)
    keyboard_listener.start_listening()

    mouse_listener = MouseListener()
    mouse_listener.signal_click.connect(input_bridge.handle_mouse_click)
    mouse_listener.start_listening()

    window.set_runtime_handles(
        keyboard_listener=keyboard_listener,
        mouse_listener=mouse_listener,
        native_input_worker=input_bridge.native_input_bridge,
        timers=[timer_enforcer],
    )

    def exception_hook(exctype, value, tb):
        import traceback
        err_msg = "".join(traceback.format_exception(exctype, value, tb))
        print(f"\n> [CRASH REPORT]\n{err_msg}")
        timer_enforcer.stop()
        sys.exit(1)
    sys.excepthook = exception_hook

    backend.start()
    window.restore_window()
    
    print(" > [SYSTEM] Macro DI88-VP is Ready.")
    # sys.stdout.write("\n") # Chừa dòng cho Status Bar Động
    exit_code = app.exec()
    sys.exit(exit_code)

# ===== MAU PYTHON ARCHIVE START =====
# Archived Python sources from sample folder for one-file migration/reference.
# --- BEGIN FILE: AimAI/__init__.py ---
# from .ClassAimBridge import AimBridge
# from .ClassAimConfig import AimIntegrationConfig
# from .ClassAimDefaults import build_detect_aim_defaults, build_detect_aim_schema
# 
# __all__ = [
#     "AimBridge",
#     "AimIntegrationConfig",
#     "build_detect_aim_defaults",
#     "build_detect_aim_schema",
# ]
# --- END FILE: AimAI/__init__.py ---

# SAMPLE AIM LOGIC FOR NATIVE MIGRATION
# --- BEGIN FILE: AimAI/ClassAimBridge.py ---
# from __future__ import annotations
# 
# import ctypes
# from dataclasses import dataclass, field
# from pathlib import Path
# from types import SimpleNamespace
# from typing import Any
# 
# from AimAI.ClassAimConfig import AimIntegrationConfig
# from AimAI.ClassAimDefaults import build_detect_aim_defaults
# from AimAI.Integration.ClassAimNativeDllBridge import AimNativeDllBridge
# from Core.ClassAssetPack import get_asset_pack
# 
# NATIVE_PROVIDER = "DirectML"
# NATIVE_BACKEND_LABEL = "DirectML (GPU)"
# 
# 
# @dataclass(slots=True)
# class AimRuntimeSnapshot:
#     status: str
#     enabled: bool
#     safe_mode: bool
#     output_backend: str
#     capture_backend: str
#     inference_backend: str
#     model: str
#     fps: float
#     source_fps: float
#     inference_ms: float
#     capture_ms: float
#     preprocess_ms: float
#     postprocess_ms: float
#     loop_ms: float
#     detections: int
#     processed_frames: int
#     last_error: str
#     runtime_source: str
#     native_required: bool
#     native_ready: bool
#     native_error: str
#     native_failures: int
# 
#     def to_dict(self) -> dict:
#         return {
#             "status": self.status,
#             "enabled": self.enabled,
#             "safe_mode": self.safe_mode,
#             "output_backend": self.output_backend,
#             "capture_backend": self.capture_backend,
#             "inference_backend": self.inference_backend,
#             "model": self.model,
#             "fps": self.fps,
#             "source_fps": self.source_fps,
#             "inference_ms": self.inference_ms,
#             "capture_ms": self.capture_ms,
#             "preprocess_ms": self.preprocess_ms,
#             "postprocess_ms": self.postprocess_ms,
#             "loop_ms": self.loop_ms,
#             "detections": self.detections,
#             "processed_frames": self.processed_frames,
#             "last_error": self.last_error,
#             "runtime_source": self.runtime_source,
#             "native_required": self.native_required,
#             "native_ready": self.native_ready,
#             "native_error": self.native_error,
#             "native_failures": self.native_failures,
#         }
# 
# 
# @dataclass(slots=True)
# class AimUiSettings:
#     bindings: dict[str, str] = field(default_factory=dict)
#     sliders: dict[str, Any] = field(default_factory=dict)
#     toggles: dict[str, bool] = field(default_factory=dict)
#     dropdowns: dict[str, str] = field(default_factory=dict)
#     colors: dict[str, str] = field(default_factory=dict)
#     file_locations: dict[str, str] = field(default_factory=dict)
#     last_loaded_model: str = "N/A"
#     last_loaded_config: str = "N/A"
# 
# 
# class _StatusValue:
#     def __init__(self, value: str) -> None:
#         self.value = value
# 
# 
# class _ControllerShim:
#     def __init__(self) -> None:
#         self.state = SimpleNamespace(
#             enabled=False,
#             safe_mode=False,
#             backend_name="native_dll",
#             last_error="",
#         )
#         self._status = "idle"
# 
#     def get_status(self) -> _StatusValue:
#         return _StatusValue(self._status)
# 
#     def set_status(self, status: str) -> None:
#         self._status = status
# 
# 
# class _HotkeyShim:
#     def __init__(self, bridge: "AimBridge") -> None:
#         self.bridge = bridge
#         self._pressed_toggle_keys: set[str] = set()
# 
#     def toggle_aim_assist(self) -> None:
#         self.bridge.toggle_aim_assist()
# 
#     def toggle_auto_trigger(self) -> None:
#         self.bridge.toggle_auto_trigger()
# 
#     def handle_press(self, key_name: str) -> None:
#         normalized = self.bridge.normalize_binding(key_name)
#         if normalized == self.bridge.normalize_binding(
#             self.bridge.settings.bindings.get("Emergency Stop Keybind", "f8")
#         ):
#             if normalized not in self._pressed_toggle_keys:
#                 self._pressed_toggle_keys.add(normalized)
#                 self.bridge.toggle_aim_assist()
#             return
#         if normalized == self.bridge.normalize_binding(
#             self.bridge.settings.bindings.get("Toggle Trigger Keybind", "f7")
#         ):
#             if normalized not in self._pressed_toggle_keys:
#                 self._pressed_toggle_keys.add(normalized)
#                 self.bridge.toggle_auto_trigger()
#             return
#         self.bridge.set_binding_pressed(normalized, True)
# 
#     def handle_release(self, key_name: str) -> None:
#         normalized = self.bridge.normalize_binding(key_name)
#         self._pressed_toggle_keys.discard(normalized)
#         self.bridge.set_binding_pressed(normalized, False)
# 
# 
# class AimBridge:
#     def __init__(self, detect_root: Path | None = None) -> None:
#         self.detect_root = detect_root or Path(__file__).resolve().parents[1]
#         self.settings = self._build_default_settings()
#         self.asset_pack = get_asset_pack()
#         self.controller = _ControllerShim()
#         self.hotkeys = _HotkeyShim(self)
#         self.context = self
#         self.native = AimNativeDllBridge(self.detect_root)
#         self._native_loaded = False
#         self._native_model_loaded = False
#         self._native_error = ""
#         self._running = False
#         self._primary_pressed = False
#         self._secondary_pressed = False
#         self._capture_backend = "DirectX"
#         self._native_failures = 0
#         self._last_status: dict[str, object] = {}
# 
#     def apply_detect_settings(self, settings: dict) -> AimRuntimeSnapshot:
#         was_running = self._running
#         config = AimIntegrationConfig.from_detect_settings(settings)
#         self._apply_config(config)
#         self._ensure_native_loaded()
# 
#         selected_model = self._resolve_effective_model_name(config)
#         if selected_model:
#             self.settings.last_loaded_model = selected_model
# 
#         self._capture_backend = str(config.runtime.get("capture_backend", "DirectX") or "DirectX")
#         self.settings.dropdowns["Screen Capture Method"] = self._capture_backend
# 
#         self.native.configure(
#             self.settings.last_loaded_model,
#             self._capture_backend,
#             NATIVE_BACKEND_LABEL,
#         )
#         self._load_native_model_or_raise(self.settings.last_loaded_model)
#         self._push_native_settings()
# 
#         if was_running or bool(config.runtime.get("auto_start")):
#             self._running = True
#             self.controller.set_status("running")
#             self.controller.state.enabled = bool(self.settings.toggles.get("Aim Assist", False))
#             self.native.start()
#             self.native.start_capture_loop()
#         return self.snapshot()
# 
#     def reload_from_detect_settings(self, settings: dict) -> AimRuntimeSnapshot:
#         config = AimIntegrationConfig.from_detect_settings(settings)
#         auto_start = bool(config.runtime.get("auto_start", False))
#         if self._running and not auto_start:
#             self.stop_runtime()
#         return self.apply_detect_settings(settings)
# 
#     def start_runtime(self) -> AimRuntimeSnapshot:
#         self._require_native_ready()
#         self._running = True
#         self.controller.set_status("running")
#         self.controller.state.enabled = bool(self.settings.toggles.get("Aim Assist", False))
#         self._push_native_settings()
#         self.native.start()
#         self.native.start_capture_loop()
#         return self.snapshot()
# 
#     def stop_runtime(self) -> AimRuntimeSnapshot:
#         self._running = False
#         self._primary_pressed = False
#         self._secondary_pressed = False
#         try:
#             self.native.stop()
#         except Exception as exc:
#             self._native_error = str(exc)
#         self.controller.set_status("idle")
#         self.controller.state.enabled = False
#         return self.snapshot()
# 
#     def toggle_aim_assist(self) -> AimRuntimeSnapshot:
#         enabled = not bool(self.settings.toggles.get("Aim Assist", False))
#         self.settings.toggles["Aim Assist"] = enabled
#         self.controller.state.enabled = enabled
#         self._push_native_settings()
#         return self.snapshot()
# 
#     def toggle_auto_trigger(self) -> AimRuntimeSnapshot:
#         enabled = not bool(self.settings.toggles.get("Auto Trigger", False))
#         self.settings.toggles["Auto Trigger"] = enabled
#         self._push_native_settings()
#         return self.snapshot()
# 
#     def warmup_inference(self, runs: int = 2) -> None:
#         self._require_native_ready()
#         self.native.run_warmup_inference(max(1, int(runs)))
# 
#     def snapshot(self) -> AimRuntimeSnapshot:
#         status: dict[str, object] = {}
#         try:
#             if self._native_loaded:
#                 status = self.native.status()
#                 self._native_error = str(status.get("last_error", "") or "")
#                 self._last_status = status
#         except Exception as exc:
#             self._native_failures += 1
#             self._native_error = str(exc)
# 
#         backend = str(status.get("backend", "") or NATIVE_BACKEND_LABEL)
#         native_ready = bool(self._native_loaded and self._native_model_loaded and not self._native_error)
#         status_text = "running" if self._running else "idle"
#         if self._native_error:
#             status_text = "error" if not self._running else "running"
#         return AimRuntimeSnapshot(
#             status=status_text,
#             enabled=bool(self.settings.toggles.get("Aim Assist", False)),
#             safe_mode=False,
#             output_backend="native_dll",
#             capture_backend=self._capture_backend,
#             inference_backend=f"Native DLL / {backend}",
#             model=self.settings.last_loaded_model,
#             fps=round(float(status.get("fps", 0.0) or 0.0), 2) if self._running else 0.0,
#             source_fps=round(float(status.get("source_fps", 0.0) or 0.0), 2) if self._running else 0.0,
#             inference_ms=round(float(status.get("latency_ms", 0.0) or 0.0), 2) if self._running else 0.0,
#             capture_ms=round(float(status.get("capture_ms", 0.0) or 0.0), 2) if self._running else 0.0,
#             preprocess_ms=0.0,
#             postprocess_ms=0.0,
#             loop_ms=round(float(status.get("loop_ms", status.get("latency_ms", 0.0)) or 0.0), 2) if self._running else 0.0,
#             detections=int(status.get("detection_count", 0) or 0),
#             processed_frames=int(status.get("processed_frames", 0) or 0),
#             last_error=self._native_error,
#             runtime_source="Native DLL" if native_ready else "Native DLL Error",
#             native_required=True,
#             native_ready=native_ready,
#             native_error=self._native_error,
#             native_failures=self._native_failures,
#         )
# 
#     def set_binding_pressed(self, normalized_key: str, pressed: bool) -> None:
#         primary = self.normalize_binding(self.settings.bindings.get("Aim Keybind", "right"))
#         secondary = self.normalize_binding(self.settings.bindings.get("Second Aim Keybind", "ctrl"))
#         if normalized_key == primary:
#             self._primary_pressed = bool(pressed)
#             self._push_native_settings()
#         elif normalized_key == secondary:
#             self._secondary_pressed = bool(pressed)
#             self._push_native_settings()
# 
#     @staticmethod
#     def normalize_binding(key_name: object) -> str:
#         normalized = str(key_name or "").strip().lower().replace(" ", "_")
#         aliases = {
#             "right_mouse": "right",
#             "left_mouse": "left",
#             "middle_mouse": "middle",
#             "left_ctrl": "ctrl",
#             "right_ctrl": "ctrl",
#             "ctrl_l": "ctrl",
#             "ctrl_r": "ctrl",
#             "control_l": "ctrl",
#             "control_r": "ctrl",
#             "left_shift": "shift",
#             "right_shift": "shift",
#             "shift_l": "shift",
#             "shift_r": "shift",
#         }
#         return aliases.get(normalized, normalized)
# 
#     def _apply_config(self, config: AimIntegrationConfig) -> None:
#         self.settings.bindings = dict(config.bindings)
#         self.settings.sliders = self._normalize_slider_values(config.sliders)
#         self.settings.toggles = dict(config.toggles)
#         self.settings.dropdowns = dict(config.dropdowns)
#         self.settings.colors = dict(config.colors)
#         self.settings.file_locations = dict(config.file_locations)
#         self.settings.last_loaded_model = str(config.meta.get("last_loaded_model", "N/A"))
#         self.settings.last_loaded_config = str(config.meta.get("last_loaded_config", "N/A"))
# 
#     def _ensure_native_loaded(self) -> None:
#         if self._native_loaded:
#             return
#         self.native.load()
#         self._native_loaded = True
#         self._native_error = ""
# 
#     def _load_native_model_or_raise(self, model_name: str) -> None:
#         model_path = self._resolve_model_path(model_name)
#         if not model_name or model_name.upper() == "N/A" or not model_path.exists():
#             raise RuntimeError(f"Native model not found: {model_path}")
#         self.native.load_model(model_path, provider=NATIVE_PROVIDER)
#         self._native_model_loaded = True
#         self._native_error = ""
# 
#     def _push_native_settings(self) -> None:
#         if not self._native_loaded:
#             return
#         left, top, width, height = self._fov_capture_region()
#         self.native.set_capture_target(left, top, width, height)
#         self.native.set_detection_settings(
#             min_confidence=self._minimum_confidence_ratio(),
#             max_detections=64,
#             target_fps=self._target_fps(),
#         )
#         screen_left, screen_top, screen_width, screen_height = self._screen_geometry()
#         _ = screen_left, screen_top
#         aim_should_move = bool(self.settings.toggles.get("Aim Assist", False)) and (
#             bool(self.settings.toggles.get("Constant AI Tracking", False))
#             or self._primary_pressed
#             or self._secondary_pressed
#         )
#         self.native.set_aim_settings(
#             screen_width=screen_width,
#             screen_height=screen_height,
#             primary_aim_position=float(self.settings.sliders.get("Primary Aim Position", 50)),
#             secondary_aim_position=float(self.settings.sliders.get("Secondary Aim Position", 50)),
#             mouse_sensitivity=float(self.settings.sliders.get("Mouse Sensitivity (+/-)", 1.0)),
#             ema_smoothing=float(self.settings.sliders.get("EMA Smoothening", 0.5)),
#             mouse_jitter=int(float(self.settings.sliders.get("Mouse Jitter", 0))),
#             head_priority=str(self.settings.dropdowns.get("Target Priority", "Body -> Head")) == "Head -> Body",
#             aim_enabled=aim_should_move,
#             output_enabled=aim_should_move,
#         )
#         self._push_native_visual_settings()
# 
#     def apply_visual_settings(self, visual_state: dict[str, object] | None) -> None:
#         if not self._native_loaded:
#             return
#         visual_state = visual_state or {}
#         self.native.set_visual_settings(
#             show_fov=bool(visual_state.get("show_fov", self.settings.toggles.get("Show FOV", False))),
#             show_detect=bool(visual_state.get("show_detect", self.settings.toggles.get("Show Detected Player", False))),
#             show_confidence=bool(visual_state.get("show_confidence", self.settings.toggles.get("Show AI Confidence", False))),
#             show_tracers=bool(visual_state.get("show_tracers", self.settings.toggles.get("Show Tracers", False))),
#             fov_size=int(float(visual_state.get("fov_size", self.settings.sliders.get("FOV Size", 300)) or 300)),
#             fov_color_argb=self._argb_hex_to_uint(
#                 visual_state.get("fov_color", self.settings.colors.get("FOV Color", "#FF8080FF")),
#                 0xFFFF8080,
#             ),
#             detect_color_argb=self._argb_hex_to_uint(
#                 visual_state.get("detect_color", self.settings.colors.get("Detected Player Color", "#FFFF4040")),
#                 0xFFFF4040,
#             ),
#             border_thickness=int(float(visual_state.get("border_thickness", self.settings.sliders.get("Border Thickness", 2)) or 2)),
#             opacity=float(visual_state.get("opacity", self.settings.sliders.get("Opacity", 1.0)) or 1.0),
#         )
# 
#     def _push_native_visual_settings(self) -> None:
#         self.apply_visual_settings(
#             {
#                 "show_fov": self.settings.toggles.get("Show FOV", False),
#                 "show_detect": self.settings.toggles.get("Show Detected Player", False),
#                 "show_confidence": self.settings.toggles.get("Show AI Confidence", False),
#                 "show_tracers": self.settings.toggles.get("Show Tracers", False),
#                 "fov_size": self.settings.sliders.get("FOV Size", 300),
#                 "fov_color": self.settings.colors.get("FOV Color", "#FF8080FF"),
#                 "detect_color": self.settings.colors.get("Detected Player Color", "#FFFF4040"),
#                 "border_thickness": self.settings.sliders.get("Border Thickness", 2),
#                 "opacity": self.settings.sliders.get("Opacity", 1.0),
#             }
#         )
# 
#     def _require_native_ready(self) -> None:
#         self._ensure_native_loaded()
#         if not self._native_model_loaded:
#             raise RuntimeError("Native DLL model is not loaded")
# 
#     def _resolve_effective_model_name(self, config: AimIntegrationConfig) -> str:
#         available = set(self._list_models())
#         runtime_model = str(config.runtime.get("model", "") or "").strip()
#         if runtime_model and runtime_model in available:
#             return runtime_model
#         last_model = str(config.meta.get("last_loaded_model", "") or "").strip()
#         if last_model and last_model.upper() != "N/A" and last_model in available:
#             return last_model
#         ordered = self._list_models()
#         return ordered[0] if ordered else runtime_model or last_model
# 
#     def _list_models(self) -> list[str]:
#         if self.asset_pack.available:
#             packed_models = self.asset_pack.list_files("bin/models", (".onnx",))
#             if packed_models:
#                 return sorted(Path(path).name for path in packed_models)
#         model_dir = self.detect_root / "bin" / "models"
#         if not model_dir.exists():
#             return []
#         return sorted(path.name for path in model_dir.glob("*.onnx") if path.is_file())
# 
#     def _resolve_model_path(self, model_name: str) -> Path:
#         packed_path = f"bin/models/{model_name}"
#         if self.asset_pack.available and self.asset_pack.has_file(packed_path):
#             return self.asset_pack.extract_to_cache(packed_path)
#         return self.detect_root / "bin" / "models" / model_name
# 
#     def _minimum_confidence_ratio(self) -> float:
#         try:
#             return max(0.0, min(1.0, float(self.settings.sliders.get("AI Minimum Confidence", 45)) / 100.0))
#         except Exception:
#             return 0.45
# 
#     def _target_fps(self) -> int:
#         for key in ("Capture FPS", "Target FPS"):
#             try:
#                 value = int(float(self.settings.sliders.get(key, 0)))
#                 if value > 0:
#                     return max(30, min(240, value))
#             except Exception:
#                 continue
#         return 144
# 
#     @staticmethod
#     def _argb_hex_to_uint(value: object, fallback: int) -> int:
#         text = str(value or "").strip()
#         if text.startswith("#"):
#             text = text[1:]
#         if len(text) != 8:
#             return int(fallback)
#         try:
#             return int(text, 16)
#         except ValueError:
#             return int(fallback)
# 
#     def _fov_capture_region(self) -> tuple[int, int, int, int]:
#         _, _, screen_width, screen_height = self._screen_geometry()
#         try:
#             fov_size = int(float(self.settings.sliders.get("FOV Size", 300)))
#         except Exception:
#             fov_size = 300
#         fov_size = max(32, min(min(screen_width, screen_height), fov_size))
#         left = max(0, int((screen_width - fov_size) / 2))
#         top = max(0, int((screen_height - fov_size) / 2))
#         return left, top, fov_size, fov_size
# 
#     @staticmethod
#     def _normalize_slider_values(sliders: dict[str, object]) -> dict[str, object]:
#         normalized = dict(sliders)
#         delay = normalized.get("Auto Trigger Delay")
#         if isinstance(delay, (int, float)) and delay <= 1:
#             normalized["Auto Trigger Delay"] = int(round(float(delay) * 1000.0))
#         return normalized
# 
#     @staticmethod
#     def _screen_geometry() -> tuple[int, int, int, int]:
#         user32 = ctypes.windll.user32
#         width = user32.GetSystemMetrics(0)
#         height = user32.GetSystemMetrics(1)
#         return (0, 0, width, height)
# 
#     @staticmethod
#     def _build_default_settings() -> AimUiSettings:
#         defaults = build_detect_aim_defaults("DirectX")
#         return AimUiSettings(
#             bindings=dict(defaults["bindings"]),
#             sliders=dict(defaults["sliders"]),
#             toggles=dict(defaults["toggles"]),
#             dropdowns=dict(defaults["dropdowns"]),
#             colors=dict(defaults["colors"]),
#             file_locations=dict(defaults["file_locations"]),
#             last_loaded_model=str(defaults["meta"].get("last_loaded_model", "N/A")),
#             last_loaded_config=str(defaults["meta"].get("last_loaded_config", "N/A")),
#         )
# --- END FILE: AimAI/ClassAimBridge.py ---

# --- BEGIN FILE: AimAI/ClassAimConfig.py ---
# from __future__ import annotations
# 
# from dataclasses import dataclass
# from typing import Any
# 
# from AimAI.ClassAimDefaults import build_detect_aim_defaults, merge_aim_settings
# 
# 
# @dataclass(slots=True)
# class AimIntegrationConfig:
#     runtime: dict[str, Any]
#     bindings: dict[str, str]
#     sliders: dict[str, Any]
#     toggles: dict[str, bool]
#     dropdowns: dict[str, str]
#     colors: dict[str, str]
#     file_locations: dict[str, str]
#     minimize: dict[str, bool]
#     meta: dict[str, Any]
# 
#     @classmethod
#     def from_detect_settings(cls, settings: dict) -> "AimIntegrationConfig":
#         aim = settings.get("aim", {}) if isinstance(settings, dict) else {}
#         runtime = aim.get("runtime", {}) if isinstance(aim, dict) else {}
#         dropdowns = aim.get("dropdowns", {}) if isinstance(aim, dict) else {}
#         capture_source = runtime.get("capture_backend") or dropdowns.get("Screen Capture Method") or settings.get("capture_mode", "DirectX")
#         default_capture = _normalize_capture_backend(str(capture_source))
#         defaults = build_detect_aim_defaults(default_capture)
#         merged = merge_aim_settings(defaults, settings.get("aim"))
#         _upgrade_legacy_shape(merged, settings)
#         return cls(
#             runtime=dict(merged["runtime"]),
#             bindings=dict(merged["bindings"]),
#             sliders=dict(merged["sliders"]),
#             toggles=dict(merged["toggles"]),
#             dropdowns=dict(merged["dropdowns"]),
#             colors=dict(merged["colors"]),
#             file_locations=dict(merged["file_locations"]),
#             minimize=dict(merged["minimize"]),
#             meta=dict(merged["meta"]),
#         )
# 
# 
# def _upgrade_legacy_shape(merged: dict, settings: dict) -> None:
#     runtime = merged["runtime"]
#     toggles = merged["toggles"]
#     dropdowns = merged["dropdowns"]
# 
#     capture_source = runtime.get("capture_backend") or dropdowns.get("Screen Capture Method") or settings.get("capture_mode", "DirectX")
#     runtime["capture_backend"] = _normalize_capture_backend(str(capture_source))
#     runtime["output_backend"] = "native_dll"
#     runtime["force_native"] = True
# 
#     toggles["Aim Assist"] = bool(runtime.get("enabled", toggles.get("Aim Assist", False)))
#     toggles["Show FOV"] = bool(merged["toggles"].get("Show FOV", True))
#     toggles["Show Detected Player"] = bool(merged["toggles"].get("Show Detected Player", False))
#     toggles["Auto Trigger"] = bool(merged["toggles"].get("Auto Trigger", False))
#     toggles["Dynamic FOV"] = bool(merged["toggles"].get("Dynamic FOV", False))
# 
#     dropdowns["Screen Capture Method"] = str(runtime["capture_backend"])
#     merged["meta"]["last_loaded_model"] = str(runtime.get("model", merged["meta"].get("last_loaded_model", "N/A")) or "N/A")
# 
# 
# def _normalize_capture_backend(value: str) -> str:
#     normalized = str(value or "DirectX").strip().upper()
#     if normalized == "DIRECTX":
#         return "DirectX"
#     if normalized == "GDI+":
#         return "GDI+"
#     if normalized == "DXCAM":
#         return "DirectX"
#     if normalized in {"MSS", "PIL"}:
#         return "GDI+"
#     return "DirectX"
# --- END FILE: AimAI/ClassAimConfig.py ---

# --- BEGIN FILE: AimAI/ClassAimDefaults.py ---
# from __future__ import annotations
# 
# from copy import deepcopy
# 
# 
# AIMMY_BINDINGS = {
#     "Aim Keybind": "Right",
#     "Second Aim Keybind": "ctrl",
#     "Toggle Trigger Keybind": "F7",
#     "Dynamic FOV Keybind": "Left",
#     "Emergency Stop Keybind": "F8",
#     "Model Switch Keybind": "OemPipe",
# }
# 
# BASE_SLIDERS = {
#     "Q Weight": 1.0,
#     "LQR Sensitivity": 0.0,
#     "Capture FPS": 144,
#     "Target FPS": 144,
# }
# 
# BASE_TOGGLES = {
#     "Color Aim": False,
# }
# 
# BASE_DROPDOWNS = {
#     "Target Order": "Cyan -> Red",
#     "Blood Color": "Pro Green (Best)",
# }
# 
# AIMMY_SLIDERS = {
#     "Suggested Model": "",
#     "SelectedDisplay": 0,
#     "FOV Size": 300,
#     "Dynamic FOV Size": 10,
#     "Mouse Sensitivity (+/-)": 0.80,
#     "Mouse Jitter": 4,
#     "Sticky Aim Threshold": 0,
#     "Y Offset (Up/Down)": 0,
#     "Y Offset (%)": 50,
#     "X Offset (Left/Right)": 0,
#     "X Offset (%)": 50,
#     "EMA Smoothening": 0.5,
#     "Kalman Lead Time": 0.10,
#     "WiseTheFox Lead Time": 0.15,
#     "Shalloe Lead Multiplier": 3.0,
#     "Auto Trigger Delay": 0.1,
#     "Primary Aim Position": 50,
#     "Secondary Aim Position": 50,
#     "AI Minimum Confidence": 45,
#     "AI Confidence Font Size": 20,
#     "Corner Radius": 0,
#     "Border Thickness": 1,
#     "Opacity": 1,
# }
# 
# AIMMY_TOGGLES = {
#     "Aim Assist": False,
#     "Sticky Aim": False,
#     "Constant AI Tracking": False,
#     "Predictions": False,
#     "EMA Smoothening": False,
#     "Enable Model Switch Keybind": True,
#     "Auto Trigger": False,
#     "FOV": False,
#     "Dynamic FOV": False,
#     "Third Person Support": False,
#     "Masking": False,
#     "Show Detected Player": False,
#     "Cursor Check": False,
#     "Spray Mode": False,
#     "Show FOV": True,
#     "Show AI Confidence": False,
#     "Show Tracers": False,
#     "Collect Data While Playing": False,
#     "Auto Label Data": False,
#     "LG HUB Mouse Movement": False,
#     "Mouse Background Effect": True,
#     "Debug Mode": False,
#     "UI TopMost": False,
#     "StreamGuard": False,
#     "X Axis Percentage Adjustment": False,
#     "Y Axis Percentage Adjustment": False,
# }
# 
# AIMMY_MINIMIZE = {
#     "Aim Assist": False,
#     "Aim Config": False,
#     "Predictions": False,
#     "Auto Trigger": False,
#     "FOV Config": False,
#     "ESP Config": False,
#     "Model Settings": False,
#     "Settings Menu": False,
#     "X/Y Percentage Adjustment": False,
#     "Theme Settings": False,
#     "Screen Settings": False,
# }
# 
# AIMMY_DROPDOWNS = {
#     "Prediction Method": "Kalman Filter",
#     "Detection Area Type": "Closest to Center Screen",
#     "Aiming Boundaries Alignment": "Center",
#     "Mouse Movement Method": "Mouse Event",
#     "Screen Capture Method": "DirectX",
#     "Tracer Position": "Bottom",
#     "Movement Path": "Cubic Bezier",
#     "Image Size": "640",
#     "Target Class": "Best Confidence",
#     "Target Priority": "Body -> Head",
#     "FOV Style": "Circle",
# }
# 
# AIMMY_COLORS = {
#     "FOV Color": "#FF8080FF",
#     "Detected Player Color": "#FF00FFFF",
#     "Theme Color": "#FF722ED1",
# }
# 
# AIMMY_FILE_LOCATIONS = {
#     "ddxoft DLL Location": "",
# }
# 
# 
# def build_detect_aim_defaults(default_capture_backend: str = "DirectX") -> dict:
#     bindings = {}
#     bindings.update(AIMMY_BINDINGS)
# 
#     sliders = dict(BASE_SLIDERS)
#     sliders.update(AIMMY_SLIDERS)
# 
#     toggles = dict(BASE_TOGGLES)
#     toggles.update(AIMMY_TOGGLES)
# 
#     dropdowns = dict(BASE_DROPDOWNS)
#     dropdowns.update(AIMMY_DROPDOWNS)
# 
#     colors = {}
#     colors.update(AIMMY_COLORS)
# 
#     file_locations = {}
#     file_locations.update(AIMMY_FILE_LOCATIONS)
# 
#     return {
#         "runtime": {
#             "enabled": False,
#             "auto_start": False,
#             "safe_mode": False,
#             "output_enabled": False,
#             "output_backend": "native_dll",
#             "capture_backend": default_capture_backend,
#             "model": "",
#             "force_native": True,
#         },
#         "bindings": bindings,
#         "sliders": sliders,
#         "toggles": toggles,
#         "dropdowns": dropdowns,
#         "colors": colors,
#         "file_locations": file_locations,
#         "minimize": dict(AIMMY_MINIMIZE),
#         "meta": {
#             "schema_version": 2,
#             "source_of_truth": "Aimmy2/MainWindow + UISections",
#             "last_loaded_model": "N/A",
#             "last_loaded_config": "N/A",
#         },
#     }
# 
# 
# def build_detect_aim_schema() -> dict:
#     return {}
# 
# 
# def normalize_detect_aim_payload(settings: dict) -> bool:
#     aim = settings.get("aim")
#     if not isinstance(aim, dict):
#         return False
# 
#     updated = False
#     runtime = aim.setdefault("runtime", {})
#     toggles = aim.setdefault("toggles", {})
# 
#     runtime_key_map = {
#         "enabled": "enabled",
#         "auto_start": "auto_start",
#         "safe_mode": "safe_mode",
#         "output_enabled": "output_enabled",
#         "output_backend": "output_backend",
#         "capture_backend": "capture_backend",
#         "model": "model",
#         "force_native": "force_native",
#     }
#     toggle_key_map = {
#         "show_fov": "Show FOV",
#         "show_detection": "Show Detected Player",
#         "auto_trigger": "Auto Trigger",
#         "dynamic_fov": "Dynamic FOV",
#     }
# 
#     for old_key, new_key in runtime_key_map.items():
#         if old_key in aim:
#             runtime[new_key] = aim.pop(old_key)
#             updated = True
# 
#     for old_key, new_key in toggle_key_map.items():
#         if old_key in aim:
#             toggles[new_key] = aim.pop(old_key)
#             updated = True
# 
#     return updated
# 
# 
# def merge_aim_settings(defaults: dict, current: dict | None) -> dict:
#     merged = deepcopy(defaults)
#     if not isinstance(current, dict):
#         return merged
#     _deep_update(merged, current)
#     return merged
# 
# 
# def _deep_update(target: dict, source: dict) -> None:
#     for key, value in source.items():
#         if isinstance(value, dict) and isinstance(target.get(key), dict):
#             _deep_update(target[key], value)
#         else:
#             target[key] = value
# --- END FILE: AimAI/ClassAimDefaults.py ---

# --- BEGIN FILE: AimAI/Integration/__init__.py ---
# """Integration package for the UI-facing AIM runtime.
# 
# Keep this package initializer intentionally empty. Importing every integration
# class here creates circular imports when the native-only AimBridge loads the
# DLL bridge.
# """
# --- END FILE: AimAI/Integration/__init__.py ---

# --- BEGIN FILE: AimAI/Integration/ClassAimBindingForwarder.py ---
# from __future__ import annotations
# 
# 
# class AimBindingForwarder:
#     def __init__(self, host) -> None:
#         self.host = host
# 
#     @property
#     def backend(self):
#         return self.host.backend
# 
#     def forward_mouse_binding(self, button_name: str, pressed: bool) -> None:
#         if self.backend.aim_bridge is None:
#             return
# 
#         mapped = {
#             "left": "left",
#             "right": "right",
#             "middle": "middle",
#             "x1": "xbutton1",
#             "x2": "xbutton2",
#         }.get(str(button_name).lower())
#         if not mapped:
#             return
# 
#         if pressed:
#             self.backend.aim_bridge.context.hotkeys.handle_press(mapped)
#         else:
#             self.backend.aim_bridge.context.hotkeys.handle_release(mapped)
#         self.host.refresh_controller.refresh_state(force_emit=True)
# 
#     def forward_key_binding(self, key_name: str, pressed: bool) -> None:
#         if self.backend.aim_bridge is None:
#             return
# 
#         mapped = {
#             "ctrl_l": "ctrl",
#             "ctrl_r": "ctrl",
#             "control_l": "ctrl",
#             "control_r": "ctrl",
#             "shift_l": "shift",
#             "shift_r": "shift",
#             "alt_l": "alt",
#             "alt_r": "alt",
#         }.get(str(key_name).lower(), str(key_name).lower())
# 
#         if pressed:
#             self.backend.aim_bridge.context.hotkeys.handle_press(mapped)
#         else:
#             self.backend.aim_bridge.context.hotkeys.handle_release(mapped)
#         self.host.refresh_controller.refresh_state(force_emit=True)
# --- END FILE: AimAI/Integration/ClassAimBindingForwarder.py ---

# --- BEGIN FILE: AimAI/Integration/ClassAimBridgeManager.py ---
# from __future__ import annotations
# 
# import copy
# import threading
# 
# from AimAI.ClassAimBridge import AimBridge
# from Core.ClassSettings import SettingsManager
# 
# 
# class AimBridgeManager:
#     def __init__(self, host) -> None:
#         self.host = host
# 
#     @property
#     def backend(self):
#         return self.host.backend
# 
#     def ensure_bridge(self):
#         if self.backend.aim_bridge is None:
#             self.backend.aim_bridge = AimBridge()
#         return self.backend.aim_bridge
# 
#     def bootstrap_runtime(self, enable_after_bootstrap: bool = False) -> None:
#         if self.backend._aim_bootstrap_done:
#             if enable_after_bootstrap and self.backend.aim_bridge is not None:
#                 self._toggle_aim_after_bootstrap(self.backend.aim_bridge)
#             return
# 
#         if self.backend._aim_bootstrap_in_progress:
#             self.backend._aim_enable_after_bootstrap = (
#                 self.backend._aim_enable_after_bootstrap or enable_after_bootstrap
#             )
#             return
# 
#         self.backend._aim_bootstrap_in_progress = True
#         self.backend._aim_enable_after_bootstrap = enable_after_bootstrap
#         self.backend.state["aim"] = {
#             **copy.deepcopy(self.backend.state.get("aim", {})),
#             "status": "loading",
#             "enabled": False,
#             "fps": 0.0,
#             "inference_ms": 0.0,
#             "last_error": "",
#         }
#         self.backend.signal_update.emit(copy.deepcopy(self.backend.state))
# 
#         threading.Thread(target=self._bootstrap_worker, daemon=True).start()
# 
#     def _bootstrap_worker(self) -> None:
#         settings = SettingsManager().load()
#         try:
#             prepared = self.host.runtime_preparer.prepare(settings)
#             aim_bridge = AimBridge()
#             snapshot = aim_bridge.reload_from_detect_settings(prepared)
#             aim_bridge.warmup_inference()
#             if self.backend._aim_enable_after_bootstrap and snapshot.status != "running":
#                 snapshot = aim_bridge.start_runtime()
# 
#             if self.backend._aim_enable_after_bootstrap:
#                 self._toggle_aim_after_bootstrap(aim_bridge)
#                 snapshot = aim_bridge.snapshot()
# 
#             self.backend.aim_bridge = aim_bridge
#             self.backend.state["aim"] = self.host.refresh_controller.build_runtime_state(snapshot)
#             self.backend._aim_bootstrap_done = True
#         except Exception as exc:
#             self.backend.state["aim"] = self.host.state_builder.build_error_state(settings, exc)
#         finally:
#             self.backend._aim_bootstrap_in_progress = False
#             self.backend._aim_enable_after_bootstrap = False
#             self.backend.signal_update.emit(copy.deepcopy(self.backend.state))
# 
#     @staticmethod
#     def _toggle_aim_after_bootstrap(aim_bridge: AimBridge) -> None:
#         toggle_key = str(aim_bridge.context.settings.bindings.get("Emergency Stop Keybind", "f8"))
#         aim_bridge.context.hotkeys.handle_press(toggle_key)
#         aim_bridge.context.hotkeys.handle_release(toggle_key)
# 
#     def sync_integration(self, settings_data: dict | None) -> None:
#         try:
#             aim_bridge = self.ensure_bridge()
#             was_running = aim_bridge.context.controller.get_status().value == "running"
#             prepared = self.host.runtime_preparer.prepare(settings_data)
#             prepared.setdefault("aim", {}).setdefault("runtime", {})["auto_start"] = was_running
#             snapshot = aim_bridge.reload_from_detect_settings(prepared)
#             if was_running and snapshot.status != "running":
#                 snapshot = aim_bridge.start_runtime()
#             self.backend.state["aim"] = self.host.refresh_controller.build_runtime_state(snapshot)
#         except Exception as exc:
#             self.backend.state["aim"] = self.host.state_builder.build_error_state(settings_data, exc)
# 
#     def start_runtime(self) -> None:
#         snapshot = self.ensure_bridge().start_runtime()
#         self.backend._aim_bootstrap_done = True
#         self.backend.state["aim"] = self.host.refresh_controller.build_runtime_state(snapshot)
#         self.backend.signal_update.emit(copy.deepcopy(self.backend.state))
# 
#     def stop_runtime(self) -> None:
#         if self.backend.aim_bridge is None:
#             return
# 
#         snapshot = self.backend.aim_bridge.stop_runtime()
#         self.backend.state["aim"] = self.host.refresh_controller.build_runtime_state(snapshot)
#         self.backend.signal_update.emit(copy.deepcopy(self.backend.state))
# 
#     def toggle_aim_assist(self) -> None:
#         if self.backend.aim_bridge is None or bool(getattr(self.backend, "_aim_bootstrap_in_progress", False)):
#             self.bootstrap_runtime(enable_after_bootstrap=True)
#             return
#         current_enabled = bool(self.backend.aim_bridge.context.settings.toggles.get("Aim Assist", False))
#         if not current_enabled and self.backend.aim_bridge.context.controller.get_status().value != "running":
#             self.backend.aim_bridge.start_runtime()
#         snapshot = self.backend.aim_bridge.toggle_aim_assist()
#         if current_enabled and not snapshot.enabled:
#             snapshot = self.backend.aim_bridge.stop_runtime()
#         self.backend.state["aim"] = self.host.refresh_controller.build_runtime_state(snapshot)
#         self.backend.signal_update.emit(copy.deepcopy(self.backend.state))
# 
#     def toggle_auto_trigger(self) -> None:
#         if self.backend.aim_bridge is None or bool(getattr(self.backend, "_aim_bootstrap_in_progress", False)):
#             self.bootstrap_runtime(enable_after_bootstrap=False)
#             return
#         current_enabled = bool(self.backend.aim_bridge.context.settings.toggles.get("Auto Trigger", False))
#         if not current_enabled and self.backend.aim_bridge.context.controller.get_status().value != "running":
#             self.backend.aim_bridge.start_runtime()
#         snapshot = self.backend.aim_bridge.toggle_auto_trigger()
#         if current_enabled:
#             aim_enabled = bool(self.backend.aim_bridge.context.settings.toggles.get("Aim Assist", False))
#             trigger_enabled = bool(self.backend.aim_bridge.context.settings.toggles.get("Auto Trigger", False))
#             if not aim_enabled and not trigger_enabled:
#                 snapshot = self.backend.aim_bridge.stop_runtime()
#         self.backend.state["aim"] = self.host.refresh_controller.build_runtime_state(snapshot)
#         self.backend.signal_update.emit(copy.deepcopy(self.backend.state))
# --- END FILE: AimAI/Integration/ClassAimBridgeManager.py ---

# --- BEGIN FILE: AimAI/Integration/ClassAimInputBridge.py ---
# from __future__ import annotations
# 
# import win32gui
# from Core import Utils
# 
# from PyQt6.QtCore import QObject, QTimer, pyqtSignal
# 
# from Core.ClassSettings import SettingsManager
# 
# 
# class AimInputBridge(QObject):
#     toggle_window_requested = pyqtSignal()
#     toggle_crosshair_requested = pyqtSignal()
#     toggle_overlay_requested = pyqtSignal()
# 
#     def __init__(self, window, backend):
#         super().__init__()
#         self.window = window
#         self.backend = backend
#         self.settings = SettingsManager()
#         self.recoil_config = self.backend.executor.config
#         self.is_ads = False
#         self.ads_toggled = False
#         self._ads_reset_timer = None
#         self.keyboard_listener = None
#         self.toggle_window_requested.connect(self.window.toggle_window_visibility)
#         self.toggle_crosshair_requested.connect(self.window.toggle_crosshair_visibility)
#         self.toggle_overlay_requested.connect(self.window.toggle_overlay_visibility)
#         self.reload_config()
# 
#     def reload_config(self):
#         self.guitoggle_key = self.settings.get("keybinds.gui_toggle", "f1").lower()
#         self.crosshair_toggle_key = self.settings.get("crosshair.toggle_key", "none").lower()
#         self.overlay_key = self.settings.get("overlay_key", "delete").lower()
#         self.aim_toggle_key = str(self.settings.get("aim.bindings.Emergency Stop Keybind", "f8")).lower()
#         self.aim_trigger_key = str(self.settings.get("aim.bindings.Toggle Trigger Keybind", "f7")).lower()
#         self.aim_primary_key = str(self.settings.get("aim.bindings.Aim Keybind", "right")).lower()
#         self.aim_secondary_key = str(self.settings.get("aim.bindings.Second Aim Keybind", "left ctrl")).lower()
#         if self.keyboard_listener:
#             self.keyboard_listener.update_guitoggle_key(self.guitoggle_key)
#             self.keyboard_listener.update_crosshair_toggle_key(self.crosshair_toggle_key)
#             self.keyboard_listener.update_overlay_key(self.overlay_key)
#             self.keyboard_listener.update_aim_runtime_keys(
#                 self.aim_toggle_key,
#                 self.aim_trigger_key,
#                 self.aim_secondary_key,
#             )
# 
#     @staticmethod
#     def _normalize_mouse_binding(key_name):
#         mapped = {
#             "right mouse": "right",
#             "left mouse": "left",
#             "middle mouse": "middle",
#             "xbutton1": "x1",
#             "xbutton2": "x2",
#         }
#         return mapped.get(str(key_name).lower(), str(key_name).lower())
# 
#     def _ensure_aim_bootstrap(self, enable_after_bootstrap: bool = False) -> bool:
#         if getattr(self.backend, "aim_bridge", None) is None or bool(
#             getattr(self.backend, "_aim_bootstrap_in_progress", False)
#         ):
#             self.backend.bootstrap_aim_runtime(enable_after_bootstrap=enable_after_bootstrap)
#             return False
#         return True
# 
#     def handle_input_action(self, action):
#         if action == "SLOT_1":
#             self.backend.set_slot(1)
#             self.window.update_macro_style(True)
#         elif action == "SLOT_2":
#             self.backend.set_slot(2)
#             self.window.update_macro_style(True)
# 
#         if not Utils.is_game_active():
#             return
#         if action == "MACRO_PAUSE":
#             self.backend.set_paused(True)
#             self.window.update_macro_style(False)
# 
#     def handle_raw_key(self, key, pressed):
#         if key == self.guitoggle_key and pressed:
#             self.toggle_window_requested.emit()
#             return
#         if key == self.crosshair_toggle_key and pressed:
#             self.toggle_crosshair_requested.emit()
#             return
#         if key == self.overlay_key and pressed:
#             self.toggle_overlay_requested.emit()
#             return
# 
#         aim_runtime_keys = {
#             self.aim_toggle_key,
#             self.aim_trigger_key,
#             self.aim_secondary_key,
#         }
#         if key in aim_runtime_keys:
#             if pressed and key == self.aim_toggle_key and hasattr(self.backend, "toggle_aim_assist_direct"):
#                 self.backend.toggle_aim_assist_direct()
#                 return
#             if pressed and key == self.aim_trigger_key and hasattr(self.backend, "toggle_auto_trigger_direct"):
#                 self.backend.toggle_auto_trigger_direct()
#                 return
#             if pressed:
#                 if not self._ensure_aim_bootstrap(enable_after_bootstrap=False):
#                     return
#             if hasattr(self.backend, "forward_aim_key_binding"):
#                 self.backend.forward_aim_key_binding(key, pressed)
#         if pressed and key in aim_runtime_keys:
#             return
#         if pressed and not Utils.is_game_active():
#             return
#         if key == "f2" and pressed:
#             self.backend.reload_config()
#         elif key == "r" and pressed:
#             pubg_ads = getattr(self.backend.pubg_config, "ads_mode", None)
#             ads_mode = pubg_ads.upper() if pubg_ads else self.settings.get("ads_mode", "HOLD").upper()
#             if ads_mode in ["CLICK", "TOGGLE"]:
#                 self.is_ads = False
#                 if hasattr(self.window, "crosshair") and self.window.crosshair:
#                     self.window.crosshair.reset_toggle_state()
# 
#     def handle_mouse_click(self, btn, pressed):
#         btn_name = str(btn).lower()
#         if pressed and btn_name in {
#             self._normalize_mouse_binding(self.aim_primary_key),
#             self._normalize_mouse_binding(self.aim_secondary_key),
#         }:
#             if not self._ensure_aim_bootstrap():
#                 return
# 
#         if hasattr(self.backend, "forward_aim_mouse_binding"):
#             self.backend.forward_aim_mouse_binding(btn_name, pressed)
# 
#         if btn_name == "right":
#             pubg_ads = getattr(self.backend.pubg_config, "ads_mode", None)
#             ads_mode = pubg_ads.upper() if pubg_ads else self.settings.get("ads_mode", "HOLD").upper()
#             if ads_mode == "HOLD":
#                 self.is_ads = pressed
#             elif ads_mode in ["CLICK", "TOGGLE"]:
#                 self.is_ads = True
#                 if pressed and self._ads_reset_timer and self._ads_reset_timer.is_alive():
#                     self._ads_reset_timer.cancel()
#                     self._ads_reset_timer = None
# 
#         if btn_name == "left" and pressed:
#             if self._ads_reset_timer and self._ads_reset_timer.is_alive():
#                 self._ads_reset_timer.cancel()
#                 self._ads_reset_timer = None
#             flags, _, _ = win32gui.GetCursorInfo()
#             cursor_visible = flags != 0
#             if not Utils.is_game_active() or cursor_visible:
#                 return
# 
#             pubg_ads = getattr(self.backend.pubg_config, "ads_mode", None)
#             ads_mode = pubg_ads.upper() if pubg_ads else self.settings.get("ads_mode", "HOLD").upper()
#             if ads_mode == "HOLD" and not self.is_ads:
#                 return
# 
#             data = self.backend.state
#             if data.get("paused", False):
#                 return
# 
#             slot = data.get("active_slot", 1)
#             gun_info = data.get(f"gun{slot}", {})
#             name = gun_info.get("name", "NONE")
#             if name != "NONE":
#                 self.backend.set_firing(True)
#                 base_table = self.recoil_config.get_base_table(name)
#                 if base_table:
#                     raw_pixels = self.recoil_config.get_raw_pattern(base_table)
#                     self.backend.executor.start_recoil(raw_pixels, initial_stance=data.get("stance", "Stand"))
#         elif btn_name == "left" and not pressed:
#             self.backend.set_firing(False)
#             self.backend.executor.stop_recoil()
#             if self.backend.executor.full_pattern_done:
#                 pubg_ads = getattr(self.backend.pubg_config, "ads_mode", None)
#                 ads_mode = pubg_ads.upper() if pubg_ads else self.settings.get("ads_mode", "HOLD").upper()
#                 if ads_mode in ["CLICK", "TOGGLE"]:
#                     def _reset_after_empty_mag():
#                         self.is_ads = False
#                         if hasattr(self.window, "crosshair") and self.window.crosshair:
#                             self.window.crosshair.reset_toggle_state()
#                     QTimer.singleShot(0, _reset_after_empty_mag)
# --- END FILE: AimAI/Integration/ClassAimInputBridge.py ---

# --- BEGIN FILE: AimAI/Integration/ClassAimNativeDllBridge.py ---
# from __future__ import annotations
# 
# import ctypes
# import os
# from pathlib import Path
# import sysconfig
# 
# 
# class Di88AimRuntimeStatus(ctypes.Structure):
#     _fields_ = [
#         ("struct_size", ctypes.c_uint32),
#         ("ready", ctypes.c_uint32),
#         ("running", ctypes.c_uint32),
#         ("status", ctypes.c_char * 32),
#         ("backend", ctypes.c_char * 64),
#         ("capture", ctypes.c_char * 32),
#         ("model", ctypes.c_char * 260),
#         ("fps", ctypes.c_double),
#         ("latency_ms", ctypes.c_double),
#         ("capture_ms", ctypes.c_double),
#         ("target_left", ctypes.c_int32),
#         ("target_top", ctypes.c_int32),
#         ("target_width", ctypes.c_int32),
#         ("target_height", ctypes.c_int32),
#         ("detection_count", ctypes.c_uint32),
#         ("captured_frames", ctypes.c_uint32),
#         ("capture_running", ctypes.c_uint32),
#         ("model_loaded", ctypes.c_uint32),
#         ("input_width", ctypes.c_int32),
#         ("input_height", ctypes.c_int32),
#         ("warmup_ms", ctypes.c_double),
#         ("source_fps", ctypes.c_double),
#         ("loop_ms", ctypes.c_double),
#         ("processed_frames", ctypes.c_uint32),
#     ]
# 
# 
# class AimNativeDllBridge:
#     def __init__(self, detect_root: Path | None = None, dll_path: Path | None = None) -> None:
#         self.detect_root = detect_root or Path(__file__).resolve().parents[2]
#         candidates = [
#             self.detect_root / "native" / "di88_aim_runtime.dll",
#             self.detect_root / "AimRuntimeNative" / "build-vs" / "Release" / "di88_aim_runtime.dll",
#             self.detect_root / "AimRuntimeNative" / "build" / "Release" / "di88_aim_runtime.dll",
#         ]
#         resolved = dll_path
#         if resolved is None:
#             resolved = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
#         self.dll_path = resolved
#         self.lib: ctypes.WinDLL | None = None
#         self.handle = ctypes.c_void_p()
#         self._dll_directory_handles: list[object] = []
#         self._has_set_capture_target = False
#         self._has_start_capture_loop = False
#         self._has_stop_capture_loop = False
#         self._has_load_model = False
#         self._has_run_warmup_inference = False
#         self._has_set_aim_settings = False
#         self._has_set_detection_settings = False
#         self._has_set_visual_settings = False
#         self._has_last_error = False
# 
#     def __del__(self) -> None:
#         try:
#             self.unload()
#         except Exception:
#             pass
# 
#     def load(self) -> None:
#         if self.lib is not None:
#             return
#         if not self.dll_path.exists():
#             raise FileNotFoundError(f"Native DLL not found: {self.dll_path}")
# 
#         self._prepare_dll_search_paths()
#         self.lib = ctypes.WinDLL(str(self.dll_path))
#         self._bind_functions()
# 
#         result = self.lib.di88_aim_create(ctypes.byref(self.handle))
#         if result != 0 or not self.handle.value:
#             raise RuntimeError(f"di88_aim_create failed with code {result}")
# 
#     def unload(self) -> None:
#         if self.lib is None:
#             return
#         if self.handle.value:
#             self.lib.di88_aim_destroy(self.handle)
#             self.handle = ctypes.c_void_p()
#         self.lib = None
# 
#     def version(self) -> str:
#         self.load()
#         assert self.lib is not None
#         return self.lib.di88_aim_runtime_version().decode("utf-8", errors="replace")
# 
#     def configure(self, model: str = "", capture: str = "DirectX", backend: str = "DirectML (GPU)") -> int:
#         self.load()
#         assert self.lib is not None
#         result = self.lib.di88_aim_configure(
#             self.handle,
#             model.encode("utf-8"),
#             capture.encode("utf-8"),
#             backend.encode("utf-8"),
#         )
#         self._raise_if_failed(result, "di88_aim_configure")
#         return result
# 
#     def load_model(self, model_path: str | Path, provider: str = "DirectML") -> int:
#         self.load()
#         assert self.lib is not None
#         if not self._has_load_model:
#             return 0
#         result = self.lib.di88_aim_load_model(
#             self.handle,
#             str(model_path).encode("utf-8"),
#             provider.encode("utf-8"),
#         )
#         self._raise_if_failed(result, "di88_aim_load_model")
#         return result
# 
#     def run_warmup_inference(self, runs: int = 2) -> int:
#         self.load()
#         assert self.lib is not None
#         if not self._has_run_warmup_inference:
#             return 0
#         result = self.lib.di88_aim_run_warmup_inference(self.handle, int(runs))
#         self._raise_if_failed(result, "di88_aim_run_warmup_inference")
#         return result
# 
#     def set_aim_settings(
#         self,
#         screen_width: int,
#         screen_height: int,
#         primary_aim_position: float,
#         secondary_aim_position: float,
#         mouse_sensitivity: float,
#         ema_smoothing: float,
#         mouse_jitter: int,
#         head_priority: bool,
#         aim_enabled: bool,
#         output_enabled: bool,
#     ) -> int:
#         self.load()
#         assert self.lib is not None
#         if not self._has_set_aim_settings:
#             return 0
#         result = self.lib.di88_aim_set_aim_settings(
#             self.handle,
#             int(screen_width),
#             int(screen_height),
#             float(primary_aim_position),
#             float(secondary_aim_position),
#             float(mouse_sensitivity),
#             float(ema_smoothing),
#             int(mouse_jitter),
#             int(bool(head_priority)),
#             int(bool(aim_enabled)),
#             int(bool(output_enabled)),
#         )
#         self._raise_if_failed(result, "di88_aim_set_aim_settings")
#         return result
# 
#     def set_detection_settings(
#         self,
#         min_confidence: float = 0.45,
#         max_detections: int = 64,
#         target_fps: int = 144,
#     ) -> int:
#         self.load()
#         assert self.lib is not None
#         if not self._has_set_detection_settings:
#             return 0
#         result = self.lib.di88_aim_set_detection_settings(
#             self.handle,
#             float(min_confidence),
#             int(max_detections),
#             int(target_fps),
#         )
#         self._raise_if_failed(result, "di88_aim_set_detection_settings")
#         return result
# 
#     def set_visual_settings(
#         self,
#         show_fov: bool = False,
#         show_detect: bool = False,
#         show_confidence: bool = False,
#         show_tracers: bool = False,
#         fov_size: int = 300,
#         fov_color_argb: int = 0xFFFF8080,
#         detect_color_argb: int = 0xFFFF4040,
#         border_thickness: int = 2,
#         opacity: float = 1.0,
#     ) -> int:
#         self.load()
#         assert self.lib is not None
#         if not self._has_set_visual_settings:
#             return 0
#         result = self.lib.di88_aim_set_visual_settings(
#             self.handle,
#             int(bool(show_fov)),
#             int(bool(show_detect)),
#             int(bool(show_confidence)),
#             int(bool(show_tracers)),
#             int(fov_size),
#             int(fov_color_argb),
#             int(detect_color_argb),
#             int(border_thickness),
#             float(opacity),
#         )
#         self._raise_if_failed(result, "di88_aim_set_visual_settings")
#         return result
# 
#     def start(self) -> int:
#         self.load()
#         assert self.lib is not None
#         result = self.lib.di88_aim_start(self.handle)
#         self._raise_if_failed(result, "di88_aim_start")
#         return result
# 
#     def stop(self) -> int:
#         self.load()
#         assert self.lib is not None
#         result = self.lib.di88_aim_stop(self.handle)
#         self._raise_if_failed(result, "di88_aim_stop")
#         return result
# 
#     def set_capture_target(self, left: int, top: int, width: int, height: int) -> int:
#         self.load()
#         assert self.lib is not None
#         if not self._has_set_capture_target:
#             return 0
#         result = self.lib.di88_aim_set_capture_target(
#             self.handle,
#             int(left),
#             int(top),
#             int(width),
#             int(height),
#         )
#         self._raise_if_failed(result, "di88_aim_set_capture_target")
#         return result
# 
#     def start_capture_loop(self) -> int:
#         self.load()
#         assert self.lib is not None
#         if not self._has_start_capture_loop:
#             return 0
#         result = self.lib.di88_aim_start_capture_loop(self.handle)
#         self._raise_if_failed(result, "di88_aim_start_capture_loop")
#         return result
# 
#     def stop_capture_loop(self) -> int:
#         self.load()
#         assert self.lib is not None
#         if not self._has_stop_capture_loop:
#             return 0
#         result = self.lib.di88_aim_stop_capture_loop(self.handle)
#         self._raise_if_failed(result, "di88_aim_stop_capture_loop")
#         return result
# 
#     def status(self) -> dict[str, object]:
#         self.load()
#         assert self.lib is not None
#         status = Di88AimRuntimeStatus()
#         result = self.lib.di88_aim_get_status(self.handle, ctypes.byref(status))
#         self._raise_if_failed(result, "di88_aim_get_status")
#         return {
#             "ready": bool(status.ready),
#             "running": bool(status.running),
#             "status": status.status.decode("utf-8", errors="replace").rstrip("\x00"),
#             "backend": status.backend.decode("utf-8", errors="replace").rstrip("\x00"),
#             "capture": status.capture.decode("utf-8", errors="replace").rstrip("\x00"),
#             "model": status.model.decode("utf-8", errors="replace").rstrip("\x00"),
#             "fps": float(status.fps),
#             "latency_ms": float(status.latency_ms),
#             "capture_ms": float(status.capture_ms),
#             "target": {
#                 "left": int(status.target_left),
#                 "top": int(status.target_top),
#                 "width": int(status.target_width),
#                 "height": int(status.target_height),
#             },
#             "detection_count": int(status.detection_count),
#             "captured_frames": int(status.captured_frames),
#             "capture_running": bool(status.capture_running),
#             "model_loaded": bool(status.model_loaded),
#             "input_width": int(status.input_width),
#             "input_height": int(status.input_height),
#             "warmup_ms": float(status.warmup_ms),
#             "source_fps": float(status.source_fps),
#             "loop_ms": float(status.loop_ms),
#             "processed_frames": int(status.processed_frames),
#             "last_error": self.last_error(),
#         }
# 
#     def last_error(self) -> str:
#         self.load()
#         assert self.lib is not None
#         if not self._has_last_error:
#             return ""
#         buffer = ctypes.create_string_buffer(1024)
#         result = self.lib.di88_aim_get_last_error(self.handle, buffer, len(buffer))
#         if result != 0:
#             return ""
#         return buffer.value.decode("utf-8", errors="replace")
# 
#     def available(self) -> bool:
#         try:
#             self.load()
#         except Exception:
#             return False
#         return bool(self.handle.value)
# 
#     def _prepare_dll_search_paths(self) -> None:
#         if self._dll_directory_handles or not hasattr(os, "add_dll_directory"):
#             return
# 
#         candidates: list[Path] = [self.dll_path.parent]
#         site_packages = Path(sysconfig.get_paths().get("purelib", ""))
#         nvidia_root = site_packages / "nvidia"
#         if nvidia_root.exists():
#             candidates.extend(path for path in nvidia_root.glob("*/bin") if path.exists())
#         torch_lib = site_packages / "torch" / "lib"
#         if torch_lib.exists():
#             candidates.append(torch_lib)
# 
#         seen: set[str] = set()
#         path_prefixes: list[str] = []
#         for directory in candidates:
#             key = str(directory.resolve()).lower()
#             if key in seen:
#                 continue
#             seen.add(key)
#             path_prefixes.append(str(directory))
#             try:
#                 self._dll_directory_handles.append(os.add_dll_directory(str(directory)))
#             except OSError:
#                 continue
#         if path_prefixes:
#             current_path = os.environ.get("PATH", "")
#             os.environ["PATH"] = os.pathsep.join(path_prefixes + [current_path])
# 
#     def _bind_functions(self) -> None:
#         assert self.lib is not None
#         self.lib.di88_aim_runtime_version.restype = ctypes.c_char_p
# 
#         self.lib.di88_aim_create.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
#         self.lib.di88_aim_create.restype = ctypes.c_int
# 
#         self.lib.di88_aim_destroy.argtypes = [ctypes.c_void_p]
#         self.lib.di88_aim_destroy.restype = ctypes.c_int
# 
#         self.lib.di88_aim_configure.argtypes = [
#             ctypes.c_void_p,
#             ctypes.c_char_p,
#             ctypes.c_char_p,
#             ctypes.c_char_p,
#         ]
#         self.lib.di88_aim_configure.restype = ctypes.c_int
# 
#         self._bind_optional_function(
#             "di88_aim_load_model",
#             [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p],
#         )
#         self._bind_optional_function(
#             "di88_aim_run_warmup_inference",
#             [ctypes.c_void_p, ctypes.c_uint32],
#         )
#         self._bind_optional_function(
#             "di88_aim_set_aim_settings",
#             [
#                 ctypes.c_void_p,
#                 ctypes.c_int32,
#                 ctypes.c_int32,
#                 ctypes.c_float,
#                 ctypes.c_float,
#                 ctypes.c_float,
#                 ctypes.c_float,
#                 ctypes.c_int32,
#                 ctypes.c_uint32,
#                 ctypes.c_uint32,
#                 ctypes.c_uint32,
#             ],
#         )
#         self._bind_optional_function(
#             "di88_aim_set_detection_settings",
#             [ctypes.c_void_p, ctypes.c_float, ctypes.c_uint32, ctypes.c_uint32],
#         )
#         self._bind_optional_function(
#             "di88_aim_set_visual_settings",
#             [
#                 ctypes.c_void_p,
#                 ctypes.c_uint32,
#                 ctypes.c_uint32,
#                 ctypes.c_uint32,
#                 ctypes.c_uint32,
#                 ctypes.c_uint32,
#                 ctypes.c_uint32,
#                 ctypes.c_uint32,
#                 ctypes.c_uint32,
#                 ctypes.c_float,
#             ],
#         )
#         self.lib.di88_aim_start.argtypes = [ctypes.c_void_p]
#         self.lib.di88_aim_start.restype = ctypes.c_int
# 
#         self.lib.di88_aim_stop.argtypes = [ctypes.c_void_p]
#         self.lib.di88_aim_stop.restype = ctypes.c_int
# 
#         self.lib.di88_aim_get_status.argtypes = [ctypes.c_void_p, ctypes.POINTER(Di88AimRuntimeStatus)]
#         self.lib.di88_aim_get_status.restype = ctypes.c_int
# 
#         self._bind_optional_function(
#             "di88_aim_set_capture_target",
#             [ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32],
#         )
#         self._bind_optional_function(
#             "di88_aim_start_capture_loop",
#             [ctypes.c_void_p],
#         )
#         self._bind_optional_function(
#             "di88_aim_stop_capture_loop",
#             [ctypes.c_void_p],
#         )
#         self._bind_optional_function(
#             "di88_aim_get_last_error",
#             [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32],
#             "last_error",
#         )
# 
#     def _bind_optional_function(self, name: str, argtypes: list[object], flag_name: str | None = None) -> None:
#         assert self.lib is not None
#         flag = f"_has_{flag_name or name.removeprefix('di88_aim_')}"
#         try:
#             function = getattr(self.lib, name)
#         except AttributeError:
#             setattr(self, flag, False)
#             return
#         function.argtypes = argtypes
#         function.restype = ctypes.c_int
#         setattr(self, flag, True)
# 
#     def _raise_if_failed(self, result: int, operation: str) -> None:
#         if result == 0:
#             return
#         error = self.last_error()
#         if error:
#             raise RuntimeError(f"{operation} failed with code {result}: {error}")
#         raise RuntimeError(f"{operation} failed with code {result}")
# --- END FILE: AimAI/Integration/ClassAimNativeDllBridge.py ---

# --- BEGIN FILE: AimAI/Integration/ClassAimRefreshController.py ---
# from __future__ import annotations
# 
# import copy
# 
# 
# class AimRefreshController:
#     def __init__(self, host) -> None:
#         self.host = host
# 
#     @property
#     def backend(self):
#         return self.host.backend
# 
#     def build_runtime_state(self, snapshot) -> dict:
#         if self.backend.aim_bridge is None:
#             return copy.deepcopy(self.backend.state.get("aim", {}))
#         return self.host.state_builder.build_runtime_state(self.backend.aim_bridge, snapshot)
# 
#     def refresh_state(self, force_emit: bool = False) -> None:
#         try:
#             if self.backend.aim_bridge is None:
#                 if force_emit:
#                     self.backend.signal_update.emit(copy.deepcopy(self.backend.state))
#                 return
# 
#             snapshot = self.backend.aim_bridge.snapshot()
#             next_state = self.build_runtime_state(snapshot)
#             changed = next_state != self.backend.state.get("aim", {})
#             self.backend.state["aim"] = next_state
#             if changed or force_emit:
#                 self.backend.signal_update.emit(copy.deepcopy(self.backend.state))
#         except Exception as exc:
#             self.backend.state["aim"] = self.host.state_builder.build_error_state(None, exc)
#             if force_emit:
#                 self.backend.signal_update.emit(copy.deepcopy(self.backend.state))
# 
#     def refresh_overlay(self) -> None:
#         return
# --- END FILE: AimAI/Integration/ClassAimRefreshController.py ---

# --- BEGIN FILE: AimAI/Integration/ClassAimRuntimeHost.py ---
# from __future__ import annotations
# 
# from .ClassAimBindingForwarder import AimBindingForwarder
# from .ClassAimBridgeManager import AimBridgeManager
# from .ClassAimRefreshController import AimRefreshController
# from .ClassAimRuntimePreparer import AimRuntimePreparer
# from .ClassAimStateBuilder import AimStateBuilder
# 
# 
# class AimRuntimeHost:
#     def __init__(self, backend) -> None:
#         self.backend = backend
#         self.runtime_preparer = AimRuntimePreparer()
#         self.state_builder = AimStateBuilder()
#         self.bridge_manager = AimBridgeManager(self)
#         self.refresh_controller = AimRefreshController(self)
#         self.binding_forwarder = AimBindingForwarder(self)
# 
#     def build_initial_state(self, settings_data: dict | None) -> dict:
#         return self.state_builder.build_initial_state(settings_data)
# 
#     def ensure_bridge(self):
#         return self.bridge_manager.ensure_bridge()
# 
#     def bootstrap_runtime(self, enable_after_bootstrap: bool = False) -> None:
#         self.bridge_manager.bootstrap_runtime(enable_after_bootstrap=enable_after_bootstrap)
# 
#     def prepare_runtime_settings(self, settings_data: dict | None) -> dict:
#         return self.runtime_preparer.prepare(settings_data)
# 
#     def sync_integration(self, settings_data: dict | None) -> None:
#         self.bridge_manager.sync_integration(settings_data)
# 
#     def build_runtime_state(self, snapshot) -> dict:
#         return self.refresh_controller.build_runtime_state(snapshot)
# 
#     def start_runtime(self) -> None:
#         self.bridge_manager.start_runtime()
# 
#     def stop_runtime(self) -> None:
#         self.bridge_manager.stop_runtime()
# 
#     def toggle_aim_assist(self) -> None:
#         self.bridge_manager.toggle_aim_assist()
# 
#     def toggle_auto_trigger(self) -> None:
#         self.bridge_manager.toggle_auto_trigger()
# 
#     def refresh_state(self, force_emit: bool = False) -> None:
#         self.refresh_controller.refresh_state(force_emit=force_emit)
# 
#     def refresh_overlay(self) -> None:
#         self.refresh_controller.refresh_overlay()
# 
#     def update_visual_settings(self, visual_state: dict | None) -> None:
#         if self.backend.aim_bridge is None:
#             return
#         self.backend.aim_bridge.apply_visual_settings(visual_state or {})
# 
#     def forward_mouse_binding(self, button_name: str, pressed: bool) -> None:
#         self.binding_forwarder.forward_mouse_binding(button_name, pressed)
# 
#     def forward_key_binding(self, key_name: str, pressed: bool) -> None:
#         self.binding_forwarder.forward_key_binding(key_name, pressed)
# --- END FILE: AimAI/Integration/ClassAimRuntimeHost.py ---

# --- BEGIN FILE: AimAI/Integration/ClassAimRuntimePreparer.py ---
# from __future__ import annotations
# 
# import copy
# 
# 
# class AimRuntimePreparer:
#     def prepare(self, settings_data: dict | None) -> dict:
#         prepared = copy.deepcopy(settings_data) if isinstance(settings_data, dict) else {}
#         aim = prepared.setdefault("aim", {})
#         runtime = aim.setdefault("runtime", {})
#         toggles = aim.setdefault("toggles", {})
#         dropdowns = aim.setdefault("dropdowns", {})
# 
#         runtime["auto_start"] = False
#         runtime["enabled"] = False
#         runtime["output_enabled"] = False
#         runtime["safe_mode"] = False
#         runtime["force_native"] = True
#         runtime["output_backend"] = "native_dll"
# 
#         toggles["Aim Assist"] = False
#         toggles["Auto Trigger"] = False
# 
#         capture_source = runtime.get("capture_backend") or dropdowns.get("Screen Capture Method")
#         if not capture_source:
#             capture_source = prepared.get("capture_mode", "DirectX")
#         normalized_capture = self._normalize_capture_backend(str(capture_source))
#         runtime["capture_backend"] = normalized_capture
#         dropdowns["Screen Capture Method"] = normalized_capture
# 
#         meta = aim.setdefault("meta", {})
#         if not runtime.get("model"):
#             last_model = str(meta.get("last_loaded_model", "") or "")
#             if last_model and last_model.upper() != "N/A":
#                 runtime["model"] = last_model
# 
#         return prepared
# 
#     @staticmethod
#     def _normalize_capture_backend(value: str) -> str:
#         normalized = str(value or "DirectX").strip().upper()
#         if normalized in {"DIRECTX", "GDI+"}:
#             return "DirectX" if normalized == "DIRECTX" else "GDI+"
#         if normalized == "DXCAM":
#             return "DirectX"
#         if normalized in {"MSS", "PIL"}:
#             return "GDI+"
#         return "DirectX"
# --- END FILE: AimAI/Integration/ClassAimRuntimePreparer.py ---

# --- BEGIN FILE: AimAI/Integration/ClassAimStateBuilder.py ---
# from __future__ import annotations
# 
# 
# class AimStateBuilder:
#     def build_initial_state(self, settings_data: dict | None) -> dict:
#         aim = settings_data.get("aim", {}) if isinstance(settings_data, dict) else {}
#         runtime = aim.get("runtime", {}) if isinstance(aim, dict) else {}
#         toggles = aim.get("toggles", {}) if isinstance(aim, dict) else {}
#         dropdowns = aim.get("dropdowns", {}) if isinstance(aim, dict) else {}
#         sliders = aim.get("sliders", {}) if isinstance(aim, dict) else {}
#         colors = aim.get("colors", {}) if isinstance(aim, dict) else {}
#         file_locations = aim.get("file_locations", {}) if isinstance(aim, dict) else {}
#         minimize = aim.get("minimize", {}) if isinstance(aim, dict) else {}
#         capture_source = runtime.get("capture_backend") or dropdowns.get("Screen Capture Method") or (settings_data.get("capture_mode", "DirectX") if isinstance(settings_data, dict) else "DirectX")
#         capture_mode = self._normalize_capture_backend(str(capture_source))
#         model_name = str(runtime.get("model") or aim.get("meta", {}).get("last_loaded_model") or "")
#         return {
#             "status": "idle",
#             "enabled": False,
#             "safe_mode": False,
#             "output_backend": "native_dll",
#             "capture_backend": capture_mode,
#             "inference_backend": "Not loaded",
#             "model": model_name,
#             "fps": 0.0,
#             "inference_ms": 0.0,
#             "capture_ms": 0.0,
#             "preprocess_ms": 0.0,
#             "postprocess_ms": 0.0,
#             "loop_ms": 0.0,
#             "detections": 0,
#             "runtime_source": "Native DLL Not Ready",
#             "native_required": True,
#             "native_ready": False,
#             "native_error": "",
#             "native_failures": 0,
#             "aim_assist": bool(toggles.get("Aim Assist", False)),
#             "auto_trigger": bool(toggles.get("Auto Trigger", False)),
#             "show_fov": bool(toggles.get("Show FOV", False)),
#             "show_detect": bool(toggles.get("Show Detected Player", False)),
#             "fov_size": int(sliders.get("FOV Size", 300)),
#             "sliders": dict(sliders),
#             "toggles": dict(toggles),
#             "dropdowns": dict(dropdowns),
#             "colors": dict(colors),
#             "file_locations": dict(file_locations),
#             "minimize": dict(minimize),
#             "last_error": "",
#         }
# 
#     def build_runtime_state(self, aim_bridge, snapshot) -> dict:
#         snapshot_dict = snapshot.to_dict()
#         settings = aim_bridge.context.settings
# 
#         snapshot_dict["aim_assist"] = bool(settings.toggles.get("Aim Assist", False))
#         snapshot_dict["auto_trigger"] = bool(settings.toggles.get("Auto Trigger", False))
#         snapshot_dict["show_fov"] = bool(settings.toggles.get("Show FOV", False))
#         snapshot_dict["show_detect"] = bool(settings.toggles.get("Show Detected Player", False))
#         snapshot_dict["fov_size"] = int(settings.sliders.get("FOV Size", 300))
#         snapshot_dict["sliders"] = dict(getattr(settings, "sliders", {}) or {})
#         snapshot_dict["toggles"] = dict(getattr(settings, "toggles", {}) or {})
#         snapshot_dict["dropdowns"] = dict(getattr(settings, "dropdowns", {}) or {})
#         snapshot_dict["colors"] = dict(getattr(settings, "colors", {}) or {})
#         snapshot_dict["file_locations"] = dict(getattr(settings, "file_locations", {}) or {})
#         return snapshot_dict
# 
#     def build_error_state(self, settings_data: dict | None, exc: Exception) -> dict:
#         capture_backend = "DirectX"
#         if isinstance(settings_data, dict):
#             aim = settings_data.get("aim", {}) if isinstance(settings_data.get("aim", {}), dict) else {}
#             runtime = aim.get("runtime", {}) if isinstance(aim, dict) else {}
#             dropdowns = aim.get("dropdowns", {}) if isinstance(aim, dict) else {}
#             capture_source = runtime.get("capture_backend") or dropdowns.get("Screen Capture Method") or settings_data.get("capture_mode", "DirectX")
#             capture_backend = self._normalize_capture_backend(str(capture_source))
#         return {
#             "status": "error",
#             "enabled": False,
#             "safe_mode": False,
#             "output_backend": "native_dll",
#             "capture_backend": capture_backend,
#             "model": "",
#             "fps": 0.0,
#             "inference_ms": 0.0,
#             "detections": 0,
#             "runtime_source": "Native DLL Error",
#             "native_required": True,
#             "native_ready": False,
#             "native_error": str(exc),
#             "native_failures": 0,
#             "aim_assist": False,
#             "auto_trigger": False,
#             "show_fov": False,
#             "show_detect": False,
#             "sliders": {},
#             "toggles": {},
#             "dropdowns": {},
#             "colors": {},
#             "file_locations": {},
#             "last_error": str(exc),
#         }
# 
#     @staticmethod
#     def _normalize_capture_backend(value: str) -> str:
#         normalized = str(value or "DirectX").strip().upper()
#         if normalized == "DIRECTX":
#             return "DirectX"
#         if normalized == "GDI+":
#             return "GDI+"
#         if normalized == "DXCAM":
#             return "DirectX"
#         if normalized in {"MSS", "PIL"}:
#             return "GDI+"
#         return "DirectX"
# --- END FILE: AimAI/Integration/ClassAimStateBuilder.py ---
