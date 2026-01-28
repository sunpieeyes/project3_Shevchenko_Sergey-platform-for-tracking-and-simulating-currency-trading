class Currency:
    """Базовый класс валюты."""
    
    def __init__(self, name, code):
        if not name or not isinstance(name, str):
            raise ValueError("Название валюты не может быть пустым")
        if not code or not isinstance(code, str):
            raise ValueError("Код валюты не может быть пустым")
        if len(code) < 2 or len(code) > 5:
            raise ValueError("Код валюты должен быть от 2 до 5 символов")
        
        self._name = name
        self._code = code.upper()
    
    @property
    def name(self):
        return self._name
    
    @property
    def code(self):
        return self._code
    
    def get_display_info(self):
        """Возвращает информацию для отображения."""
        return f"{self.code} - {self.name}"
    
    def __str__(self):
        return self.get_display_info()


class FiatCurrency(Currency):
    """Фиатная валюта (обычные деньги)."""
    
    def __init__(self, name, code, issuing_country):
        super().__init__(name, code)
        self._issuing_country = issuing_country
    
    @property
    def issuing_country(self):
        return self._issuing_country
    
    def get_display_info(self):
        base = super().get_display_info()
        return f"[FIAT] {base} (Страна: {self.issuing_country})"


class CryptoCurrency(Currency):
    """Криптовалюта."""
    
    def __init__(self, name, code, algorithm, market_cap=0.0):
        super().__init__(name, code)
        self._algorithm = algorithm
        self._market_cap = float(market_cap)
    
    @property
    def algorithm(self):
        return self._algorithm
    
    @property
    def market_cap(self):
        return self._market_cap
    
    def get_display_info(self):
        base = super().get_display_info()
        cap_str = f"{self.market_cap:.2e}" if self.market_cap > 1e6 else f"{self.market_cap:,.2f}"
        return f"[CRYPTO] {base} (Алгоритм: {self.algorithm}, Кап: {cap_str})"


# Реестр валют
_currency_registry = {}

def init_currency_registry():
    """Инициализирует реестр валют."""
    global _currency_registry
    
    # Фиатные валюты
    _currency_registry['USD'] = FiatCurrency("US Dollar", "USD", "United States")
    _currency_registry['EUR'] = FiatCurrency("Euro", "EUR", "Eurozone")
    _currency_registry['RUB'] = FiatCurrency("Russian Ruble", "RUB", "Russia")
    _currency_registry['GBP'] = FiatCurrency("British Pound", "GBP", "United Kingdom")
    
    # Криптовалюты
    _currency_registry['BTC'] = CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1_200_000_000_000)
    _currency_registry['ETH'] = CryptoCurrency("Ethereum", "ETH", "Ethash", 400_000_000_000)
    _currency_registry['SOL'] = CryptoCurrency("Solana", "SOL", "Proof of History", 60_000_000_000)


def get_currency(code):
    """Возвращает валюту по коду."""
    code = code.upper()
    
    if not _currency_registry:
        init_currency_registry()
    
    if code not in _currency_registry:
        from .exceptions import BadCurrencyError
        raise BadCurrencyError(code)
    
    return _currency_registry[code]


def list_currencies():
    """Возвращает список всех валют."""
    if not _currency_registry:
        init_currency_registry()
    
    return list(_currency_registry.values())


def is_currency_supported(code):
    """Проверяет, поддерживается ли валюта."""
    if not _currency_registry:
        init_currency_registry()
    
    return code.upper() in _currency_registry