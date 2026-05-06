from __future__ import annotations

import ctypes
import logging
import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = Path(__file__).resolve().parent
APP_ROOT = (
    Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else PROJECT_ROOT
)
GAME_PATH_TOKENS = (
    "pubg",
    "tslgame",
    "binaries/win64",
    "steamapps/common/pubg",
)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

from src.core import utils as Utils
from src.core.logging_config import setup_logging

logger = logging.getLogger(__name__)


def _normalize_runtime_path(path_value: str | os.PathLike[str]) -> str:
    try:
        return Path(path_value).resolve().as_posix().lower()
    except Exception:
        return str(path_value).replace("\\", "/").lower()


def _is_disallowed_game_path(path_value: str | os.PathLike[str]) -> bool:
    normalized = _normalize_runtime_path(path_value)
    return any(token in normalized for token in GAME_PATH_TOKENS)


def _is_within_path(path_value: Path, root_value: Path) -> bool:
    try:
        path_value.resolve().relative_to(root_value.resolve())
        return True
    except ValueError:
        return False


def _log_runtime_paths() -> tuple[Path, Path, Path]:
    cwd = Path(os.getcwd()).resolve()
    executable_path = Path(sys.executable).resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    logger.info("Runtime cwd: %s", cwd)
    logger.info("Runtime executable: %s", executable_path)
    logger.info("Project root: %s", PROJECT_ROOT)
    logger.info("App root: %s", APP_ROOT)
    logger.info("Runtime root: %s", RUNTIME_ROOT)
    logger.info("Temp root: %s", temp_root)
    return cwd, executable_path, temp_root


def _enforce_safe_runtime_location(app) -> bool:
    from PyQt6.QtWidgets import QMessageBox

    cwd, executable_path, temp_root = _log_runtime_paths()
    blocked_paths = []
    if _is_disallowed_game_path(cwd):
        blocked_paths.append(f"cwd={cwd}")
    if _is_disallowed_game_path(executable_path):
        blocked_paths.append(f"sys.executable={executable_path}")
    if _is_disallowed_game_path(APP_ROOT):
        blocked_paths.append(f"app_root={APP_ROOT}")
    if _is_disallowed_game_path(RUNTIME_ROOT):
        blocked_paths.append(f"runtime_root={RUNTIME_ROOT}")
    if _is_disallowed_game_path(temp_root):
        blocked_paths.append(f"temp_root={temp_root}")

    runtime_allowed = _is_within_path(RUNTIME_ROOT, APP_ROOT) or _is_within_path(
        RUNTIME_ROOT, temp_root
    )
    if not runtime_allowed:
        blocked_paths.append(f"runtime_outside_allowed_roots={RUNTIME_ROOT}")

    if not blocked_paths:
        return True

    warning_message = (
        "Ứng dụng không được phép chạy từ thư mục game PUBG.\n\n"
        + "\n".join(blocked_paths)
        + "\n\nHãy di chuyển app ra ngoài thư mục game rồi chạy lại."
    )
    logger.warning("Safety guard blocked startup: %s", " | ".join(blocked_paths))
    QMessageBox.critical(None, "Safety Guard", warning_message)
    app.quit()
    return False


def main() -> int:
    Utils.set_high_dpi()
    setup_logging()

    import win32api
    from PyQt6.QtGui import QFont, QIcon
    from PyQt6.QtWidgets import QApplication, QDialog

    from src.core.backend import BackendThread
    from src.core.controllers.gui_bridge import GuiInputBridge
    from src.core.path_utils import get_resource_path
    from src.core.settings import SettingsManager
    from src.core.timing import HighPrecisionTimer
    from src.gui.macro_window import MacroWindow, ResolutionNoticeDialog
    from src.input.keyboard_listener import KeyboardListener
    from src.input.mouse_listener import MouseListener

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "di88.phutho.macro.v1"
        )
    except Exception:
        logger.exception("Failed to set AppUserModelID")

    timer_enforcer = HighPrecisionTimer()
    timer_enforcer.start()

    app = QApplication(sys.argv)
    app.setApplicationName("Di88-VP")
    app.setApplicationDisplayName("Di88-VP")
    app.setQuitOnLastWindowClosed(True)
    app.setFont(QFont("Segoe UI", 9))
    if not _enforce_safe_runtime_location(app):
        timer_enforcer.stop()
        return 0

    screen_width = win32api.GetSystemMetrics(0)
    screen_height = win32api.GetSystemMetrics(1)
    resolution_text = f"{screen_width}x{screen_height}"
    resolution_dialog = ResolutionNoticeDialog(resolution_text)
    if resolution_dialog.exec() != QDialog.DialogCode.Accepted:
        timer_enforcer.stop()
        sys.exit(0)

    window = MacroWindow()
    window.setWindowTitle("Di88-VP")
    window.setWindowIcon(QIcon(get_resource_path("di88vp.ico")))
    settings_manager = SettingsManager()
    runtime_context: dict[str, object] = {}

    def start_runtime_if_needed() -> None:
        if runtime_context.get("backend") is not None:
            return

        logger.info("Runtime lazy start requested")
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

        window.set_runtime_handles(
            keyboard_listener=keyboard_listener,
            mouse_listener=mouse_listener,
            timers=[timer_enforcer],
        )

        backend.start()
        runtime_context.update(
            {
                "backend": backend,
                "input_bridge": input_bridge,
                "keyboard_listener": keyboard_listener,
                "mouse_listener": mouse_listener,
            }
        )
        logger.info("Runtime started")

    window.set_runtime_starter(start_runtime_if_needed)

    def exception_hook(exctype, value, tb):
        import traceback

        logger.critical(
            "Unhandled exception:\n%s",
            "".join(traceback.format_exception(exctype, value, tb)),
        )
        timer_enforcer.stop()
        sys.exit(1)

    def on_quit() -> None:
        try:
            logger.info(
                "aboutToQuit triggered | shutdown_started=%s",
                bool(getattr(window, "_is_shutting_down", False)),
            )
        except Exception:
            logger.exception("Failed shutdown during app quit")
        timer_enforcer.stop()

    sys.excepthook = exception_hook
    app.aboutToQuit.connect(on_quit)

    start_runtime_if_needed()
    window.show()

    logger.info("Macro DI88-VP is ready")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
