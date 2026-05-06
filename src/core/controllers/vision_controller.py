from __future__ import annotations

import logging
import threading
import time

logger = logging.getLogger(__name__)


# Hợp nhất kết quả detect vào state runtime và GUI
class VisionController:
    def __init__(self, state_store, recoil_controller, gui_bridge, pubg_config) -> None:
        self.state_store = state_store
        self.recoil_controller = recoil_controller
        self.gui_bridge = gui_bridge
        self.pubg_config = pubg_config
        self._running = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._config_poll_loop,
            name="_config_poll_loop",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        self._stop_event.set()
        thread = self._thread
        if thread is None:
            return
        thread.join(0.2)
        if thread.is_alive():
            logger.warning("config poll loop did not stop within timeout")
        else:
            logger.info("config poll loop stopped")
        self._thread = None

    def _config_poll_loop(self) -> None:
        while self._running and not self._stop_event.is_set():
            if self.pubg_config.parse_config():
                self.pubg_config.debug_print()
                ads = getattr(self.pubg_config, "ads_mode", None)
                if ads:
                    self.gui_bridge.emit_ads_update(ads.upper())
            if self._stop_event.wait(0.1):
                break

    def handle_detection(self, data: dict[str, object]) -> None:
        def normalize_scope(name: object) -> str:
            if not name:
                return "NONE"
            upper = str(name).upper()
            return "SCOPEKH" if "KH" in upper else upper

        state = self.state_store.state
        changed = False

        if "ai_status" in data:
            ai_status = str(data["ai_status"])
            if ai_status == "ACTIVE":
                self.state_store.ai_active_until = time.time() + 0.5
            elif (
                ai_status == "HIBERNATE"
                and time.time() < self.state_store.ai_active_until
            ):
                ai_status = "ACTIVE"

            if state.get("ai_status") != ai_status:
                state["ai_status"] = ai_status
                changed = True

        if "stance" in data and time.time() > self.state_store.stance_lock_until:
            stance = str(data["stance"])
            self.state_store.stance_buffer.append(stance)
            if len(self.state_store.stance_buffer) > 3:
                self.state_store.stance_buffer.pop(0)

            if len(self.state_store.stance_buffer) == 3 and all(
                s == self.state_store.stance_buffer[0]
                for s in self.state_store.stance_buffer
            ):
                target_stance = self.state_store.stance_buffer[0]
                if state.get("stance") != target_stance:
                    state["stance"] = target_stance
                    changed = True

        active_slot = int(state.get("active_slot", 1))
        for slot_num in [1, 2]:
            key = f"gun{slot_num}"
            if key not in data or not data[key]:
                continue

            partial_weapon = dict(data[key])
            old_weapon = state.get(key, {})

            old_scope_raw = (
                old_weapon.get("scope", "NONE")
                if isinstance(old_weapon, dict)
                else "NONE"
            )
            old_scope_norm = normalize_scope(old_scope_raw)
            new_scope_raw = partial_weapon.get("scope", old_scope_raw)
            new_scope_norm = normalize_scope(new_scope_raw)

            new_name = partial_weapon.get("name", "NONE")
            if new_name == "NONE":
                self.state_store.weapon_buffers[key].append("NONE")
                if len(self.state_store.weapon_buffers[key]) < 2:
                    partial_weapon["name"] = old_weapon.get("name", "NONE")
                if len(self.state_store.weapon_buffers[key]) > 5:
                    self.state_store.weapon_buffers[key].pop(0)
            else:
                self.state_store.weapon_buffers[key] = []

            merged_weapon = (
                {**old_weapon, **partial_weapon}
                if isinstance(old_weapon, dict)
                else partial_weapon
            )

            if slot_num == active_slot:
                old_name = (
                    old_weapon.get("name", "NONE")
                    if isinstance(old_weapon, dict)
                    else "NONE"
                )
                detected_name = partial_weapon.get("name", old_name)
                if detected_name != old_name or new_scope_norm != old_scope_norm:
                    if new_scope_norm == "SCOPEKH":
                        state["hybrid_mode"] = "Scope1"
                    changed = True

            if new_scope_norm == "SCOPEKH":
                zoom = "1" if state["hybrid_mode"] == "Scope1" else "4"
                merged_weapon["scope"] = f"ScopeKH_{zoom}"

            state[key] = merged_weapon
            changed = True

        if changed:
            self.recoil_controller.sync_executor()
            self.gui_bridge.emit_state()

            slot = int(state.get("active_slot", 1))
            gun_info = state.get(f"gun{slot}", {})
            if normalize_scope(gun_info.get("scope")) == "SCOPEKH":
                self.gui_bridge.emit_message(
                    "SCOPE",
                    "KH X4" if state.get("hybrid_mode") == "Scope4" else "KH X1",
                )
