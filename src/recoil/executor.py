import time
from threading import Thread

import win32api
import win32con


# Thực thi kéo tâm theo pattern recoil hiện tại
class RecoilExecutor:
    def __init__(self):
        super().__init__()
        from src.recoil.config import RecoilConfig

        self.config = RecoilConfig()

        self.running = False
        self.thread = None

        self.pattern = []
        self.current_index = 0
        self.full_pattern_done = False  # True khi bắn hết toàn bộ pattern (hết đạn)

        # HỆ SỐ CỐ ĐỊNH (Súng + Phụ kiện)
        self.gun_base_mult = 1.0

        # HỆ SỐ ĐỘNG (Tư thế sấy)
        self.st_stand = 1.0
        self.st_crouch = 1.0
        self.st_prone = 1.0

        # TRẠNG THÁI REAL-TIME
        self.live_stance = "Stand"
        self.current_gun_name = "NONE"
        self._remainder_y = 0.0

    def start_recoil(self, base_pattern, initial_stance="Stand"):
        self.stop_recoil()

        self.live_stance = initial_stance
        self._remainder_y = 0.0
        self.pattern = base_pattern

        self.current_index = 0
        self.full_pattern_done = False  # Reset mỗi lần bắt đầu bắn

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
        # Precise loop timing using stable Target Time method
        sampling_rate = 0.008  # 8ms
        if hasattr(self.config.data, "sampling_rate_ms"):
            sampling_rate = self.config.data.sampling_rate_ms / 1000.0

        next_time = time.perf_counter()

        from src.core import utils as Utils

        while self.running:
            # 1. KIỂM TRA CỬA SỔ GAME
            if not Utils.is_game_active():
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
                    self.full_pattern_done = True  # Đã bắn hết pattern = hết đạn

                # LOGIC CỘNG DỒN SỐ DƯ (Chuẩn mực High-Precision)
                total_y = pixels + self._remainder_y
                move_y = int(total_y)
                self._remainder_y = total_y - move_y

                if move_y != 0:
                    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, 0, move_y, 0, 0)

            # Đảm bảo nhịp 8ms chuẩn xác
            curr_t = time.perf_counter()
            if next_time > curr_t:
                time.sleep(next_time - curr_t)
            else:
                next_time = curr_t
