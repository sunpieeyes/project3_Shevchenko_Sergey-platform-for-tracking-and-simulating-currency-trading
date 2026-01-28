from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ..core.utils import load_json, save_json


class RatesStorage:
    def __init__(self, rates_path: str, history_path: str) -> None:
        self.rates_path = Path(rates_path)
        self.history_path = Path(history_path)

    def write_rates_snapshot(self, pairs: dict[str, dict]) -> None:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        data = {"pairs": pairs, "last_refresh": now}
        save_json(str(self.rates_path), data)

    def append_history(self, pairs: dict[str, dict]) -> None:
        # Минимальная история: массив записей
        history = load_json(str(self.history_path))
        if not isinstance(history, list):
            history = []

        for pair, obj in pairs.items():
            entry = {
                "id": f"{pair}_{obj.get('updated_at')}",
                "from_currency": pair.split("_")[0],
                "to_currency": pair.split("_")[1],
                "rate": obj.get("rate"),
                "timestamp": obj.get("updated_at"),
                "source": obj.get("source"),
                "meta": {},
            }
            history.append(entry)

        save_json(str(self.history_path), history)
