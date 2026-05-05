from __future__ import annotations

from PyQt6.QtCore import QObject

from src.core import utils as Utils
from src.core.settings import SettingsManager


# Phát signal backend ra GUI với snapshot state hiện tại
class GuiSignalBridge:
    def __init__(self, backend, state_store) -> None:
        self.backend = backend
        self.state_store = state_store

    def emit_state(self) -> None:
        self.backend.signal_update.emit(self.state_store.snapshot())

    def emit_message(self, title: str, message: str) -> None:
        self.backend.signal_message.emit(title, message)

    def emit_ads_update(self, mode: str) -> None:
        self.backend.signal_ads_update.emit(mode)


# Kết nối input chuột phím với backend và giao diện
class GuiInputBridge(QObject):
    def __init__(self, window, backend):
        super().__init__()
        self.window = window
        self.backend = backend
        self.settings = SettingsManager()
        self.recoil_config = self.backend.executor.config
        self.is_ads = False
        self.ads_toggled = False
        self._ads_reset_timer = None
        self.reload_config()

    def reload_config(self):
        self.guitoggle_key = self.settings.get("keybinds.gui_toggle", "f1").lower()
        if hasattr(self, "keyboard_listener") and self.keyboard_listener:
            self.keyboard_listener.update_guitoggle_key(self.guitoggle_key)

    def handle_input_action(self, action):
        if action == "SLOT_1":
            self.backend.set_slot(1)
            self.window.update_macro_style(True)
        elif action == "SLOT_2":
            self.backend.set_slot(2)
            self.window.update_macro_style(True)

        if not Utils.is_game_active():
            return
        if action == "MACRO_PAUSE":
            self.backend.set_paused(True)
            self.window.update_macro_style(False)

    def handle_raw_key(self, key, pressed):
        if key == self.guitoggle_key and pressed:
            if self.window.isVisible():
                self.window.hide()
            else:
                self.window.show()
            return
        if pressed and not Utils.is_game_active():
            return
        elif key == "f2" and pressed:
            self.backend.reload_config()
        elif key == "r" and pressed:
            pubg_ads = getattr(self.backend.pubg_config, "ads_mode", None)
            ads_mode = (
                pubg_ads.upper()
                if pubg_ads
                else self.settings.get("ads_mode", "HOLD").upper()
            )
            if ads_mode in ["CLICK", "TOGGLE"]:
                self.is_ads = False
                if hasattr(self.window, "crosshair") and self.window.crosshair:
                    self.window.crosshair.reset_toggle_state()

    def handle_mouse_click(self, btn, pressed):
        btn_name = str(btn).lower()
        if btn_name == "right":
            pubg_ads = getattr(self.backend.pubg_config, "ads_mode", None)
            ads_mode = (
                pubg_ads.upper()
                if pubg_ads
                else self.settings.get("ads_mode", "HOLD").upper()
            )
            if ads_mode == "HOLD":
                self.is_ads = pressed
            elif ads_mode in ["CLICK", "TOGGLE"]:
                self.is_ads = True
                if (
                    pressed
                    and self._ads_reset_timer
                    and self._ads_reset_timer.is_alive()
                ):
                    self._ads_reset_timer.cancel()
                    self._ads_reset_timer = None
        if btn_name == "left" and pressed:
            if self._ads_reset_timer and self._ads_reset_timer.is_alive():
                self._ads_reset_timer.cancel()
                self._ads_reset_timer = None
            import win32gui

            flags, _, _ = win32gui.GetCursorInfo()
            cursor_visible = flags != 0

            if not Utils.is_game_active() or cursor_visible:
                return

            pubg_ads = getattr(self.backend.pubg_config, "ads_mode", None)
            ads_mode = (
                pubg_ads.upper()
                if pubg_ads
                else self.settings.get("ads_mode", "HOLD").upper()
            )

            if ads_mode == "HOLD" and not self.is_ads:
                return

            data = self.backend.state
            if data.get("paused", False):
                return

            slot = data.get("active_slot", 1)
            gun_info = data.get(f"gun{slot}", {})
            name = gun_info.get("name", "NONE")
            if name != "NONE":
                self.backend.set_firing(True)
                base_table = self.recoil_config.get_base_table(name)
                if base_table:
                    raw_pixels = self.recoil_config.get_raw_pattern(base_table)
                    self.backend.recoil_controller.start_recoil(
                        raw_pixels, initial_stance=data.get("stance", "Stand")
                    )
        elif btn_name == "left" and not pressed:
            from PyQt6.QtCore import QTimer

            self.backend.set_firing(False)
            self.backend.recoil_controller.stop_recoil()
            if self.backend.executor.full_pattern_done:
                pubg_ads = getattr(self.backend.pubg_config, "ads_mode", None)
                ads_mode = (
                    pubg_ads.upper()
                    if pubg_ads
                    else self.settings.get("ads_mode", "HOLD").upper()
                )
                if ads_mode in ["CLICK", "TOGGLE"]:

                    def _reset_after_empty_mag():
                        self.is_ads = False
                        if hasattr(self.window, "crosshair") and self.window.crosshair:
                            self.window.crosshair.reset_toggle_state()

                    QTimer.singleShot(0, _reset_after_empty_mag)
