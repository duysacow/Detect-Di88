from __future__ import annotations

import logging
import time

import win32gui
from PyQt6.QtCore import QThread

from src.core import utils as Utils
from src.core.pipeline import FramePacket

logger = logging.getLogger(__name__)


# Worker chỉ capture frame mới nhất cho pipeline
class CaptureWorker(QThread):
    def __init__(self, capture, state_store, frame_queue, timer) -> None:
        super().__init__()
        self.capture = capture
        self.state_store = state_store
        self.frame_queue = frame_queue
        self.timer = timer
        self.running = True

    def stop(self) -> None:
        self.running = False

    def run(self) -> None:
        try:
            while self.running:
                start = time.perf_counter()
                game_active = Utils.is_game_active()
                if not game_active:
                    time.sleep(0.01)
                    continue

                flags, _, _ = win32gui.GetCursorInfo()
                frame = self.capture.grab_regional_image()
                if frame is None:
                    time.sleep(0.005)
                    continue

                packet = FramePacket(
                    frame=frame,
                    captured_at=time.perf_counter(),
                    cursor_visible=flags != 0,
                    menu_blocked=self.state_store.menu_blocked,
                    game_active=game_active,
                )
                packet.capture_latency_ms = self.timer.mark("capture", start)
                # Drop frame cũ để detector luôn ăn frame mới nhất, giảm latency.
                self.frame_queue.put_latest(packet)
        finally:
            self.capture.close_current_thread_capture()
