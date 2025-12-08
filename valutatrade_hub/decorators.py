from functools import wraps
from valutatrade_hub.logging_config import logger

def log_action(action_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = kwargs.get("user_id", None)
            currency_code = kwargs.get("currency_code", None)
            amount = kwargs.get("amount", None)
            try:
                result = func(*args, **kwargs)
                logger.info(f"{action_name} user_id={user_id} currency={currency_code} amount={amount} result=OK")
                return result
            except Exception as e:
                logger.info(f"{action_name} user_id={user_id} currency={currency_code} amount={amount} result=ERROR error={type(e).__name__} message={e}")
                raise
        return wrapper
    return decorator
