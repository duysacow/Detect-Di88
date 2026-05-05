from __future__ import annotations

import ctypes
import time
from threading import Lock


# Ghi nhận latency từng stage trong pipeline realtime
class StageTimer:
    def __init__(self) -> None:
        self._lock = Lock()
        self._latencies: dict[str, float] = {}

    def mark(self, stage: str, started_at: float) -> float:
        latency_ms = (time.perf_counter() - started_at) * 1000.0
        with self._lock:
            self._latencies[stage] = latency_ms
        return latency_ms

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            return dict(self._latencies)


# Ép hệ thống dùng timer độ chính xác cao khi app chạy
class HighPrecisionTimer:
    def __init__(self) -> None:
        self.active = False

    def start(self) -> None:
        if not self.active:
            ctypes.windll.winmm.timeBeginPeriod(1)
            self.active = True

    def stop(self) -> None:
        if self.active:
            ctypes.windll.winmm.timeEndPeriod(1)
            self.active = False
