import hashlib
from datetime import datetime
from typing import Dict


# ======================================================
#   USER
# ======================================================
class User:
    def __init__(self, user_id: int, username: str, hashed_password: str, salt: str,
                 registration_date: datetime):
        self._user_id = user_id
        self.username = username               # через сеттер
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    # -------------------------
    # Getters
    # -------------------------
    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    # -------------------------
    # username getter/setter
    # -------------------------
    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not value or value.strip() == "":
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value

    # -------------------------
    # Password operations
    # -------------------------
    def change_password(self, new_password: str) -> None:
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        hashed = hashlib.sha256((new_password + self._salt).encode()).hexdigest()
        self._hashed_password = hashed

    def verify_password(self, password: str) -> bool:
        hashed = hashlib.sha256((password + self._salt).encode()).hexdigest()
        return hashed == self._hashed_password

    # -------------------------
    def get_user_info(self) -> dict:
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }


# ======================================================
#   WALLET
# ======================================================
class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code
        self.balance = balance  # setter

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise ValueError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        if amount > self._balance:
            raise ValueError("Недостаточно средств")
        self._balance -= amount

    def get_balance_info(self) -> dict:
        return {
            "currency_code": self.currency_code,
            "balance": self._balance
        }


# ======================================================
#   PORTFOLIO
# ======================================================
class Portfolio:
    def __init__(self, user_id: int, wallets: Dict[str, Wallet] | None = None):
        self._user_id = user_id
        self._wallets = wallets or {}

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        return dict(self._wallets)  # копия

    def add_currency(self, currency_code: str) -> None:
        if currency_code in self._wallets:
            raise ValueError(f"Кошелёк '{currency_code}' уже существует")
        self._wallets[currency_code] = Wallet(currency_code)

    def get_wallet(self, currency_code: str) -> Wallet:
        if currency_code not in self._wallets:
            raise ValueError(f"Кошелёк '{currency_code}' не найден")
        return self._wallets[currency_code]

    def get_total_value(self, base_currency="USD") -> float:
        # Для упрощения — фиктивные курсы
        exchange_rates = {
            "USD": 1.0,
            "EUR": 1.08,
            "BTC": 59000,
            "ETH": 3700,
            "RUB": 0.010,
        }

        if base_currency not in exchange_rates:
            raise ValueError(f"Неизвестная базовая валюта '{base_currency}'")

        total = 0.0
        for w in self._wallets.values():
            if w.currency_code not in exchange_rates:
                continue
            usd_value = w.balance * exchange_rates[w.currency_code]
            base_value = usd_value / exchange_rates[base_currency]
            total += base_value

        return round(total, 4)
