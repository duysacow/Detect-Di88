import copy
import time

from PyQt6.QtCore import QThread, pyqtSignal

from src.core.key_poller import KeyPollingThread
from src.core.pubg_config import PubgConfig
from src.core.settings import SettingsManager
from src.core.vision_worker import VisionWorker
from src.detection.capture import ScreenCapture
from src.detection.detection_engine import DetectionEngine
from src.recoil.executor import RecoilExecutor
from src.recoil.sensitivity import SensitivityCalculator


# Điều phối backend, state game và đồng bộ recoil
class BackendThread(QThread):
    signal_update = pyqtSignal(object)
    signal_message = pyqtSignal(str, str)
    signal_ads_update = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True
        settings = SettingsManager()
        self.capture = ScreenCapture(capture_mode="DXCAM")
        self.detector = DetectionEngine(template_folder="FullHD")
        self.executor = RecoilExecutor()

        self.state = {
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

        self.stance_lock_until = 0.0
        self.ai_active_until = 0.0

        self.stance_buffer = []
        self.weapon_buffers = {"gun1": [], "gun2": []}
        self.menu_blocked = False

        self.pubg_config = PubgConfig()
        self.sens_calculator = SensitivityCalculator()

        if self.pubg_config.parse_config():
            self.pubg_config.debug_print()

        self.vision_worker = VisionWorker(self, self.capture, self.detector)
        self.vision_worker.signal_vision_update.connect(self._on_vision_update)
        self.vision_worker.start()
        self.poller = KeyPollingThread(self)
        self.poller.start()

    def _sync_executor(self):
        slot = self.state["active_slot"]
        gun_info = copy.deepcopy(self.state[f"gun{slot}"])

        self.executor.live_stance = self.state["stance"]
        self.executor.current_gun_name = gun_info["name"]

        sens_multiplier = self.sens_calculator.calculate_sens_multiplier(
            self.pubg_config,
            gun_info,
            hybrid_mode=self.state.get("hybrid_mode", "Scope1"),
        )

        base_mult = self.executor.config.get_master_multiplier(gun_info)
        self.executor.gun_base_mult = base_mult * sens_multiplier
        st = self.executor.config.get_all_stance_multipliers(gun_info["name"])

        self.executor.st_stand = float(st["Stand"])
        self.executor.st_crouch = float(st["Crouch"])
        self.executor.st_prone = float(st["Prone"])

    def toggle_hybrid_mode(self):
        """Chuyển đổi giữa X1 và X4 cho Scope Kết Hợp"""
        if self.state.get("hybrid_mode") == "Scope1":
            self.state["hybrid_mode"] = "Scope4"
        else:
            self.state["hybrid_mode"] = "Scope1"

        slot = self.state.get("active_slot", 1)
        gun_key = f"gun{slot}"
        current_scope = self.state[gun_key].get("scope", "")
        if "KH" in str(current_scope).upper():
            zoom = "1" if self.state["hybrid_mode"] == "Scope1" else "4"
            self.state[gun_key]["scope"] = f"ScopeKH_{zoom}"

        msg = "KH X4" if self.state["hybrid_mode"] == "Scope4" else "KH X1"
        self.signal_message.emit("SCOPE", msg)

        self._sync_executor()
        self.signal_update.emit(self.state)

    def reload_config(self):
        self.executor.reload_config()
        self.poller.refresh_settings()
        self.signal_message.emit("SUCCESS", "CONFIG REFRESHED!")

    def _on_vision_update(self, data):
        """
        XỬ LÝ CÁC THAY ĐỔI TỪ VISION (ZIN Logic)
        """

        def normalize_scope(name):
            if not name:
                return "NONE"
            n = str(name).upper()
            if "KH" in n:
                return "SCOPEKH"
            return n

        new_state = copy.deepcopy(self.state)
        changed = False

        if "ai_status" in data:
            if data["ai_status"] == "ACTIVE":
                self.ai_active_until = time.time() + 0.5
            elif (
                data["ai_status"] == "HIBERNATE" and time.time() < self.ai_active_until
            ):
                data["ai_status"] = "ACTIVE"

            if new_state.get("ai_status") != data["ai_status"]:
                new_state["ai_status"] = data["ai_status"]
                changed = True

        if "stance" in data:
            if time.time() > self.stance_lock_until:
                self.stance_buffer.append(data["stance"])
                if len(self.stance_buffer) > 3:
                    self.stance_buffer.pop(0)

                if len(self.stance_buffer) == 3 and all(
                    s == self.stance_buffer[0] for s in self.stance_buffer
                ):
                    target_stance = self.stance_buffer[0]
                    if new_state.get("stance") != target_stance:
                        new_state["stance"] = target_stance
                        changed = True

        active_slot = new_state.get("active_slot", 1)

        for slot_num in [1, 2]:
            key = f"gun{slot_num}"
            if key in data and data[key]:
                partial_weapon = data[key]
                old_weapon = self.state.get(key, {})

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
                    self.weapon_buffers[key].append("NONE")
                    if len(self.weapon_buffers[key]) < 2:
                        partial_weapon["name"] = old_weapon.get("name", "NONE")
                    if len(self.weapon_buffers[key]) > 5:
                        self.weapon_buffers[key].pop(0)
                else:
                    self.weapon_buffers[key] = []

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
                    new_name = partial_weapon.get("name", old_name)

                    if new_name != old_name or new_scope_norm != old_scope_norm:
                        if new_scope_norm == "SCOPEKH":
                            new_state["hybrid_mode"] = "Scope1"
                        changed = True

                if new_scope_norm == "SCOPEKH":
                    zoom = "1" if new_state["hybrid_mode"] == "Scope1" else "4"
                    merged_weapon["scope"] = f"ScopeKH_{zoom}"

                new_state[key] = merged_weapon
                changed = True

        if changed:
            new_state["firing"] = self.state.get("firing", False)
            new_state["paused"] = self.state.get("paused", False)
            new_state["active_slot"] = self.state.get("active_slot", 1)

            self.state = new_state
            self._sync_executor()

            self.signal_update.emit(copy.deepcopy(self.state))

            slot = self.state.get("active_slot", 1)
            gun_info = self.state.get(f"gun{slot}", {})
            if normalize_scope(gun_info.get("scope")) == "SCOPEKH":
                msg = "KH X4" if self.state.get("hybrid_mode") == "Scope4" else "KH X1"
                self.signal_message.emit("SCOPE", msg)

    def set_slot(self, slot):
        self.state["paused"] = False

        if self.state.get("active_slot") != slot:
            self.state["active_slot"] = slot

        self._sync_executor()
        self.signal_update.emit(copy.deepcopy(self.state))

    def set_paused(self, paused):
        self.state["paused"] = paused
        self.signal_update.emit(copy.deepcopy(self.state))

    def set_firing(self, is_firing):
        """Cập nhật trạng thái đang bắn để Overlay đổi màu"""
        if self.state.get("firing") != is_firing:
            self.state["firing"] = is_firing
            self.signal_update.emit(copy.deepcopy(self.state))

    def set_stance_by_key(self, stance):
        """Cập nhật tư thế từ phím bấm (Ưu tiên tuyệt đối)"""
        if stance == "Crouch" and self.state.get("stance") == "Crouch":
            stance = "Stand"
        elif stance == "Prone" and self.state.get("stance") == "Prone":
            stance = "Stand"

        self.state["stance"] = stance
        self.stance_buffer = [stance] * 3
        self.stance_lock_until = time.time() + 0.8

        if self.executor:
            self.executor.live_stance = stance

        self.signal_update.emit(copy.deepcopy(self.state))

    def stop(self):
        self.running = False
        self.vision_worker.running = False
        self.poller.running = False
        self.quit()
