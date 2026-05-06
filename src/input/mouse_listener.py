import logging
import threading

from pynput import mouse
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


# Lắng nghe và phát sự kiện click chuột
class MouseListener(QObject):
    signal_click = pyqtSignal(str, bool)  # (button_name, pressed)
    # button_name in ["left", "right", "middle", "x1", "x2"]

    def __init__(self):
        super().__init__()
        self.listener = None
        self.running = False
        self._native_callback_thread_seen = None

    def start_listening(self):
        if not self.listener:
            self.listener = mouse.Listener(on_click=self.on_click)
            self.listener.daemon = True
            self.listener.start()
            self.running = True

    def stop_listening(self):
        if self.listener:
            logger.info("Stopping mouse listener")
            listener = self.listener
            self.running = False
            listener.stop()
            try:
                listener.join(0.075)
            except Exception:
                logger.exception("Mouse listener join failed")
            if listener.is_alive():
                logger.warning("mouse listener did not stop within timeout")
            else:
                logger.info("mouse listener stopped")
            self.listener = None

    def _track_callback_thread(self):
        current = threading.current_thread()
        if current.__class__.__name__ != "_DummyThread":
            return
        descriptor = f"{current.name}:{current.__class__.__name__}"
        if self._native_callback_thread_seen == descriptor:
            return
        self._native_callback_thread_seen = descriptor
        logger.warning("Mouse callback running on native thread: %s", descriptor)

    def get_native_callback_source(self):
        return self._native_callback_thread_seen

    def on_click(self, x, y, button, pressed):
        try:
            self._track_callback_thread()
            if not self.running:
                return
            # Convert button to string
            btn_str = str(button).replace("Button.", "")
            self.signal_click.emit(btn_str, pressed)
        except Exception:
            logger.exception("Mouse on_click failed")
