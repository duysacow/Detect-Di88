from __future__ import annotations

import logging
import time
from queue import Empty

from PyQt6.QtCore import QThread, pyqtSignal

from src.core.controllers.gui_bridge import GuiSignalBridge
from src.core.controllers.input_controller import InputController
from src.core.controllers.recoil_controller import RecoilController
from src.core.controllers.vision_controller import VisionController
from src.core.pipeline import PipelineQueues
from src.core.pubg_config import PubgConfig
from src.core.state import StateStore
from src.core.settings import SettingsManager
from src.core.timing import StageTimer
from src.core.workers.capture_worker import CaptureWorker
from src.core.workers.detection_worker import DetectionWorker
from src.core.workers.input_worker import InputWorker
from src.detection.capture import ScreenCapture
from src.detection.detection_engine import DetectionEngine
from src.recoil.executor import RecoilExecutor

logger = logging.getLogger(__name__)


# Facade backend giữ API cũ nhưng chạy theo pipeline realtime.
class BackendThread(QThread):
    signal_update = pyqtSignal(object)
    signal_message = pyqtSignal(str, str)
    signal_ads_update = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.running = True
        raw_capture_mode = str(SettingsManager().get("capture_mode", "DXCAM") or "DXCAM").upper()
        capture_mode = {
            "DXCAM": "DXCAM",
            "DIRECTX": "DXCAM",
            "DXGI": "DXCAM",
            "NATIVE": "DXCAM",
            "AUTO": "DXCAM",
            "MSS": "MSS",
            "GDI": "MSS",
            "GDI+": "MSS",
            "PIL": "MSS",
        }.get(raw_capture_mode, "DXCAM")
        self.capture = ScreenCapture(capture_mode=capture_mode)
        self.detector = DetectionEngine(
            screen_width=self.capture.width,
            screen_height=self.capture.height,
        )
        self.executor = RecoilExecutor()
        self.pubg_config = PubgConfig()

        self.state_store = StateStore()
        self.pipeline = PipelineQueues()
        self.timer = StageTimer()
        self.gui_bridge = GuiSignalBridge(self, self.state_store)
        self.recoil_controller = RecoilController(
            self.state_store, self.executor, self.pubg_config
        )
        self.vision_controller = VisionController(
            self.state_store,
            self.recoil_controller,
            self.gui_bridge,
            self.pubg_config,
        )
        self.input_controller = InputController(
            self.state_store,
            self.recoil_controller,
            self.gui_bridge,
            self.pipeline.command_queue,
        )

        self.capture_worker = CaptureWorker(
            self.capture, self.state_store, self.pipeline.frame_queue, self.timer
        )
        self.detection_worker = DetectionWorker(
            self.detector,
            self.capture,
            self.pipeline.frame_queue,
            self.pipeline.detection_queue,
            self.timer,
        )
        self.input_worker = InputWorker(self.pipeline.command_queue, self.timer)

        if self.pubg_config.parse_config():
            self.pubg_config.debug_print()
        self.recoil_controller.sync_executor()

    @property
    def state(self):
        return self.state_store.state

    def run(self) -> None:
        self.vision_controller.start()
        self.input_controller.start()
        self.capture_worker.start()
        self.detection_worker.start()
        self.input_worker.start()

        try:
            while self.running:
                try:
                    packet = self.pipeline.detection_queue.get(timeout=0.1)
                except Empty:
                    continue

                decision_started_at = time.perf_counter()
                self.vision_controller.handle_detection(packet.updates)
                decision_ms = self.timer.mark("decision", decision_started_at)
                total_ms = (
                    packet.capture_latency_ms
                    + packet.detection_latency_ms
                    + decision_ms
                    + self.timer.snapshot().get("input", 0.0)
                )
                self.timer.set("total", total_ms)
                self.timer.maybe_log_perf()
        finally:
            self._stop_workers()
            self._wait_workers()
            self.capture.close()

    def reload_config(self) -> None:
        self.recoil_controller.reload_config()
        self.input_controller.refresh_settings()
        self.gui_bridge.emit_message("SUCCESS", "CONFIG REFRESHED!")

    def set_slot(self, slot: int) -> None:
        self.input_controller.set_slot(slot)

    def set_paused(self, paused: bool) -> None:
        self.input_controller.set_paused(paused)

    def set_firing(self, is_firing: bool) -> None:
        self.input_controller.set_firing(is_firing)

    def set_stance_by_key(self, stance: str) -> None:
        self.input_controller.set_stance_by_key(stance)

    def toggle_hybrid_mode(self) -> None:
        self.input_controller.toggle_hybrid_mode()

    def stop(self) -> None:
        logger.info("Backend stop requested")
        self.running = False
        self.recoil_controller.stop_recoil()
        self.vision_controller.stop()
        self.input_controller.stop()
        self._stop_workers()
        if not self.isRunning():
            self.capture.close()
        self.quit()

    def _stop_workers(self) -> None:
        for worker in (self.capture_worker, self.detection_worker, self.input_worker):
            try:
                worker.stop()
            except Exception:
                logger.exception("Failed to stop worker %s", worker.__class__.__name__)

    def _wait_workers(self, timeout_ms: int = 300) -> None:
        all_stopped = True
        for worker in (self.capture_worker, self.detection_worker, self.input_worker):
            try:
                if worker.isRunning():
                    logger.info(
                        "Waiting worker %s for %sms",
                        worker.__class__.__name__,
                        timeout_ms,
                    )
                    worker.wait(timeout_ms)
                if worker.isRunning():
                    all_stopped = False
                    logger.warning(
                        "worker %s did not stop within timeout",
                        worker.__class__.__name__,
                    )
                else:
                    logger.info("worker %s stopped", worker.__class__.__name__)
            except Exception:
                all_stopped = False
                logger.exception("Failed waiting worker %s", worker.__class__.__name__)
        if all_stopped:
            logger.info("all backend workers exited")
