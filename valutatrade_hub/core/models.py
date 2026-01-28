class User:
    """Пользователь системы."""
    
    def __init__(self, user_id, username, hashed_password, salt, reg_date=None):
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._reg_date = reg_date
    
    @property
    def user_id(self):
        return self._user_id
    
    @property
    def username(self):
        return self._username
    
    @username.setter
    def username(self, value):
        if not value:
            raise ValueError("Имя не может быть пустым")
        self._username = value
    
    @property
    def password_hash(self):
        return self._hashed_password
    
    @property
    def salt(self):
        return self._salt
    
    def get_info(self):
        """Возвращает информацию о пользователе."""
        return {
            'id': self.user_id,
            'name': self.username,
            'registered': self._reg_date
        }
    
    def change_password(self, new_password):
        """Меняет пароль."""
        if len(new_password) < 4:
            raise ValueError("Пароль слишком короткий")
        
        from .utils import hash_password
        self._hashed_password, self._salt = hash_password(new_password)
    
    def check_password(self, password):
        """Проверяет пароль."""
        from .utils import verify_password
        return verify_password(password, self.password_hash, self.salt)
    
    def to_dict(self):
        """Преобразует в словарь для сохранения."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'hashed_password': self.password_hash,
            'salt': self.salt,
            'registration_date': self._reg_date
        }
    
    @classmethod
    def from_dict(cls, data):
        """Создает из словаря."""
        return cls(
            data['user_id'],
            data['username'],
            data['hashed_password'],
            data['salt'],
            data.get('registration_date')
        )


class Wallet:
    """Кошелек для одной валюты."""
    
    def __init__(self, currency, balance=0.0):
        self.currency = currency.upper()
        self._balance = float(balance)
    
    @property
    def balance(self):
        return self._balance
    
    @balance.setter
    def balance(self, value):
        value = float(value)
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = value
    
    def add_money(self, amount):
        """Добавляет деньги."""
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        self.balance += float(amount)
    
    def take_money(self, amount):
        """Снимает деньги."""
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        if amount > self.balance:
            from .exceptions import InsufficientFundsError
            raise InsufficientFundsError(self.balance, amount, self.currency)
        self.balance -= float(amount)
    
    def get_info(self):
        """Информация о кошельке."""
        return {
            'currency': self.currency,
            'balance': self.balance
        }
    
    def to_dict(self):
        """Для сохранения в JSON."""
        return {
            'currency_code': self.currency,
            'balance': self.balance
        }
    
    @classmethod
    def from_dict(cls, data):
        """Создает из словаря."""
        return cls(data['currency_code'], data['balance'])


class Portfolio:
    """Портфель пользователя."""
    
    def __init__(self, user_id, wallets=None):
        self.user_id = user_id
        self.wallets = wallets or {} 
    
    def add_wallet(self, currency):
        """Добавляет новый кошелек."""
        currency = currency.upper()
        if currency not in self.wallets:
            self.wallets[currency] = Wallet(currency)
        return self.wallets[currency]
    
    def get_wallet(self, currency):
        """Получает кошелек."""
        currency = currency.upper()
        return self.wallets.get(currency)
    
    def get_total_value(self, base='USD'):
        """Считает общую стоимость."""
        rates = {
            'USD': 1.0,
            'EUR': 1.08,
            'BTC': 50000.0,
            'ETH': 3000.0,
            'RUB': 0.011
        }
        
        total = 0.0
        
        for currency, wallet in self.wallets.items():
            if currency == base:
                total += wallet.balance
            else:
                rate_to_usd = rates.get(currency, 1.0)
                rate_usd_to_base = 1.0 / rates.get(base, 1.0)
                total += wallet.balance * rate_to_usd * rate_usd_to_base
        
        return total
    
    def to_dict(self):
        """Для сохранения."""
        return {
            'user_id': self.user_id,
            'wallets': {
                code: wallet.to_dict()
                for code, wallet in self.wallets.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data):
        """Создает из словаря."""
        wallets = {}
        for code, wallet_data in data.get('wallets', {}).items():
            wallets[code] = Wallet.from_dict(wallet_data)
        return cls(data['user_id'], wallets)