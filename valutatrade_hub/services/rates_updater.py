import json
import urllib.request
from datetime import datetime
from pathlib import Path

from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.core.exceptions import ApiRequestError


API_URL = "https://open.er-api.com/v6/latest/USD"   # рабочий API


def update_rates():
    """Обновляет rates.json через публичный API open.er-api.com"""

    settings = SettingsLoader()
    data_path = Path(settings.get("data_path", "data/"))
    rates_file = data_path / "rates.json"
    
    print("USING DATA PATH:", rates_file)

    # --- Запрос к API ---
    try:
        with urllib.request.urlopen(API_URL, timeout=10) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        raise ApiRequestError(f"API request failed: {e}")

    # --- Валидация ответа ---
    if raw.get("result") != "success" or "rates" not in raw:
        raise ApiRequestError("Invalid API response")

    rates = raw["rates"]

    # Иногда API возвращает base_code, иногда base
    base = raw.get("base_code") or raw.get("base") or "USD"

    if not isinstance(base, str):
        base = "USD"

    # --- Форматирование ---
    formatted = {}

    for code, val in rates.items():
        if not isinstance(code, str):
            continue
        if not isinstance(val, (int, float)):
            continue

        # USD_EUR
        formatted[f"{base}_{code}"] = val

        # EUR_USD
        if val != 0:
            formatted[f"{code}_{base}"] = 1 / val

    final_data = {
        "updated_at": datetime.utcnow().isoformat(),
        "rates": formatted
    }

    rates_file.parent.mkdir(parents=True, exist_ok=True)

    with rates_file.open("w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)

    return True
