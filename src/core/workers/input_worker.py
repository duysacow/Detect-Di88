from __future__ import annotations

import os
import time
from queue import Empty

import win32api
from PyQt6.QtCore import QThread

from src.core.input_batch import batch_send
from src.core.timing import precise_sleep


# Worker chỉ thực thi lệnh input từ command queue
class InputWorker(QThread):
    def __init__(self, command_queue, timer) -> None:
        super().__init__()
        self.command_queue = command_queue
        self.timer = timer
        self.running = True
        self._jitter_debug = os.getenv("DI88_INPUT_JITTER_DEBUG", "0") == "1"
        self._last_exec_at = 0.0
        self._last_jitter_log_at = 0.0
        self._intervals_ms: list[float] = []

    def run(self) -> None:
        while self.running:
            try:
                command = self.command_queue.get(timeout=0.1)
            except Empty:
                continue

            started_at = time.perf_counter()
            self._record_interval(started_at)
            if command.command_type == "fast_loot":
                self._perform_fast_loot(**command.payload)
            self.timer.mark("input", started_at)
            self._log_jitter_if_due(started_at)
            self.timer.maybe_log_perf()

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
            precise_sleep(0.02)
            batch_send([(0x17, 2)])
            precise_sleep(0.18)
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
                    precise_sleep(0.015)
                precise_sleep(0.05)
            batch_send([(0x17, 0)])
            precise_sleep(0.02)
            batch_send([(0x17, 2)])
        finally:
            busy_event.clear()

    def _record_interval(self, started_at: float) -> None:
        if self._last_exec_at > 0.0:
            self._intervals_ms.append((started_at - self._last_exec_at) * 1000.0)
        self._last_exec_at = started_at

    def _log_jitter_if_due(self, now: float) -> None:
        if not self._jitter_debug or not self._intervals_ms:
            return
        if now - self._last_jitter_log_at < 1.0:
            return

        self._last_jitter_log_at = now
        avg_ms = sum(self._intervals_ms) / len(self._intervals_ms)
        min_ms = min(self._intervals_ms)
        max_ms = max(self._intervals_ms)
        print(
            f"[JITTER] avg={avg_ms:.1f}ms"
            f" min={min_ms:.1f}ms"
            f" max={max_ms:.1f}ms"
        )
        self._intervals_ms.clear()
