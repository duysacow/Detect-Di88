from __future__ import annotations

import logging
import os
import time
from queue import Empty

import win32gui
from PyQt6.QtCore import QThread

from src.core import utils as Utils
from src.core.input_batch import batch_send
from src.core.timing import precise_sleep

logger = logging.getLogger(__name__)


# Worker chỉ thực thi lệnh input từ command queue.
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

    def stop(self) -> None:
        self.running = False

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

    def _perform_fast_loot(self, busy_event, config: dict | None = None, running_state=None) -> None:
        started_at = time.perf_counter()
        config = config or {}
        mouse_move_abs, mouse_down, mouse_up = 0x0001 | 0x8000, 0x0002, 0x0004
        inventory_toggle_scancode = int(config.get("inventory_toggle_scancode", 0x17))
        loot_slots = list(config.get("loot_slots", []))
        total_slots = len(loot_slots)
        dest_x, dest_y = tuple(config.get("drag_destination", (0, 0)))
        open_settle_s = float(
            config.get(
                "fastloot_open_delay_ms",
                config.get("open_settle_ms", 12),
            )
        ) / 1000.0
        open_timeout_s = float(config.get("inventory_open_timeout_ms", 220)) / 1000.0
        open_poll_s = max(
            0.003,
            float(config.get("inventory_poll_interval_ms", 6)) / 1000.0,
        )
        click_delay_s = max(
            0.003,
            float(
                config.get(
                    "fastloot_click_delay_ms",
                    config.get("click_delay_ms", 10),
                )
            )
            / 1000.0,
        )
        close_settle_s = float(
            config.get(
                "fastloot_close_delay_ms",
                config.get("close_settle_ms", 10),
            )
        ) / 1000.0

        try:
            logger.info("fastloot started")
            if not Utils.is_game_active():
                logger.info("fastloot aborted: not PUBG active")
                return
            if total_slots == 0 or dest_x <= 0 or dest_y <= 0:
                logger.warning("fastloot aborted: missing calibrated profile")
                return

            inventory_was_open = self._is_inventory_open()
            if not inventory_was_open:
                self._tap_inventory_key(inventory_toggle_scancode)
                precise_sleep(open_settle_s)

            if not self._wait_inventory_open(open_timeout_s, open_poll_s):
                logger.info("fastloot aborted: inventory not opened")
                return

            logger.info("inventory opened")

            for index, (slot_x, slot_y) in enumerate(loot_slots, start=1):
                if not Utils.is_game_active():
                    logger.info("fastloot aborted: not PUBG active")
                    return
                if not self._is_inventory_open():
                    logger.info("fastloot aborted: inventory not opened")
                    return

                batch_send(
                    [
                        (mouse_move_abs, slot_x, slot_y),
                        (mouse_down, 0, 0),
                        (mouse_move_abs, dest_x, dest_y),
                        (mouse_up, 0, 0),
                    ]
                )
                logger.info("clicked slot %d/%d", index, total_slots)
                precise_sleep(click_delay_s)

            self._tap_inventory_key(inventory_toggle_scancode)
            precise_sleep(close_settle_s)
            logger.info("inventory closed")
            logger.info(
                "fastloot completed in %.1f ms",
                (time.perf_counter() - started_at) * 1000.0,
            )
        finally:
            if running_state is not None:
                running_state.fastloot_running = False
            busy_event.clear()

    def _tap_inventory_key(self, scancode: int) -> None:
        batch_send([(scancode, 0)])
        precise_sleep(0.02)
        batch_send([(scancode, 2)])

    def _wait_inventory_open(self, timeout_s: float, poll_interval_s: float) -> bool:
        deadline = time.perf_counter() + max(0.05, timeout_s)
        while time.perf_counter() < deadline:
            if self._is_inventory_open():
                return True
            precise_sleep(poll_interval_s)
        return False

    def _is_inventory_open(self) -> bool:
        if not Utils.is_game_active():
            return False
        try:
            flags, _, _ = win32gui.GetCursorInfo()
            return flags != 0
        except Exception:
            logger.warning("fastloot inventory gate check failed", exc_info=True)
            return False

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
        logger.info(
            "[JITTER] avg=%.1fms min=%.1fms max=%.1fms",
            avg_ms,
            min_ms,
            max_ms,
        )
        self._intervals_ms.clear()
