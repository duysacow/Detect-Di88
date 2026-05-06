from __future__ import annotations

import logging
import time
import zlib
from queue import Empty

import numpy as np
from PyQt6.QtCore import QThread

from src.core.pipeline import DetectionPacket

logger = logging.getLogger(__name__)


# Worker chỉ đọc frame và chạy detect cho pipeline
class DetectionWorker(QThread):
    def __init__(self, detector, capture, frame_queue, detection_queue, timer) -> None:
        super().__init__()
        self.detector = detector
        self.capture = capture
        self.frame_queue = frame_queue
        self.detection_queue = detection_queue
        self.timer = timer
        self.running = True
        self._last_signatures: dict[str, int] = {}
        self._last_gate_state: str | None = None

    def stop(self) -> None:
        self.running = False

    def run(self) -> None:
        try:
            while self.running:
                try:
                    frame_packet = self.frame_queue.get(timeout=0.1)
                except Empty:
                    continue
                start = time.perf_counter()
                updates = self._detect(frame_packet)
                packet = DetectionPacket(
                    updates=updates,
                    captured_at=frame_packet.captured_at,
                    detected_at=time.perf_counter(),
                    capture_latency_ms=getattr(frame_packet, "capture_latency_ms", 0.0),
                    detection_latency_ms=self.timer.mark("detection", start),
                )
                # Drop result cũ để decision luôn xử lý kết quả detect mới nhất.
                self.detection_queue.put_latest(packet)
        finally:
            self.capture.close_current_thread_capture()

    def _detect(self, frame_packet) -> dict[str, object]:
        img = frame_packet.frame
        updates: dict[str, object] = {}

        if not frame_packet.game_active:
            self._log_gate_state("not_pubg", "detect skipped: not PUBG")
            updates["ai_status"] = "HIBERNATE"
            return updates

        if not frame_packet.cursor_visible:
            self._log_gate_state("cursor_hidden", "detect skipped: cursor hidden")
            updates["ai_status"] = "HIBERNATE"
            return updates

        self._log_gate_state("running", "detect running: PUBG cursor visible")

        roi_img = self.capture.get_roi_from_image(img, "stance")
        if roi_img is not None:
            signature = self._fingerprint(roi_img)
            if self._last_signatures.get("stance") != signature:
                self._last_signatures["stance"] = signature
                detected_stance = self.detector.detect_stance(roi_img, roi_name="stance")
                if detected_stance is not None:
                    updates["stance"] = detected_stance

        updates["ai_status"] = "ACTIVE"
        for slot_num in [1, 2]:
            detected = self._scan_slot(img, slot_num)
            if detected:
                updates[f"gun{slot_num}"] = detected
        return updates

    def _log_gate_state(self, state: str, message: str) -> None:
        if self._last_gate_state == state:
            return
        self._last_gate_state = state
        logger.info(message)

    def _scan_slot(self, img, slot_num: int) -> dict[str, object]:
        slot_key = f"gun{slot_num}"
        roi_types = {
            "name": "name",
            "scope": "scope",
            "grip": "grip",
            "muzzle": "accessories",
        }
        detected: dict[str, object] = {}
        for roi_type, field in roi_types.items():
            roi_name = f"{slot_key}_{roi_type}"
            roi_img = self.capture.get_roi_from_image(img, roi_name)
            if roi_img is None:
                continue

            signature = self._fingerprint(roi_img)
            if self._last_signatures.get(roi_name) == signature:
                continue
            self._last_signatures[roi_name] = signature

            if roi_type == "name":
                detected[field] = self.detector.detect_weapon_name(roi_img)
            elif roi_type == "scope":
                detected[field] = self.detector.detect_scope(roi_img)
            elif roi_type == "grip":
                detected[field] = self.detector.detect_grip(roi_img)
            elif roi_type == "muzzle":
                detected[field] = self.detector.detect_accessory(roi_img)
        return detected

    def _fingerprint(self, roi_img: np.ndarray) -> int:
        return zlib.adler32(memoryview(np.ascontiguousarray(roi_img)))
