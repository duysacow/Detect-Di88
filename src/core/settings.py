import copy
import json
import logging
import os
import stat
import threading
from pathlib import Path

from src.core.path_utils import ensure_safe_output_path, get_resource_path, get_user_data_path

logger = logging.getLogger(__name__)


# Quản lý đọc ghi cài đặt ứng dụng
class SettingsManager:
    """Manages application settings with persistent storage"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.settings_file = get_user_data_path("settings.json")
            self.default_settings_file = Path(
                get_resource_path(os.path.join("src", "config", "settings.json"))
            )
            self._cache = None
            self.initialized = True

    def _get_defaults(self):
        """Default settings structure - FULL project defaults"""
        return {
            "keybinds": {"gui_toggle": "f1"},
            "ads_mode": "HOLD",
            "crosshair": {
                "active": True,
                "style": "x",
                "color": "Red",
                "color_index": 0,
                "toggle_key": "home",
                "ads_mode": "HOLD",
            },
            "capture_mode": "DXCAM",
            "overlay_enabled": True,
            "fast_loot_key": "caps_lock",
            "fast_loot": True,
            "slide_trick": True,
            "overlay_key": "delete",
            "scope_intensity": {
                "normal": 100,
                "x2": 100,
                "x3": 100,
                "x4": 100,
                "x6": 100,
            },
        }

    def load(self):
        """Load settings from file, create with defaults if not exists"""
        if self._cache is not None:
            return self._cache

        defaults = self._load_default_settings()
        if not self.settings_file.exists():
            self._cache = defaults
            return self._cache

        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                loaded_settings = json.load(f)
            sanitized_user_settings = self._sanitize_user_settings(
                loaded_settings,
                prune_defaults=True,
                default_reference=defaults,
            )
            if sanitized_user_settings != loaded_settings:
                try:
                    self._persist_user_settings(sanitized_user_settings)
                except Exception:
                    logger.warning(
                        "Failed to persist migrated user settings to %s; using in-memory sanitized settings",
                        self.settings_file,
                        exc_info=True,
                    )
            self._cache = self._merge_with_defaults(sanitized_user_settings, defaults)

        except Exception:
            logger.exception("Failed to load settings, using defaults")
            self._cache = defaults

        return self._cache

    def _load_default_settings(self):
        defaults = self._get_defaults()
        if self.default_settings_file.exists():
            try:
                with open(self.default_settings_file, "r", encoding="utf-8") as f:
                    bundled_defaults = json.load(f)
                if isinstance(bundled_defaults, dict):
                    self._merge_defaults(bundled_defaults, defaults)
                    return bundled_defaults
            except Exception:
                logger.exception(
                    "Failed to load bundled default settings from %s",
                    self.default_settings_file,
                )
        return defaults

    def _merge_defaults(self, current, defaults):
        """Merge defaults into current settings (adds missing keys)"""
        for key, value in defaults.items():
            if key not in current:
                current[key] = value
            elif isinstance(value, dict) and isinstance(current[key], dict):
                self._merge_defaults(current[key], value)

    def save(self, settings=None):
        """Save settings to file"""
        if settings is None:
            settings = self._cache

        if settings is None:
            return

        defaults = self._load_default_settings()
        user_settings = self._sanitize_user_settings(
            settings,
            prune_defaults=True,
            default_reference=defaults,
        )

        settings_file = ensure_safe_output_path(self.settings_file, purpose="settings file")
        settings_file.parent.mkdir(parents=True, exist_ok=True)

        with self._lock:
            try:
                self._write_settings_file(settings_file, user_settings)
                self._cache = self._merge_with_defaults(user_settings, defaults)
                return True
            except PermissionError:
                logger.warning(
                    "Permission denied while saving settings to %s; trying recovery",
                    settings_file,
                    exc_info=True,
                )
                try:
                    settings_file.parent.mkdir(parents=True, exist_ok=True)
                    if settings_file.exists():
                        os.chmod(settings_file, stat.S_IWRITE | stat.S_IREAD)
                    self._write_settings_file(settings_file, user_settings)
                    self._cache = self._merge_with_defaults(user_settings, defaults)
                    return True
                except Exception:
                    logger.warning(
                        "Settings recovery failed for %s; keeping in-memory cache only",
                        settings_file,
                        exc_info=True,
                    )
                    self._cache = self._merge_with_defaults(user_settings, defaults)
                    return False
            except Exception:
                logger.exception("Failed to save settings to %s", settings_file)
                self._cache = self._merge_with_defaults(user_settings, defaults)
                return False

    def _write_settings_file(self, settings_file: Path, settings: dict) -> None:
        temp_file = settings_file.with_suffix(f"{settings_file.suffix}.tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, settings_file)

    def get(self, key, default=None):
        """Get setting value by key (supports nested keys with dot notation)"""
        settings = self.load()

        keys = key.split(".")
        value = settings

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key, value):
        """Set setting value by key (supports nested keys with dot notation)"""
        settings = self.load()

        keys = key.split(".")
        current = settings

        for i, k in enumerate(keys[:-1]):
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value
        self.save(settings)

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        defaults = self._load_default_settings()
        self.save({})
        self._cache = defaults
        return defaults

    def _merge_with_defaults(self, user_settings, defaults=None):
        merged = copy.deepcopy(defaults or self._load_default_settings())
        if isinstance(user_settings, dict):
            self._merge_user_settings(merged, user_settings)
        return merged

    def _merge_user_settings(self, target, source):
        for key, value in source.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                self._merge_user_settings(target[key], value)
            else:
                target[key] = copy.deepcopy(value)

    def _normalize_capture_mode(self, mode):
        normalized = str(mode or "DXCAM").strip().upper()
        return "MSS" if normalized == "MSS" else "DXCAM"

    def _normalize_key_value(self, value, default_value):
        text = str(value or default_value).strip().lower()
        return text or str(default_value).strip().lower()

    def _normalize_ads_mode(self, value, default_value="HOLD"):
        return str(value or default_value).strip().upper() or str(default_value).strip().upper()

    def _normalize_crosshair_color(self, value, default_value="Red"):
        normalized = str(value or default_value).strip()
        mojibake_map = {
            "Tráº¯ng": "Trắng",
            "Äá»": "Đỏ",
            "VÃ ng": "Vàng",
            "Xanh LÃ¡": "Xanh Lá",
            "Xanh Ngá»c": "Xanh Ngọc",
            "Xanh DÆ°Æ¡ng": "Xanh Dương",
        }
        return mojibake_map.get(normalized, normalized or str(default_value).strip())

    def _sanitize_user_settings(self, settings, prune_defaults=False, default_reference=None):
        if not isinstance(settings, dict):
            settings = {}

        defaults = copy.deepcopy(default_reference or self._load_default_settings())
        sanitized = {}

        keybinds = settings.get("keybinds")
        if isinstance(keybinds, dict):
            sanitized["keybinds"] = {
                "gui_toggle": self._normalize_key_value(
                    keybinds.get("gui_toggle"),
                    defaults.get("keybinds", {}).get("gui_toggle", "f1"),
                )
            }

        sanitized["ads_mode"] = self._normalize_ads_mode(
            settings.get("ads_mode"),
            defaults.get("ads_mode", "HOLD"),
        )
        sanitized["capture_mode"] = self._normalize_capture_mode(
            settings.get("capture_mode", defaults.get("capture_mode", "DXCAM"))
        )
        sanitized["fast_loot_key"] = self._normalize_key_value(
            settings.get("fast_loot_key"),
            defaults.get("fast_loot_key", "caps_lock"),
        )
        sanitized["fast_loot"] = bool(settings.get("fast_loot", defaults.get("fast_loot", True)))
        sanitized["slide_trick"] = bool(
            settings.get("slide_trick", defaults.get("slide_trick", True))
        )
        sanitized["overlay_enabled"] = bool(
            settings.get("overlay_enabled", defaults.get("overlay_enabled", True))
        )
        sanitized["overlay_key"] = self._normalize_key_value(
            settings.get("overlay_key"),
            defaults.get("overlay_key", "delete"),
        )

        scope_defaults = defaults.get("scope_intensity", {})
        scope_settings = settings.get("scope_intensity", {})
        if not isinstance(scope_settings, dict):
            scope_settings = {}
        sanitized["scope_intensity"] = {}
        for scope_key in ("normal", "x2", "x3", "x4", "x6"):
            sanitized["scope_intensity"][scope_key] = int(
                scope_settings.get(scope_key, scope_defaults.get(scope_key, 100))
            )

        crosshair_defaults = defaults.get("crosshair", {})
        crosshair_settings = settings.get("crosshair", {})
        if not isinstance(crosshair_settings, dict):
            crosshair_settings = {}
        sanitized["crosshair"] = {
            "active": bool(crosshair_settings.get("active", crosshair_defaults.get("active", True))),
            "style": str(crosshair_settings.get("style", crosshair_defaults.get("style", "x"))),
            "color": self._normalize_crosshair_color(
                crosshair_settings.get("color"),
                crosshair_defaults.get("color", "Red"),
            ),
            "color_index": int(
                crosshair_settings.get(
                    "color_index",
                    crosshair_defaults.get("color_index", 0),
                )
            ),
            "toggle_key": self._normalize_key_value(
                crosshair_settings.get("toggle_key"),
                crosshair_defaults.get("toggle_key", "home"),
            ),
            "ads_mode": self._normalize_ads_mode(
                crosshair_settings.get("ads_mode"),
                crosshair_defaults.get("ads_mode", "HOLD"),
            ),
        }

        aim_settings = settings.get("aim")
        if isinstance(aim_settings, dict):
            sanitized_aim = {}
            runtime_settings = aim_settings.get("runtime")
            if isinstance(runtime_settings, dict):
                sanitized_aim["runtime"] = {
                    "capture_backend": str(
                        runtime_settings.get(
                            "capture_backend",
                            defaults.get("aim", {}).get("runtime", {}).get(
                                "capture_backend",
                                "DirectX",
                            ),
                        )
                    ),
                    "model": str(
                        runtime_settings.get(
                            "model",
                            defaults.get("aim", {}).get("runtime", {}).get("model", ""),
                        )
                    ),
                }

            meta_settings = aim_settings.get("meta")
            if isinstance(meta_settings, dict):
                sanitized_aim["meta"] = {
                    "last_loaded_model": str(
                        meta_settings.get(
                            "last_loaded_model",
                            defaults.get("aim", {}).get("meta", {}).get(
                                "last_loaded_model",
                                "N/A",
                            ),
                        )
                    )
                }

            for section_name in (
                "bindings",
                "sliders",
                "toggles",
                "dropdowns",
                "colors",
                "file_locations",
                "minimize",
            ):
                section_value = aim_settings.get(section_name)
                if isinstance(section_value, dict):
                    sanitized_aim[section_name] = copy.deepcopy(section_value)

            if sanitized_aim:
                sanitized["aim"] = sanitized_aim

        if prune_defaults:
            sanitized_defaults = self._sanitize_user_settings(
                defaults,
                prune_defaults=False,
                default_reference=defaults,
            )
            sanitized = self._prune_default_values(sanitized, sanitized_defaults) or {}

        return sanitized

    def _prune_default_values(self, value, defaults):
        if isinstance(value, dict) and isinstance(defaults, dict):
            pruned = {}
            for key, current_value in value.items():
                default_value = defaults.get(key)
                pruned_value = self._prune_default_values(current_value, default_value)
                if pruned_value is not None:
                    pruned[key] = pruned_value
            return pruned or None
        if value == defaults:
            return None
        return copy.deepcopy(value)

    def _persist_user_settings(self, settings):
        settings_file = ensure_safe_output_path(self.settings_file, purpose="settings file")
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self._write_settings_file(settings_file, settings or {})
