import time

import win32api
from PyQt6.QtCore import QThread

from src.core import utils as Utils
from src.core.input_batch import batch_send
from src.core.settings import SettingsManager


# Luồng polling phím nóng và thao tác hỗ trợ trong game
class KeyPollingThread(QThread):
    def __init__(self, parent=None):
        super().__init__()
        self.backend = parent
        self.running = True
        self._last_keys = [False] * 8
        self.refresh_settings()

    def refresh_settings(self):
        """Pre-load settings to avoid disk I/O in the tight loop"""
        sm = SettingsManager()
        self.fast_loot_enabled = sm.get("fast_loot", False)
        fl_key_str = sm.get("fast_loot_key", "caps_lock").lower()
        self.fast_loot_vk = {
            "caps_lock": 0x14,
            "caps lock": 0x14,
            "shift": 0x10,
            "ctrl": 0x11,
            "alt": 0x12,
        }.get(fl_key_str, 0x14)

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

            if self.fast_loot_enabled:
                if win32api.GetAsyncKeyState(self.fast_loot_vk) & 0x8000:
                    self.perform_fast_loot(self.fast_loot_vk)

            self._last_keys = current_keys
            time.sleep(0.01)

    def perform_fast_loot(self, trigger_vk):
        """Logic gắp đồ thần tốc"""
        mouse_move_abs, mouse_down, mouse_up = 0x0001 | 0x8000, 0x0002, 0x0004
        loot_coords = [
            (68, 579),
            (68, 512),
            (66, 450),
            (67, 390),
            (68, 329),
            (67, 266),
            (69, 207),
            (68, 146),
        ]
        dest_x, dest_y = 938, 504
        batch_send([(0x17, 0)])
        time.sleep(0.02)
        batch_send([(0x17, 2)])
        time.sleep(0.18)
        while win32api.GetAsyncKeyState(trigger_vk) & 0x8000:
            for lx, ly in loot_coords:
                if not (win32api.GetAsyncKeyState(trigger_vk) & 0x8000):
                    break
                batch_send(
                    [
                        (mouse_move_abs, lx, ly),
                        (mouse_down, 0, 0),
                        (mouse_move_abs, dest_x, dest_y),
                        (mouse_up, 0, 0),
                    ]
                )
                time.sleep(0.015)
            time.sleep(0.05)
        batch_send([(0x17, 0)])
        time.sleep(0.02)
        batch_send([(0x17, 2)])
