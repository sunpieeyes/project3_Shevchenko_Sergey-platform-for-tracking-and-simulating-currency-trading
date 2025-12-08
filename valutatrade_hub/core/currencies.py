from abc import ABC, abstractmethod
from valutatrade_hub.core.exceptions import CurrencyNotFoundError

class Currency(ABC):
    def __init__(self, code: str, name: str):
        self.code = code.upper()
        self.name = name
        if not self.name or not self.code or not (2 <= len(self.code) <= 5):
            raise ValueError("Неверные параметры валюты")

    @abstractmethod
    def get_display_info(self) -> str:
        ...

class FiatCurrency(Currency):
    def __init__(self, code: str, name: str, issuing_country: str):
        super().__init__(code, name)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"

class CryptoCurrency(Currency):
    def __init__(self, code: str, name: str, algorithm: str, market_cap: float):
        super().__init__(code, name)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"

# Реестр валют
CURRENCY_REGISTRY = {
    "USD": FiatCurrency("USD", "US Dollar", "United States"),
    "EUR": FiatCurrency("EUR", "Euro", "Eurozone"),
    "BTC": CryptoCurrency("BTC", "Bitcoin", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("ETH", "Ethereum", "Ethash", 4.5e11),
}

def get_currency(code: str) -> Currency:
    code = code.upper()
    if code not in CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(f"Неизвестная валюта '{code}'")
    return CURRENCY_REGISTRY[code]
