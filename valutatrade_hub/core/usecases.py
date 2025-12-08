"""
Business usecases: register, login, logout, show_portfolio, buy, sell, get_rate.

Работает с JSON-хранилищем в data/, использует SettingsLoader для путей/TTL,
логирует операции через @log_action, бросает доменные исключения из core.exceptions.
"""

from __future__ import annotations
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from valutatrade_hub.infra.storage import read_json, write_json_atomic
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.decorators import log_action

# Импортируем исключения — предполагается, что core/exceptions содержит эти классы.
# Если у тебя имена отличаются — сообщи, поправим.
from valutatrade_hub.core.exceptions import (
    UserExistsError,
    AuthenticationError,
    InsufficientFundsError,
    CurrencyNotFoundError,
    ApiRequestError,
)

# Настройки (singleton)
_SETTINGS = SettingsLoader()
DATA_PATH = _SETTINGS.get("data_path", "data")
# Пути к файлам — составляем из data_path
USERS_FILE = _SETTINGS.get("users_file", f"{DATA_PATH.rstrip('/')}/users.json")
PORTFOLIOS_FILE = _SETTINGS.get("portfolios_file", f"{DATA_PATH.rstrip('/')}/portfolios.json")
RATES_FILE = _SETTINGS.get("rates_file", f"{DATA_PATH.rstrip('/')}/rates.json")
SESSION_FILE = _SETTINGS.get("session_file", f"{DATA_PATH.rstrip('/')}/session.json")

RATES_TTL = int(_SETTINGS.get("RATES_TTL_SECONDS", 300))
DEFAULT_BASE = _SETTINGS.get("default_base_currency", "USD")


# -------------------------
# Helpers: read/write simple JSON-backed stores
# -------------------------
def _load_users() -> list[Dict[str, Any]]:
    data = read_json(USERS_FILE)
    return data if isinstance(data, list) else []


def _save_users(users: list[Dict[str, Any]]) -> None:
    write_json_atomic(USERS_FILE, users)


def _load_portfolios() -> list[Dict[str, Any]]:
    data = read_json(PORTFOLIOS_FILE)
    return data if isinstance(data, list) else []


def _save_portfolios(portfolios: list[Dict[str, Any]]) -> None:
    write_json_atomic(PORTFOLIOS_FILE, portfolios)


def _load_rates_raw() -> Dict[str, Any]:
    data = read_json(RATES_FILE)
    return data if isinstance(data, dict) else {}


def _get_rates_and_refresh_time() -> tuple[Dict[str, float], Optional[datetime]]:
    """
    Возвращает (rates_map, last_refresh_dt)
    Поддерживает формат:
      - {"USD":1.0,"EUR":1.12,...,"last_refresh":"2025-10-01T12:00:00"}
      - или {"EUR_USD": {"rate":1.0786, "updated_at":"..."}, ...} (частично)
    """
    raw = _load_rates_raw()
    if not raw:
        return {}, None

    # parse last refresh if available
    last_refresh = raw.get("last_refresh") or raw.get("updated_at")
    if last_refresh:
        try:
            last_refresh_dt = datetime.fromisoformat(last_refresh)
        except Exception:
            last_refresh_dt = None
    else:
        last_refresh_dt = None

    rates: Dict[str, float] = {}
    for k, v in raw.items():
        if k in ("last_refresh", "updated_at", "source"):
            continue
        # simple format: "USD": 1.0
        if isinstance(v, (int, float)):
            rates[k.upper()] = float(v)
        # nested dict: {"BTC": {"rate": 30000, ...}}
        elif isinstance(v, dict) and "rate" in v and "_" not in k:
            try:
                rates[k.upper()] = float(v["rate"])
            except Exception:
                continue
        # ignore other complex forms for now

    if "USD" not in rates:
        rates["USD"] = 1.0

    return rates, last_refresh_dt


def _load_session() -> dict:
    data = read_json(SESSION_FILE)
    return data if isinstance(data, dict) else {}


def _save_session(sess: dict) -> None:
    write_json_atomic(SESSION_FILE, sess)


