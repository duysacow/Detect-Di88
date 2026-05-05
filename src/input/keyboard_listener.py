import threading
import time

from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

# Bộ lưu trữ toàn cục Tracking Physical Keys (Được quản lý tự động bởi Pynput, bỏ qua SendInput)
PHYSICAL_KEYS = set()
INJECT_LOCK = threading.Lock()
INJECTED_EVENTS = {}  # { 'w_press': [timestamp1, timestamp2], ... }


def add_injected_event(key, is_press):
    """
    Macro (ví dụ LuotNgoi) gọi hàm này trước khi thực sự SendInput.
    Cấp 1 Token báo cho Pynput biết sẽ có 1 event ảo sắp đến.
    """
    with INJECT_LOCK:
        if key == "shift_l" or key == "shift_r":
            key = "shift"
        k = f"{key.lower()}_{'press' if is_press else 'release'}"
        if k not in INJECTED_EVENTS:
            INJECTED_EVENTS[k] = []
        INJECTED_EVENTS[k].append(time.time())


def consume_injected_event(key, is_press):
    """
    Pynput gọi hàm này mỗi khi nhận event. Nếu có Token, tự động tiêu hủy 1 Token và trả về True.
    """
    with INJECT_LOCK:
        if key == "shift_l" or key == "shift_r":
            key = "shift"
        k = f"{key.lower()}_{'press' if is_press else 'release'}"

        now = time.time()
        if k in INJECTED_EVENTS:
            # Dọn dẹp Tokens cũ quá 1 giây (đề phòng Pynput miss event gây rác)
            INJECTED_EVENTS[k] = [t for t in INJECTED_EVENTS[k] if now - t < 1.0]
            if len(INJECTED_EVENTS[k]) > 0:
                INJECTED_EVENTS[k].pop(0)  # Tiêu hủy 1 Token
                return True
        return False


# Lắng nghe và phát sự kiện bàn phím cho ứng dụng
class KeyboardListener(QObject):
    # Signals
    signal_key_event = pyqtSignal(str, bool)  # Raw Key
    signal_action = pyqtSignal(str)  # Game Action (e.g. "SWITCH_GUN_1")

    def __init__(self):
        super().__init__()
        self.listener = None
        self.running = False

        # Mapping Key -> Action
        self.key_map = {
            # CHỈ 2 PHÍM NÀY KÍCH HOẠT MACRO
            "1": "SLOT_1",
            "!": "SLOT_1",
            "2": "SLOT_2",
            "@": "SLOT_2",
            # TẤT CẢ CÁC SLOT KHÁC -> TỰ ĐỘNG PAUSE MACRO
            "3": "MACRO_PAUSE",
            "#": "MACRO_PAUSE",
            "4": "MACRO_PAUSE",
            "$": "MACRO_PAUSE",
            "5": "MACRO_PAUSE",
            "%": "MACRO_PAUSE",
            "6": "MACRO_PAUSE",
            "^": "MACRO_PAUSE",
            "7": "MACRO_PAUSE",
            "&": "MACRO_PAUSE",
            "g": "MACRO_PAUSE",  # Lựu đạn
            "x": "MACRO_PAUSE",  # Pause thủ công
            # Stance keys
            "c": "STANCE_CROUCH",
            "z": "STANCE_PRONE",
            "space": "STANCE_JUMP",
        }

        # Keys requiring Raw Event (Press/Release) tracking
        self.raw_keys = {"r"}  # 'r' để detect nạp đạn

        # Track pressed keys to prevent auto-repeat spam
        self.pressed_keys = set()

        # Current GUI Toggle Key
        self.current_guitoggle_key = "f1"
        self.raw_keys.add(self.current_guitoggle_key)

    def update_guitoggle_key(self, new_key):
        """Update the GUI Toggle key in raw_keys"""
        new_key = new_key.lower()

        # Remove old key
        if self.current_guitoggle_key in self.raw_keys:
            self.raw_keys.discard(self.current_guitoggle_key)

        # Add new key
        self.raw_keys.add(new_key)
        self.current_guitoggle_key = new_key
        # print(f"[KEYBOARD] Updated GUI Toggle Key: {new_key}")

    def start_listening(self):
        if not self.listener:
            # Pynput Listener
            self.listener = keyboard.Listener(
                on_press=self.on_press, on_release=self.on_release
            )
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
            if not k_str:
                return

            # NẾU CÓ TOKEN TỪ MACRO -> ĐÂY LÀ PHÍM ẢO -> BỎ QUA NGAY LẬP TỨC
            if consume_injected_event(k_str, True):
                return

            # Ghi nhận phím vào bộ nhớ Vật Lý Toàn Cục
            PHYSICAL_KEYS.add(k_str)

            # 1. OPTIMIZATION: Check Relevance FIRST
            # If key is NOT in map and NOT in raw_keys, IGNORE completely.
            is_raw = k_str in self.raw_keys
            action = self.key_map.get(k_str)

            if not is_raw and not action:
                return

            # 2. Anti-Repeat Logic (Only for relevant keys)
            if k_str in self.pressed_keys:
                return
            self.pressed_keys.add(k_str)

            # 3. Emit Signals
            if is_raw:
                self.signal_key_event.emit(k_str, True)

            if action:
                self.signal_action.emit(action)

        except Exception as e:
            print(f"[KeyError] {e}")

    def on_release(self, key):
        try:
            k_str = self.get_key_name(key)
            if not k_str:
                return

            # NẾU CÓ TOKEN TỪ MACRO -> ĐÂY LÀ PHÍM ẢO -> BỎ QUA NGAY LẬP TỨC
            if consume_injected_event(k_str, False):
                return

            # Gỡ phím khỏi bộ nhớ Vật Lý Toàn Cục
            if k_str in PHYSICAL_KEYS:
                PHYSICAL_KEYS.discard(k_str)

            # Clean up state (Only if it was tracked)
            if k_str in self.pressed_keys:
                self.pressed_keys.remove(k_str)

            # Emit Release for Raw Keys
            if k_str in self.raw_keys:
                self.signal_key_event.emit(k_str, False)
        except Exception as e:
            print(f"[KEYBOARD] on_release error: {e}")

    def get_key_name(self, key):
        # Convert pynput key to string
        if hasattr(key, "char") and key.char:
            return key.char.lower()  # Always Lowercase (Fix Shift+W -> w)
        elif hasattr(key, "name"):
            return key.name
        else:
            return str(key).replace("Key.", "")
