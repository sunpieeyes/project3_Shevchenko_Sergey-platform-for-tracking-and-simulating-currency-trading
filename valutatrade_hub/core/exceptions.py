class MyError(Exception):
    """Базовая ошибка приложения."""


class CurrencyNotFoundError(MyError):
    """Неизвестная валюта."""
    def __init__(self, code: str):
        super().__init__(f"Неизвестная валюта '{code}'")


class ApiRequestError(MyError):
    """Сбой внешнего API / недоступен источник курсов."""
    def __init__(self, reason: str):
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")


class InsufficientFundsError(MyError):
    """Недостаточно средств."""
    def __init__(self, available: float, required: float, code: str):
        super().__init__(
            f"Недостаточно средств: доступно {available} {code}, требуется {required} {code}"
        )


class NotEnoughMoneyError(InsufficientFundsError):
    """Старое имя ошибки (алиас)."""
    def __init__(self, have, need, currency):
        super().__init__(available=have, required=need, code=currency)


class BadCurrencyError(CurrencyNotFoundError):
    """Старое имя ошибки (алиас)."""
    def __init__(self, code: str):
        super().__init__(code)


class UserNotFoundError(MyError):
    def __init__(self, username: str):
        super().__init__(f"Пользователь '{username}' не найден")


class WrongPasswordError(MyError):
    def __init__(self):
        super().__init__("Неверный пароль")


class NotLoggedInError(MyError):
    def __init__(self, msg: str = "Сначала выполните login"):
        super().__init__(msg)


class BadAmountError(MyError):
    def __init__(self, msg: str = "'amount' должен быть положительным числом"):
        super().__init__(msg)