def _hash_pw(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


# -------------------------
# User flows
# -------------------------
def _next_user_id(users: list[Dict[str, Any]]) -> int:
    if not users:
        return 1
    ids = [u.get("user_id", 0) for u in users if isinstance(u, dict)]
    return max(ids, default=0) + 1


@log_action("REGISTER")
def register(username: str, password: str) -> Dict[str, Any]:
    users = _load_users()
    if any(u.get("username") == username for u in users):
        raise UserExistsError(f"Username '{username}' already taken")
    uid = _next_user_id(users)
    salt = secrets.token_hex(8)
    hashed = _hash_pw(password, salt)
    reg_date = datetime.utcnow().isoformat()
    user_obj = {
        "user_id": uid,
        "username": username,
        "hashed_password": hashed,
        "salt": salt,
        "registration_date": reg_date,
    }
    users.append(user_obj)
    _save_users(users)

    # create empty portfolio
    portfolios = _load_portfolios()
    portfolios.append({"user_id": uid, "wallets": {}})
    _save_portfolios(portfolios)

    return {"user_id": uid, "username": username}


@log_action("LOGIN")
def login(username: str, password: str) -> Dict[str, Any]:
    users = _load_users()
    user = next((u for u in users if u.get("username") == username), None)
    if not user:
        raise AuthenticationError(f"User '{username}' not found")
    salt = user.get("salt")
    if _hash_pw(password, salt) != user.get("hashed_password"):
        raise AuthenticationError("Invalid password")
    sess = {"username": username, "user_id": user["user_id"], "logged_at": datetime.utcnow().isoformat()}
    _save_session(sess)
    return {"user_id": user["user_id"], "username": username}


def logout() -> None:
    _save_session({})


def current_session() -> dict:
    return _load_session()


# -------------------------
# Core operations: show, buy, sell, get_rate
# -------------------------
def _find_portfolio_entry(portfolios: list[Dict[str, Any]], user_id: int) -> Optional[Dict[str, Any]]:
    return next((p for p in portfolios if int(p.get("user_id")) == int(user_id)), None)


def _ensure_logged_in() -> dict:
    sess = _load_session()
    if not sess or "user_id" not in sess:
        raise AuthenticationError("Please login first")
    return sess


def show_portfolio(base: str = DEFAULT_BASE) -> Dict[str, Any]:
    sess = _ensure_logged_in()
    uid = int(sess["user_id"])
    portfolios = _load_portfolios()
    p = _find_portfolio_entry(portfolios, uid)
    if not p or not p.get("wallets"):
        return {"user": sess["username"], "base": base, "wallets": {}, "total": 0.0}

    rates, last_refresh = _get_rates_and_refresh_time()
    base = base.upper()
    if base not in rates:
        raise CurrencyNotFoundError(base)

    wallets = p.get("wallets", {})
    detailed = {}
    total_in_base = 0.0
    for cur_code, info in wallets.items():
        cur = cur_code.upper()
        bal = float(info.get("balance", 0.0))
        if cur not in rates:
            value_in_base = 0.0
        else:
            value_in_base = bal * (rates[cur] / rates[base])
        detailed[cur] = {"balance": bal, "value_in_base": round(value_in_base, 8)}
        total_in_base += value_in_base

    return {"user": sess["username"], "base": base, "wallets": detailed, "total": round(total_in_base, 8), "rates_last_refresh": (last_refresh.isoformat() if last_refresh else None)}


@log_action("BUY")
def buy(currency_code: str, amount: float) -> Dict[str, Any]:
    sess = _ensure_logged_in()
    uid = int(sess["user_id"])
    if amount <= 0:
        raise ValueError("'amount' must be positive")

    # validate currency via factory
    try:
        get_currency(currency_code)
    except CurrencyNotFoundError:
        raise

    portfolios = _load_portfolios()
    p = _find_portfolio_entry(portfolios, uid)
    if p is None:
        p = {"user_id": uid, "wallets": {}}
        portfolios.append(p)

    wallets = p.setdefault("wallets", {})
    cur = currency_code.upper()
    w = wallets.get(cur)
    if not w:
        wallets[cur] = {"currency_code": cur, "balance": float(amount)}
    else:
        wallets[cur]["balance"] = float(wallets[cur].get("balance", 0.0)) + float(amount)

    _save_portfolios(portfolios)

    # estimate cost in USD if rate available
    rates, last_refresh = _get_rates_and_refresh_time()
    est_usd = None
    if cur in rates:
        est_usd = float(amount) * float(rates[cur])

    return {"user_id": uid, "currency": cur, "amount": float(amount), "estimated_cost_usd": est_usd, "rates_last_refresh": (last_refresh.isoformat() if last_refresh else None)}


@log_action("SELL")
def sell(currency_code: str, amount: float) -> Dict[str, Any]:
    sess = _ensure_logged_in()
    uid = int(sess["user_id"])
    if amount <= 0:
        raise ValueError("'amount' must be positive")
    try:
        get_currency(currency_code)
    except CurrencyNotFoundError:
        raise

    portfolios = _load_portfolios()
    p = _find_portfolio_entry(portfolios, uid)
    if p is None or "wallets" not in p or currency_code.upper() not in p["wallets"]:
        raise InsufficientFundsError(available=0.0, required=amount, code=currency_code.upper())

    cur = currency_code.upper()
    bal = float(p["wallets"][cur].get("balance", 0.0))
    if amount > bal:
        raise InsufficientFundsError(available=bal, required=amount, code=cur)

    p["wallets"][cur]["balance"] = bal - float(amount)
    _save_portfolios(portfolios)

    # estimate revenue in USD if rate available
    rates, last_refresh = _get_rates_and_refresh_time()
    revenue_usd = None
    if cur in rates:
        revenue_usd = float(amount) * float(rates[cur])

    return {"user_id": uid, "currency": cur, "amount": float(amount), "estimated_revenue_usd": revenue_usd, "rates_last_refresh": (last_refresh.isoformat() if last_refresh else None)}


def get_rate(from_code: str, to_code: str) -> Dict[str, Any]:
    # validate currency codes via factory
    try:
        get_currency(from_code)
        get_currency(to_code)
    except CurrencyNotFoundError:
        raise

    rates, last_refresh = _get_rates_and_refresh_time()
    if not rates:
        raise ApiRequestError("Rates cache empty or unavailable")

    # TTL check
    if last_refresh is None:
        raise ApiRequestError("Rates cache missing timestamp; update required")
    now = datetime.utcnow()
    if (now - last_refresh) > timedelta(seconds=RATES_TTL):
        raise ApiRequestError("Rates cache is stale; Parser Service update required")

    f = from_code.upper()
    t = to_code.upper()
    if f not in rates or t not in rates:
        raise CurrencyNotFoundError(f"{f} or {t} not present in rates")

    # rate f->t = rates[t] / rates[f] assuming rates[*] are USD-based
    rate = float(rates[t]) / float(rates[f])
    return {"from": f, "to": t, "rate": rate, "rates_last_refresh": last_refresh.isoformat()}
