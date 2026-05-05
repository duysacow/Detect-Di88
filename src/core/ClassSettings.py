import json
from pathlib import Path
import threading

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
        if not hasattr(self, 'initialized'):
            self.settings_file = Path(__file__).resolve().parents[1] / "config" / "settings.json"
            self._cache = None
            self.initialized = True
    
    def _get_defaults(self):
        """Default settings structure - FULL project defaults"""
        return {
            "keybinds": {
                "gui_toggle": "f1"
            },
            "ads_mode": "HOLD",
            "stop_keys": ["x", "g", "5"],
            "crosshair": {
                "active": True,
                "style": "1: Gap Cross",
                "color": "Red",
                "ads_mode": "HOLD"
            },
            "capture_mode": "MSS"
        }
    
    def load(self):
        """Load settings from file, create with defaults if not exists"""
        if self._cache is not None:
            return self._cache
        
        if not self.settings_file.exists():
            # Create with defaults
            defaults = self._get_defaults()
            self.save(defaults)
            self._cache = defaults
            return self._cache
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                self._cache = json.load(f)
                
            # Merge with defaults (in case new settings were added)
            defaults = self._get_defaults()
            self._merge_defaults(self._cache, defaults)
            
        except Exception as e:
            print(f"[WARN] Failed to load settings: {e}, using defaults")
            self._cache = self._get_defaults()
        
        return self._cache
    
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
        
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            self._cache = settings
    
    def get(self, key, default=None):
        """Get setting value by key (supports nested keys with dot notation)"""
        settings = self.load()
        
        keys = key.split('.')
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
        
        keys = key.split('.')
        current = settings
        
        for i, k in enumerate(keys[:-1]):
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        self.save(settings)
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        defaults = self._get_defaults()
        self.save(defaults)
        return defaults
