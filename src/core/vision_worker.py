import concurrent.futures
import hashlib
import time

import win32api
import win32gui
from PyQt6.QtCore import QThread, pyqtSignal

from src.core import utils as Utils


# Luồng xử lý nhận diện hình ảnh và trạng thái game
class VisionWorker(QThread):
    signal_vision_update = pyqtSignal(object)

    def __init__(self, backend, capture, detector):
        super().__init__()
        self.backend = backend
        self.capture = capture
        self.detector = detector
        self.running = True

    def run(self):
        """HÀM KHỞI CHẠY LUỒNG (Bắt buộc của QThread)"""
        self.run_vision_loop()

    def run_vision_loop(self):
        last_hashes = {}
        last_cfg_check = 0.0

        while self.running:
            now = time.time()
            if now - last_cfg_check >= 0.1:
                last_cfg_check = now
                if self.backend.pubg_config.parse_config():
                    self.backend.pubg_config.debug_print()
                    ads = getattr(self.backend.pubg_config, "ads_mode", None)
                    if ads:
                        self.backend.signal_ads_update.emit(ads.upper())

            try:
                if not Utils.is_game_active():
                    time.sleep(0.5)
                    continue

                menu_blocked = getattr(self.backend, "menu_blocked", False)
                flags, h_cursor, (cx, cy) = win32gui.GetCursorInfo()
                self.is_cursor_visible = flags != 0
                self.is_tab_held = (win32api.GetAsyncKeyState(0x09) & 0x8000) != 0

                if not self.is_cursor_visible and self.backend:
                    self.backend.inventory_gate = False
            except Exception:
                self.is_tab_held = False
                self.is_cursor_visible = False
                menu_blocked = getattr(self.backend, "menu_blocked", False)

            img = self.capture.grab_regional_image()
            if img is None:
                time.sleep(0.01)
                continue

            new_vision_state = {}
            if not menu_blocked:
                roi_img = self.capture.get_roi_from_image(img, "stance")
                if roi_img is not None:
                    curr_hash = hashlib.md5(roi_img.tobytes()).hexdigest()
                    if last_hashes.get("stance") != curr_hash:
                        last_hashes["stance"] = curr_hash
                        new_vision_state["stance"] = self.detector.detect_stance(
                            roi_img
                        )

            if not self.is_cursor_visible or menu_blocked:
                new_vision_state["ai_status"] = "HIBERNATE"
                self.signal_vision_update.emit(new_vision_state)
                time.sleep(0.03)
                continue

            roi_dieukien = self.capture.get_roi_from_image(img, "dieukien")
            if (
                roi_dieukien is None
                or self.detector.detect_ui_anchor(roi_dieukien, threshold=0.4) == "NONE"
            ):
                new_vision_state["ai_status"] = "HIBERNATE"
                self.signal_vision_update.emit(new_vision_state)
                time.sleep(0.03)
                continue

            new_vision_state["ai_status"] = "ACTIVE"

            def scan_slot(i):
                """Quét 1 slot súng. Chạy song song với slot kia."""
                s_key = f"gun{i}"
                roi_types = {
                    "name": "name",
                    "scope": "scope",
                    "grip": "grip",
                    "muzzle": "accessories",
                }
                detected = {}
                for r_type, field in roi_types.items():
                    roi_name = f"{s_key}_{r_type}"
                    roi_img = self.capture.get_roi_from_image(img, roi_name)
                    if roi_img is None:
                        continue
                    curr_hash = hashlib.md5(roi_img.tobytes()).hexdigest()
                    if last_hashes.get(roi_name) == curr_hash:
                        continue
                    last_hashes[roi_name] = curr_hash

                    if r_type == "name":
                        detected[field] = self.detector.detect_weapon_name(roi_img)
                    elif r_type == "scope":
                        detected[field] = self.detector.detect_scope(roi_img)
                    elif r_type == "grip":
                        detected[field] = self.detector.detect_grip(roi_img)
                    elif r_type == "muzzle":
                        detected[field] = self.detector.detect_accessory(roi_img)

                return s_key, detected

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
                futures = {ex.submit(scan_slot, i): i for i in [1, 2]}
                for fut in concurrent.futures.as_completed(futures):
                    s_key, detected = fut.result()
                    if detected:
                        new_vision_state[s_key] = detected
                        new_vision_state["ai_status"] = "ACTIVE"

            self.signal_vision_update.emit(new_vision_state)
            time.sleep(0.02)
