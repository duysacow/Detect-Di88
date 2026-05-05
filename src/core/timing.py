from __future__ import annotations

import ctypes
import os
import time
from threading import Lock


# Ghi nhận latency từng stage trong pipeline realtime
class StageTimer:
    def __init__(self) -> None:
        self._lock = Lock()
        self._latencies: dict[str, float] = {}
        self._perf_debug = os.getenv("DI88_PERF_DEBUG", "0") == "1"
        self._last_perf_log_at = 0.0

    def mark(self, stage: str, started_at: float) -> float:
        latency_ms = (time.perf_counter() - started_at) * 1000.0
        return self.set(stage, latency_ms)

    def set(self, stage: str, latency_ms: float) -> float:
        with self._lock:
            self._latencies[stage] = latency_ms
        return latency_ms

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            return dict(self._latencies)

    def maybe_log_perf(self) -> None:
        if not self._perf_debug:
            return

        now = time.perf_counter()
        if now - self._last_perf_log_at < 1.0:
            return

        self._last_perf_log_at = now
        stats = self.snapshot()
        capture_ms = stats.get("capture", 0.0)
        detection_ms = stats.get("detection", 0.0)
        decision_ms = stats.get("decision", 0.0)
        input_ms = stats.get("input", 0.0)
        total_ms = stats.get(
            "total", capture_ms + detection_ms + decision_ms + input_ms
        )
        print(
            f"[PERF] capture={capture_ms:.1f}ms"
            f" detect={detection_ms:.1f}ms"
            f" decision={decision_ms:.1f}ms"
            f" input={input_ms:.1f}ms"
            f" total={total_ms:.1f}ms"
        )


# Ép hệ thống dùng timer độ chính xác cao khi app chạy
def precise_sleep(duration_s: float) -> None:
    if duration_s <= 0:
        return

    deadline = time.perf_counter() + duration_s
    while True:
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            return
        if remaining > 0.002:
            time.sleep(remaining - 0.001)
        else:
            time.sleep(0)


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
