import os
import json
from .models import User, Portfolio
from .exceptions import *
from .utils import hash_password, get_next_id, get_current_time
from .session import session
from ..infra.database import Database
from datetime import datetime, timezone


class AppLogic:
    """Основная логика приложения."""
    
    def __init__(self):
        self.db = Database()
        self._load_session()
    
    def _save_session(self):
        """Сохраняет сессию в файл."""
        if session.is_logged_in():
            session_file = "data/session.json"
            session_data = {
                'user_id': session.current_user.user_id,
                'username': session.current_user.username
            }
            os.makedirs(os.path.dirname(session_file), exist_ok=True)
            with open(session_file, 'w') as f:
                json.dump(session_data, f)
    
    def _load_session(self):
        """Загружает сессию из файла."""
        session_file = "data/session.json"
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                user_data = self.db.find_user(session_data['username'])
                if user_data:
                    user = User.from_dict(user_data)
                    session.login(user)
            except Exception:
                pass
    
    def _clear_session(self):
        """Очищает файл сессии."""
        session_file = "data/session.json"
        if os.path.exists(session_file):
            os.remove(session_file)
    
    
    def register(self, username, password):
        """Регистрирует нового пользователя."""
        if not username:
            raise ValueError("Нужно указать имя")
        if len(password) < 4:
            raise ValueError("Пароль должен быть от 4 символов")
        
        if self.db.find_user(username):
            raise ValueError(f"Имя '{username}' уже занято")
        
        users = self.db.get_all_users()
        new_id = get_next_id(users)
        
        hashed_pass, salt = hash_password(password)
        reg_date = get_current_time()
        
        user_data = {
            'user_id': new_id,
            'username': username,
            'hashed_password': hashed_pass,
            'salt': salt,
            'registration_date': reg_date
        }
        
        self.db.add_user(user_data)
        
        portfolio_data = {
            'user_id': new_id,
            'wallets': {}
        }
        self.db.save_portfolio(portfolio_data)
        
        user = User.from_dict(user_data)
        
        session.login(user)
        self._save_session()
        
        return user
    
    def login(self, username, password):
        """Вход в систему."""
        user_data = self.db.find_user(username)
        if not user_data:
            raise UserNotFoundError(f"Пользователь '{username}' не найден")
        
        user = User.from_dict(user_data)
        
        if not user.check_password(password):
            raise WrongPasswordError("Неправильный пароль")
        
        session.login(user)
        self._save_session()
        return user
    
    def logout(self):
        """Выход."""
        session.logout()
        self._clear_session()
    
    def get_current_user(self):
        """Получает текущего пользователя."""
        if not session.is_logged_in():
            raise NotLoggedInError("Вы не вошли в систему")
        return session.current_user
    
    
    def get_portfolio(self, user_id=None):
        """Получает портфель."""
        if user_id is None:
            user_id = session.get_user_id()
        
        portfolio_data = self.db.get_portfolio(user_id)
        if not portfolio_data:
            portfolio_data = {'user_id': user_id, 'wallets': {}}
            self.db.save_portfolio(portfolio_data)
        
        return Portfolio.from_dict(portfolio_data)
    
    def show_my_portfolio(self, base='USD'):
        """Показывает портфель текущего пользователя."""
        if not session.is_logged_in():
            raise NotLoggedInError("Вы не вошли в систему")
        
        user = session.current_user
        portfolio = self.get_portfolio(user.user_id)
        
        result = {
            'user': user.username,
            'base': base,
            'wallets': [],
            'total': 0.0
        }
        
        total = 0.0
        
        rates = {
            'USD': 1.0,
            'EUR': 1.08,
            'BTC': 50000.0,
            'ETH': 3000.0,
            'RUB': 0.011
        }
        
        for currency, wallet in portfolio.wallets.items():
            wallet_info = wallet.get_info()
            
            if currency == base:
                value = wallet.balance
            else:
                rate = rates.get(currency, 1.0)
                value = wallet.balance * rate
            
            wallet_info['value'] = value
            result['wallets'].append(wallet_info)
            total += value
        
        result['total'] = total
        return result
    
    
    def buy(self, currency, amount):
        """Покупает валюту."""
        # Проверяем вход
        if not session.is_logged_in():
            raise NotLoggedInError("Вы не вошли в систему")
        
        if amount <= 0:
            raise BadAmountError(f"Сумма должна быть > 0: {amount}")
        
        currency = currency.upper()
        user_id = session.get_user_id()
        portfolio = self.get_portfolio(user_id)
        
        # Получаем или создаем кошелек
        wallet = portfolio.get_wallet(currency)
        if not wallet:
            wallet = portfolio.add_wallet(currency)
        
        # Нужен USD кошелек для оплаты
        usd_wallet = portfolio.get_wallet('USD')
        if not usd_wallet:
            raise NotEnoughMoneyError(0, 1, 'USD')
        
        # Простой курс для расчета
        rates = {
            'BTC': 50000.0,
            'ETH': 3000.0,
            'EUR': 1.08,
            'RUB': 0.011
        }
        rate = rates.get(currency, 1.0)
        cost = amount * rate
        
        # Проверяем хватает ли USD
        if usd_wallet.balance < cost:
            raise NotEnoughMoneyError(usd_wallet.balance, cost, 'USD')
        
        # Выполняем
        usd_wallet.take_money(cost)
        wallet.add_money(amount)
        
        # Сохраняем
        self.db.save_portfolio(portfolio.to_dict())
        
        return {
            'success': True,
            'currency': currency,
            'amount': amount,
            'cost': cost,
            'new_balance': wallet.balance,
            'usd_left': usd_wallet.balance
        }
    
    def sell(self, currency, amount):
        """Продает валюту."""
        # Проверяем вход
        if not session.is_logged_in():
            raise NotLoggedInError("Вы не вошли в систему")
        
        if amount <= 0:
            raise BadAmountError(f"Сумма должна быть > 0: {amount}")
        
        currency = currency.upper()
        user_id = session.get_user_id()
        portfolio = self.get_portfolio(user_id)
        
        # Проверяем кошелек
        wallet = portfolio.get_wallet(currency)
        if not wallet:
            raise NotEnoughMoneyError(0, amount, currency)
        
        # Проверяем хватает ли валюты
        if wallet.balance < amount:
            raise NotEnoughMoneyError(wallet.balance, amount, currency)
        
        # USD кошелек для получения денег
        usd_wallet = portfolio.get_wallet('USD')
        if not usd_wallet:
            usd_wallet = portfolio.add_wallet('USD')
        
        # Простой курс для расчета
        rates = {
            'BTC': 50000.0,
            'ETH': 3000.0,
            'EUR': 1.08,
            'RUB': 0.011
        }
        rate = rates.get(currency, 1.0)
        revenue = amount * rate
        
        # Выполняем
        wallet.take_money(amount)
        usd_wallet.add_money(revenue)
        
        # Сохраняем
        self.db.save_portfolio(portfolio.to_dict())
        
        return {
            'success': True,
            'currency': currency,
            'amount': amount,
            'revenue': revenue,
            'new_balance': wallet.balance,
            'usd_now': usd_wallet.balance
        }
    
    def get_rate(self, from_curr, to_curr):
        """Получает курс (с учётом кэша rates.json и TTL)."""
        from_curr = str(from_curr).upper()
        to_curr = str(to_curr).upper()

        # простая валидация кода (2–5, верхний регистр)
        for code in (from_curr, to_curr):
            if not code.isalpha() or not (2 <= len(code) <= 5) or code != code.upper():
                raise CurrencyNotFoundError(code)

        if from_curr == to_curr:
            return 1.0

        ttl = self.db.settings.get_rates_ttl()

        def _parse_iso(s: str) -> datetime:
            s = s.replace("Z", "+00:00")
            return datetime.fromisoformat(s)

        rates_data = self.db.get_rates()
        pairs = {}
        if isinstance(rates_data, dict):
            pairs = rates_data.get("pairs") or {}

        pair = f"{from_curr}_{to_curr}"
        if pair in pairs:
            meta = pairs[pair]
            rate = float(meta["rate"])
            updated_at = meta.get("updated_at")
            if updated_at:
                age = (datetime.now(timezone.utc) - _parse_iso(updated_at).astimezone(timezone.utc)).total_seconds()
                if age > ttl:
                    raise ApiRequestError(f"кэш для {pair} устарел (старше {ttl} сек). Выполните update-rates")
            return rate

        inv_pair = f"{to_curr}_{from_curr}"
        if inv_pair in pairs:
            meta = pairs[inv_pair]
            inv_rate = float(meta["rate"])
            updated_at = meta.get("updated_at")
            if updated_at:
                age = (datetime.now(timezone.utc) - _parse_iso(updated_at).astimezone(timezone.utc)).total_seconds()
                if age > ttl:
                    raise ApiRequestError(f"кэш для {inv_pair} устарел (старше {ttl} сек). Выполните update-rates")
            if inv_rate == 0:
                raise ApiRequestError(f"некорректный курс в кеше для {inv_pair}")
            return 1.0 / inv_rate

        fixed = {
            "EUR_USD": 1.08,
            "BTC_USD": 50000.0,
            "ETH_USD": 3000.0,
            "RUB_USD": 0.011,
        }
        if to_curr == "USD" and f"{from_curr}_USD" in fixed:
            return fixed[f"{from_curr}_USD"]
        if from_curr == "USD" and f"{to_curr}_USD" in fixed:
            return 1.0 / fixed[f"{to_curr}_USD"]

        raise ApiRequestError(f"курс {from_curr}→{to_curr} недоступен")
    
    def add_money(self, currency, amount):
        """Добавляет деньги на счет (для теста)."""
        if not session.is_logged_in():
            raise NotLoggedInError("Вы не вошли в систему")
        
        if amount <= 0:
            raise BadAmountError("Сумма должна быть положительной")
        
        currency = currency.upper()
        user_id = session.get_user_id()
        portfolio = self.get_portfolio(user_id)
        
        wallet = portfolio.get_wallet(currency)
        if not wallet:
            wallet = portfolio.add_wallet(currency)
        
        old = wallet.balance
        wallet.add_money(amount)
        
        self.db.save_portfolio(portfolio.to_dict())
        
        return {
            'currency': currency,
            'added': amount,
            'was': old,
            'now': wallet.balance
        }