class UserExistsError(Exception):
    """Пользователь уже существует."""
    pass


class UserNotFoundError(Exception):
    """Пользователь не найден."""
    pass


class AuthenticationError(Exception):
    """Ошибка аутентификации."""
    pass


class InsufficientFundsError(Exception):
    """Недостаточно средств на кошельке."""
    def __init__(self, code: str, available: float, required: float):
        self.code = code
        self.available = available
        self.required = required
        message = (
            f"Недостаточно средств: доступно {available} {code}, "
            f"требуется {required} {code}"
        )
        super().__init__(message)


class CurrencyNotSupportedError(Exception):
    """Операция недоступна для данной валюты."""
    pass


class RateNotAvailableError(Exception):
    """Курс валюты временно недоступен."""
    pass


class CurrencyNotFoundError(Exception):
    """Валюта не найдена."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Неизвестная валюта '{code}'")


class ApiRequestError(Exception):
    """Ошибка при обращении к внешнему API."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
