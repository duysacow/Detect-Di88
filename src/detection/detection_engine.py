import ctypes
import logging
import os
import re

import cv2

from src.core.path_utils import get_resource_path
from src.core.settings import SettingsManager

logger = logging.getLogger(__name__)


# Nhận diện súng, phụ kiện và trạng thái từ ảnh chụp.
class DetectionEngine:
    def __init__(self, template_folder=None, screen_width=None, screen_height=None):
        self.base_dir = get_resource_path("")
        self.settings = SettingsManager()
        self.screen_width, self.screen_height = self._resolve_screen_size(
            screen_width, screen_height
        )
        requested_template_folder = (
            template_folder
            or self._select_template_folder(self.screen_width, self.screen_height)
        )
        self.template_folder, self.template_dir = self._resolve_template_dir(
            requested_template_folder
        )
        self.thresholds = self._load_thresholds()

        self.templates = {
            "weapons": {},
            "ui": {},
            "accessories": {},
            "grip": {},
            "scopes": {},
            "stances": {},
            "dieukien": {},
        }

        total_count = 0
        for category in self.templates:
            total_count += self._load_category(category)

        logger.info(
            "Template selected: %s (%sx%s)",
            self.template_folder,
            self.screen_width,
            self.screen_height,
        )
        logger.info("Detection engine loaded %s templates (BGR mode)", total_count)

    def _load_thresholds(self) -> dict[str, float]:
        return {
            "default_match": float(
                self.settings.get("detection.thresholds.default_match", 0.8)
            ),
            "weapon_name": float(
                self.settings.get("detection.thresholds.weapon_name", 0.8)
            ),
            "accessory": float(
                self.settings.get("detection.thresholds.accessory", 0.8)
            ),
            "grip": float(self.settings.get("detection.thresholds.grip", 0.8)),
            "scope": float(self.settings.get("detection.thresholds.scope", 0.8)),
            "ui_anchor": float(
                self.settings.get("detection.thresholds.ui_anchor", 0.65)
            ),
            "ui_gate": float(self.settings.get("detection.thresholds.ui_gate", 0.4)),
            "stance": float(self.settings.get("detection.thresholds.stance", 0.6)),
            "early_exit": float(
                self.settings.get("detection.thresholds.early_exit", 0.98)
            ),
        }

    def _resolve_screen_size(self, screen_width, screen_height):
        if screen_width is not None and screen_height is not None:
            return int(screen_width), int(screen_height)

        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    def _select_template_folder(self, screen_width, screen_height):
        if screen_height >= 1440:
            return "3440x1440"
        return "1920x1080"

    def _resolve_template_dir(self, template_folder):
        candidates = [
            os.path.join(self.base_dir, template_folder),
            os.path.join(self.base_dir, "src", "Template", template_folder),
        ]

        for path in candidates:
            if os.path.exists(path):
                return template_folder, path

        fallback_folder = "1920x1080"
        fallback_path = os.path.join(self.base_dir, "src", "Template", fallback_folder)
        logger.warning(
            "Template folder '%s' not found, fallback path=%s",
            template_folder,
            fallback_path,
        )
        return fallback_folder, fallback_path

    def _load_category(self, category):
        category_dir = {"stances": "stance"}.get(category, category)
        path = os.path.join(self.template_dir, category_dir)
        if not os.path.exists(path):
            return 0

        count = 0
        for file in os.listdir(path):
            if not file.lower().endswith((".png", ".jpg", ".jpeg")):
                continue

            full_path = os.path.join(path, file)
            img = cv2.imread(full_path)
            if img is None:
                logger.warning("Failed to load template image: %s", full_path)
                continue

            name = os.path.splitext(file)[0].upper()
            self.templates[category][name] = img
            count += 1
        return count

    def _match_result(self, roi, category, threshold=None):
        if category not in self.templates or not self.templates[category]:
            return "NONE", -1.0

        threshold = (
            self.thresholds["default_match"] if threshold is None else float(threshold)
        )
        early_exit = self.thresholds["early_exit"]
        max_val = -1.0
        best_name = "NONE"

        for name, tpl in self.templates[category].items():
            if tpl.shape[0] > roi.shape[0] or tpl.shape[1] > roi.shape[1]:
                continue

            res = cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED)
            _, val, _, _ = cv2.minMaxLoc(res)

            if val > max_val:
                max_val = val
                best_name = name

            if val > early_exit:
                break

        if max_val >= threshold:
            return best_name, float(max_val)
        return "NONE", float(max_val)

    def _match(self, roi, category, threshold=None):
        best_name, _ = self._match_result(roi, category, threshold)
        return best_name

    def detect_weapon_name(self, roi, threshold=None):
        threshold = self.thresholds["weapon_name"] if threshold is None else threshold
        return self._match(roi, "weapons", threshold)

    def detect_ui_anchor(self, roi, threshold=None):
        threshold = self.thresholds["ui_anchor"] if threshold is None else threshold
        return self._match(roi, "dieukien", threshold)

    def detect_accessory(self, roi, threshold=None):
        threshold = self.thresholds["accessory"] if threshold is None else threshold
        res = self._match(roi, "accessories", threshold)
        if res == "NONE":
            return "NONE"

        name = res.upper()
        if "GIAMGIAT" in name:
            return "GiamGiat"
        if "ANTIALUA" in name:
            return "AnTiaLua"
        if "GIAMRUNG" in name:
            return "GiamRung"
        if "ATLSMG" in name:
            return "ATLsmg"
        if "GGIATSMG" in name:
            return "GGiatSMG"
        if "GTHANHSMG" in name:
            return "GThanhSMG"
        return res

    def detect_grip(self, roi, threshold=None):
        threshold = self.thresholds["grip"] if threshold is None else threshold
        res = self._match(roi, "grip", threshold)
        if res == "NONE":
            return "NONE"

        name = res.upper()
        if "TCDUNG" in name:
            return "tcDung"
        if "TCHONG" in name:
            return "tcHong"
        if "TCLASER" in name:
            return "tcLaser"
        if "TCNAMCHAT" in name:
            return "tcNamChat"
        if "TCNGHIENG" in name:
            return "tcNghieng"
        if "TCNHE" in name:
            return "tcNhe"
        return res

    def detect_scope(self, roi, threshold=None):
        threshold = self.thresholds["scope"] if threshold is None else threshold
        res = self._match(roi, "scopes", threshold)
        if res == "NONE":
            return "NONE"

        name = res.upper()
        if "SCOPEKH" in name:
            return "ScopeKH"

        match = re.search(r"SCOPE(\d+)", name)
        if match:
            return "Scope" + match.group(1)

        return res

    def _map_stance_template_name(self, template_name: str) -> str | None:
        upper = str(template_name or "").upper()
        if upper in {"DUNG", "STAND", "STANDING"}:
            return "Stand"
        if upper in {"NGOI", "CROUCH", "CROUCHING", "SIT", "SITTING"}:
            return "Crouch"
        if upper in {"NAM", "PRONE", "LYING"}:
            return "Prone"
        return None

    def detect_stance(self, roi, threshold=None, roi_name="stance"):
        threshold = self.thresholds["stance"] if threshold is None else threshold
        template_name, score = self._match_result(roi, "stances", threshold)
        matched_label = (
            None if template_name == "NONE" else self._map_stance_template_name(template_name)
        )
        roi_desc = f"{roi_name}[{roi.shape[1]}x{roi.shape[0]}]"
        logger.info(
            "stance detect: template_name=%s matched_label=%s score=%.4f roi=%s",
            template_name,
            matched_label or "NONE",
            score,
            roi_desc,
        )
        return matched_label
