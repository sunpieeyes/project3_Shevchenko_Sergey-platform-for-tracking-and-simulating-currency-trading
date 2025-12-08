import json
from pathlib import Path
from threading import Lock

class SettingsLoader:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = None):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.config_path = Path(config_path or "valutatrade_hub/config.json")
        self._data = {}
        self.reload()

    def reload(self):
        if self.config_path.exists():
            with self.config_path.open("r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = {
                "data_path": "data/",
                "RATES_TTL_SECONDS": 300,
                "default_base_currency": "USD",
                "log_path": "logs/actions.log"
            }

    def get(self, key: str, default=None):
        return self._data.get(key, default)
