from __future__ import annotations

import threading
import time

import win32api

from src.core import utils as Utils
from src.core.pipeline import InputCommand
from src.core.settings import SettingsManager


# Điều phối hotkey realtime và phát lệnh input nền
class InputController:
    def __init__(self, state_store, recoil_controller, gui_bridge, command_queue) -> None:
        self.state_store = state_store
        self.recoil_controller = recoil_controller
        self.gui_bridge = gui_bridge
        self.command_queue = command_queue
        self.running = False
        self._thread: threading.Thread | None = None
        self._last_keys = [False] * 8
        self._fast_loot_busy = threading.Event()
        self.refresh_settings()

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.running = False

    def refresh_settings(self) -> None:
        sm = SettingsManager()
        self.fast_loot_enabled = sm.get("fast_loot", False)
        fl_key_str = sm.get("fast_loot_key", "caps_lock").lower()
        self.fast_loot_vk = {
            "caps_lock": 0x14,
            "caps lock": 0x14,
            "shift": 0x10,
            "ctrl": 0x11,
            "alt": 0x12,
        }.get(fl_key_str, 0x14)

    def _poll_loop(self) -> None:
        while self.running:
            if not Utils.is_game_active():
                self.recoil_controller.stop_recoil()
                time.sleep(0.05)
                continue

            vks = [0x11, 0x12, 0x31, 0x32, 0x43, 0x5A, 0x20, 0x02]
            current_keys = [(win32api.GetAsyncKeyState(vk) & 0x8000) != 0 for vk in vks]

            if current_keys[4] and not self._last_keys[4]:
                self.set_stance_by_key("Crouch")
            if current_keys[5] and not self._last_keys[5]:
                self.set_stance_by_key("Prone")
            if current_keys[6] and not self._last_keys[6]:
                self.set_stance_by_key("Stand")

            is_tab = (win32api.GetAsyncKeyState(0x09) & 0x8000) != 0
            is_esc = (win32api.GetAsyncKeyState(0x1B) & 0x8000) != 0
            is_map = (win32api.GetAsyncKeyState(0x4D) & 0x8000) != 0
            is_comma = (win32api.GetAsyncKeyState(0xBC) & 0x8000) != 0

            if is_tab:
                self.state_store.menu_blocked = False
            elif is_esc or is_map or is_comma:
                self.state_store.menu_blocked = True

            if current_keys[1] and (current_keys[7] and not self._last_keys[7]):
                self.toggle_hybrid_mode()

            if self.fast_loot_enabled:
                if (
                    win32api.GetAsyncKeyState(self.fast_loot_vk) & 0x8000
                    and not self._fast_loot_busy.is_set()
                ):
                    self._fast_loot_busy.set()
                    self.command_queue.put(
                        InputCommand(
                            command_type="fast_loot",
                            payload={
                                "trigger_vk": self.fast_loot_vk,
                                "busy_event": self._fast_loot_busy,
                            },
                            issued_at=time.perf_counter(),
                        )
                    )

            self._last_keys = current_keys
            time.sleep(0.01)

    def set_slot(self, slot: int) -> None:
        self.state_store.state["paused"] = False
        self.state_store.state["active_slot"] = slot
        self.recoil_controller.sync_executor()
        self.gui_bridge.emit_state()

    def set_paused(self, paused: bool) -> None:
        self.state_store.state["paused"] = paused
        self.gui_bridge.emit_state()

    def set_firing(self, is_firing: bool) -> None:
        if self.state_store.state.get("firing") != is_firing:
            self.state_store.state["firing"] = is_firing
            self.gui_bridge.emit_state()

    def set_stance_by_key(self, stance: str) -> None:
        current = self.state_store.state.get("stance")
        if stance == "Crouch" and current == "Crouch":
            stance = "Stand"
        elif stance == "Prone" and current == "Prone":
            stance = "Stand"

        self.state_store.state["stance"] = stance
        self.state_store.stance_buffer = [stance] * 3
        self.state_store.stance_lock_until = time.time() + 0.8
        self.recoil_controller.set_live_stance(stance)
        self.gui_bridge.emit_state()

    def toggle_hybrid_mode(self) -> None:
        state = self.state_store.state
        state["hybrid_mode"] = "Scope4" if state.get("hybrid_mode") == "Scope1" else "Scope1"
        slot = self.state_store.get_active_slot()
        gun_key = f"gun{slot}"
        current_scope = state[gun_key].get("scope", "")
        if "KH" in str(current_scope).upper():
            zoom = "1" if state["hybrid_mode"] == "Scope1" else "4"
            state[gun_key]["scope"] = f"ScopeKH_{zoom}"

        self.gui_bridge.emit_message(
            "SCOPE", "KH X4" if state["hybrid_mode"] == "Scope4" else "KH X1"
        )
        self.recoil_controller.sync_executor()
        self.gui_bridge.emit_state()
