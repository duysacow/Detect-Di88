from pynput import mouse
from PyQt6.QtCore import QObject, pyqtSignal


# Lắng nghe và phát sự kiện click chuột
class MouseListener(QObject):
    signal_click = pyqtSignal(str, bool)  # (button_name, pressed)
    # button_name in ["left", "right", "middle", "x1", "x2"]

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
            # Convert button to string
            btn_str = str(button).replace("Button.", "")
            self.signal_click.emit(btn_str, pressed)
        except Exception as e:
            print(f"[MOUSE] on_click error: {e}")
