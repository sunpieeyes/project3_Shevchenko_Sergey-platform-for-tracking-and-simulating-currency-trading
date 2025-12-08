from datetime import datetime
import hashlib
from typing import Dict
from valutatrade_hub.core.exceptions import InsufficientFundsError

class User:
    def __init__(self, user_id: int, username: str, password: str, salt: str = None, registration_date: str = None):
        self._user_id = user_id
        self._username = username
        self._salt = salt or self._generate_salt()
        self._hashed_password = self._hash_password(password, self._salt)
        self._registration_date = registration_date or datetime.utcnow().isoformat()

    @staticmethod
    def _generate_salt() -> str:
        import secrets
        return secrets.token_hex(8)

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

    def verify_password(self, password: str) -> bool:
        return self._hash_password(password, self._salt) == self._hashed_password

    def change_password(self, new_password: str):
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._hashed_password = self._hash_password(new_password, self._salt)

    def get_user_info(self) -> Dict:
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date
        }

    @property
    def username(self):
        return self._username

    @property
    def user_id(self):
        return self._user_id


class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code.upper()
        self._balance = float(balance)

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("Баланс должен быть положительным числом")
        self._balance = float(value)

    def deposit(self, amount: float):
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")
        self._balance += amount

    def withdraw(self, amount: float):
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")
        if amount > self._balance:
            raise InsufficientFundsError(self._balance, amount, self.currency_code)
        self._balance -= amount

    def get_balance_info(self):
        return f"{self.currency_code}: {self._balance:.4f}"


class Portfolio:
    def __init__(self, user_id: int, wallets: Dict[str, Wallet] = None):
        self._user_id = user_id
        self._wallets: Dict[str, Wallet] = wallets or {}

    def add_currency(self, currency_code: str):
        currency_code = currency_code.upper()
        if currency_code not in self._wallets:
            self._wallets[currency_code] = Wallet(currency_code)

    def get_wallet(self, currency_code: str) -> Wallet:
        currency_code = currency_code.upper()
        return self._wallets.get(currency_code)

    def wallets(self):
        return dict(self._wallets)

    def get_total_value(self, exchange_rates: dict, base_currency='USD'):
        total = 0.0
        for code, wallet in self._wallets.items():
            rate = exchange_rates.get(f"{code}_{base_currency}", 1.0)
            total += wallet.balance * rate
        return total
