from __future__ import annotations

from queue import Empty

from PyQt6.QtCore import QThread, pyqtSignal

from src.core.controllers.gui_bridge import GuiSignalBridge
from src.core.controllers.input_controller import InputController
from src.core.controllers.recoil_controller import RecoilController
from src.core.controllers.vision_controller import VisionController
from src.core.pipeline import PipelineQueues
from src.core.pubg_config import PubgConfig
from src.core.state import StateStore
from src.core.timing import StageTimer
from src.core.workers.capture_worker import CaptureWorker
from src.core.workers.detection_worker import DetectionWorker
from src.core.workers.input_worker import InputWorker
from src.detection.capture import ScreenCapture
from src.detection.detection_engine import DetectionEngine
from src.recoil.executor import RecoilExecutor


# Facade backend giữ API cũ nhưng chạy theo pipeline realtime
class BackendThread(QThread):
    signal_update = pyqtSignal(object)
    signal_message = pyqtSignal(str, str)
    signal_ads_update = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.running = True
        self.capture = ScreenCapture(capture_mode="DXCAM")
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
        self.input_worker = InputWorker(self.pipeline.command_queue)

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

        while self.running:
            try:
                packet = self.pipeline.detection_queue.get(timeout=0.1)
            except Empty:
                continue
            self.vision_controller.handle_detection(packet.updates)

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
        self.running = False
        self.vision_controller.stop()
        self.input_controller.stop()
        self.capture_worker.running = False
        self.detection_worker.running = False
        self.input_worker.running = False
        self.quit()
