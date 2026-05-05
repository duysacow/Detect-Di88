from __future__ import annotations

from threading import RLock
from typing import Any


# Lưu state runtime và metadata dùng chung cho pipeline
class StateStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._state: dict[str, Any] = {
            "gun1": {
                "name": "NONE",
                "scope": "NONE",
                "grip": "NONE",
                "accessories": "NONE",
            },
            "gun2": {
                "name": "NONE",
                "scope": "NONE",
                "grip": "NONE",
                "accessories": "NONE",
            },
            "stance": "Stand",
            "active_slot": 1,
            "paused": False,
            "firing": False,
            "hybrid_mode": "Scope1",
            "ai_status": "HIBERNATE",
        }
        self.menu_blocked = False
        self.inventory_gate = False
        self.stance_lock_until = 0.0
        self.ai_active_until = 0.0
        self.stance_buffer: list[str] = []
        self.weapon_buffers: dict[str, list[str]] = {"gun1": [], "gun2": []}

    @property
    def state(self) -> dict[str, Any]:
        return self._state

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                **self._state,
                "gun1": dict(self._state["gun1"]),
                "gun2": dict(self._state["gun2"]),
            }

    def update(self, **changes: Any) -> None:
        with self._lock:
            self._state.update(changes)

    def set_gun(self, gun_key: str, gun_data: dict[str, Any]) -> None:
        with self._lock:
            self._state[gun_key] = gun_data

    def get_active_slot(self) -> int:
        return int(self._state.get("active_slot", 1))

    def get_active_gun(self) -> dict[str, Any]:
        return self._state[f"gun{self.get_active_slot()}"]

