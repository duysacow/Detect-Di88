from __future__ import annotations

from src.recoil.sensitivity import SensitivityCalculator


# Đồng bộ state vũ khí với executor recoil hiện tại
class RecoilController:
    def __init__(self, state_store, executor, pubg_config) -> None:
        self.state_store = state_store
        self.executor = executor
        self.pubg_config = pubg_config
        self.sens_calculator = SensitivityCalculator()

    def sync_executor(self) -> None:
        slot = self.state_store.get_active_slot()
        gun_info = dict(self.state_store.state[f"gun{slot}"])
        state = self.state_store.state

        self.executor.live_stance = state["stance"]
        self.executor.current_gun_name = gun_info["name"]

        sens_multiplier = self.sens_calculator.calculate_sens_multiplier(
            self.pubg_config,
            gun_info,
            hybrid_mode=state.get("hybrid_mode", "Scope1"),
        )

        base_mult = self.executor.config.get_master_multiplier(gun_info)
        self.executor.gun_base_mult = base_mult * sens_multiplier
        stance_map = self.executor.config.get_all_stance_multipliers(gun_info["name"])
        self.executor.st_stand = float(stance_map["Stand"])
        self.executor.st_crouch = float(stance_map["Crouch"])
        self.executor.st_prone = float(stance_map["Prone"])

    def set_live_stance(self, stance: str) -> None:
        self.executor.live_stance = stance

    def start_recoil(self, raw_pixels, initial_stance: str) -> None:
        self.executor.start_recoil(raw_pixels, initial_stance=initial_stance)

    def stop_recoil(self) -> None:
        self.executor.stop_recoil()

    def reload_config(self) -> None:
        self.executor.reload_config()
