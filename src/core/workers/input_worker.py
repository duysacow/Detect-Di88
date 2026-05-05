from __future__ import annotations

import time
from queue import Empty

import win32api
from PyQt6.QtCore import QThread

from src.core.input_batch import batch_send


# Worker chỉ thực thi lệnh input từ command queue
class InputWorker(QThread):
    def __init__(self, command_queue) -> None:
        super().__init__()
        self.command_queue = command_queue
        self.running = True

    def run(self) -> None:
        while self.running:
            try:
                command = self.command_queue.get(timeout=0.1)
            except Empty:
                continue

            if command.command_type == "fast_loot":
                self._perform_fast_loot(**command.payload)

    def _perform_fast_loot(self, trigger_vk: int, busy_event) -> None:
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
        try:
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
        finally:
            busy_event.clear()
