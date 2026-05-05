from __future__ import annotations

from dataclasses import dataclass, field
from queue import Empty, Full, Queue
from typing import Any, Generic, TypeVar


@dataclass(slots=True)
class FramePacket:
    frame: Any
    captured_at: float
    cursor_visible: bool
    menu_blocked: bool
    game_active: bool
    capture_latency_ms: float = 0.0


@dataclass(slots=True)
class DetectionPacket:
    updates: dict[str, Any]
    captured_at: float
    detected_at: float
    capture_latency_ms: float = 0.0
    detection_latency_ms: float = 0.0


@dataclass(slots=True)
class InputCommand:
    command_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    issued_at: float = 0.0


T = TypeVar("T")


# Queue giữ phần tử mới nhất và bỏ phần tử cũ khi đầy
class LatestQueue(Generic[T]):
    def __init__(self, maxsize: int = 1) -> None:
        self._queue: Queue[T] = Queue(maxsize=maxsize)

    def put_latest(self, item: T) -> None:
        # Drop phần tử cũ để pipeline luôn xử lý frame/result mới nhất, giảm latency.
        while True:
            try:
                self._queue.put_nowait(item)
                return
            except Full:
                try:
                    self._queue.get_nowait()
                except Empty:
                    return

    def get(self, timeout: float | None = None) -> T:
        return self._queue.get(timeout=timeout)

    def empty(self) -> bool:
        return self._queue.empty()


@dataclass(slots=True)
class PipelineQueues:
    frame_queue: LatestQueue[FramePacket] = field(default_factory=LatestQueue)
    detection_queue: LatestQueue[DetectionPacket] = field(default_factory=LatestQueue)
    command_queue: Queue[InputCommand] = field(default_factory=lambda: Queue(maxsize=64))
