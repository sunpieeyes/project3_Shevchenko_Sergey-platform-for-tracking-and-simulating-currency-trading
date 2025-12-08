from valutatrade_hub.core.currencies import get_currency, Currency
from valutatrade_hub.core.exceptions import CurrencyNotFoundError

def validate_currency_code(code: str) -> Currency:
    try:
        return get_currency(code)
    except CurrencyNotFoundError as e:
        raise e

def convert_amount(amount: float, rate: float) -> float:
    return amount * rate
