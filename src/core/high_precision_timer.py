import ctypes
import time


# Ép hệ thống dùng timer độ chính xác cao khi app chạy
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
