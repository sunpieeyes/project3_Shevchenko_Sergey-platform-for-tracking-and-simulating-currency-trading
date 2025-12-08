import json
from pathlib import Path

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.data_path = Path("data")
        self.users_file = self.data_path / "users.json"
        self.portfolios_file = self.data_path / "portfolios.json"
        self.rates_file = self.data_path / "rates.json"

    def _read_json(self, path):
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _write_json(self, path, data):
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_portfolio(self, user_id):
        portfolios = self._read_json(self.portfolios_file)
        for p in portfolios:
            if p["user_id"] == user_id:
                return {k: Wallet(v["currency_code"], v["balance"]) for k, v in p["wallets"].items()}
        return {}

    def save_portfolio(self, user_id, wallets):
        portfolios = self._read_json(self.portfolios_file)
        for p in portfolios:
            if p["user_id"] == user_id:
                p["wallets"] = {k: {"currency_code": v.currency_code, "balance": v.balance} for k, v in wallets.items()}
                self._write_json(self.portfolios_file, portfolios)
                return
        # Если портфеля нет — добавляем
        portfolios.append({
            "user_id": user_id,
            "wallets": {k: {"currency_code": v.currency_code, "balance": v.balance} for k, v in wallets.items()}
        })
        self._write_json(self.portfolios_file, portfolios)

    def get_rate(self, from_code, to_code):
        rates = self._read_json(self.rates_file)
        key = f"{from_code}_{to_code}"
        return rates.get(key, {"rate": 1.0, "updated_at": None})
