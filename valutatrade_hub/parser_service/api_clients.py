from __future__ import annotations

import json
import urllib.request
import urllib.parse
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from ..core.exceptions import ApiRequestError
from .config import ParserConfig


class BaseApiClient(ABC):
    @abstractmethod
    def fetch_rates(self) -> dict[str, dict]:
        """
        Возвращает словарь пар вида:
        {
          "BTC_USD": {"rate": 59337.21, "updated_at": "...Z", "source": "..."},
          ...
        }
        """
        raise NotImplementedError


def _http_get_json(url: str, timeout: int) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            if resp.status != 200:
                raise ApiRequestError(f"HTTP {resp.status}")
            data = resp.read().decode("utf-8")
            return json.loads(data)
    except ApiRequestError:
        raise
    except Exception as e:
        raise ApiRequestError(str(e)) from e


class CoinGeckoClient(BaseApiClient):
    def __init__(self, cfg: ParserConfig) -> None:
        self.cfg = cfg

    def fetch_rates(self) -> dict[str, dict]:
        ids = [self.cfg.CRYPTO_ID_MAP[c] for c in self.cfg.CRYPTO_CURRENCIES if c in self.cfg.CRYPTO_ID_MAP]
        if not ids:
            return {}

        qs = urllib.parse.urlencode({"ids": ",".join(ids), "vs_currencies": self.cfg.BASE_CURRENCY.lower()})
        url = f"{self.cfg.COINGECKO_URL}?{qs}"

        payload = _http_get_json(url, self.cfg.REQUEST_TIMEOUT)

        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        out: dict[str, dict] = {}
        for code, cg_id in self.cfg.CRYPTO_ID_MAP.items():
            if cg_id in payload and self.cfg.BASE_CURRENCY.lower() in payload[cg_id]:
                rate = float(payload[cg_id][self.cfg.BASE_CURRENCY.lower()])
                out[f"{code}_{self.cfg.BASE_CURRENCY}"] = {"rate": rate, "updated_at": now, "source": "CoinGecko"}
        return out


class ExchangeRateApiClient(BaseApiClient):
    def __init__(self, cfg: ParserConfig) -> None:
        self.cfg = cfg

    def fetch_rates(self) -> dict[str, dict]:
        if not self.cfg.EXCHANGERATE_API_KEY:
            raise ApiRequestError("EXCHANGERATE_API_KEY не задан")

        url = f"{self.cfg.EXCHANGERATE_API_URL}/{self.cfg.EXCHANGERATE_API_KEY}/latest/{self.cfg.BASE_CURRENCY}"
        payload = _http_get_json(url, self.cfg.REQUEST_TIMEOUT)

        if payload.get("result") != "success":
            raise ApiRequestError(payload.get("error-type", "unknown error"))

        rates = payload.get("conversion_rates") or payload.get("rates") or {}
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        out: dict[str, dict] = {}
        for code in self.cfg.FIAT_CURRENCIES:
            if code in rates:
                # Тут rate = сколько CODE за 1 USD (если base USD).
                # Нам нужен CODE_USD (1 CODE = ? USD), то есть обратное значение.
                raw = float(rates[code])
                if raw == 0:
                    continue
                out[f"{code}_{self.cfg.BASE_CURRENCY}"] = {"rate": 1.0 / raw, "updated_at": now, "source": "ExchangeRate-API"}
        return out
