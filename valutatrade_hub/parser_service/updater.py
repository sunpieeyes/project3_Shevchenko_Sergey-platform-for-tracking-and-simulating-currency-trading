from __future__ import annotations

import logging

from ..core.exceptions import ApiRequestError
from .api_clients import BaseApiClient
from .storage import RatesStorage


class RatesUpdater:
    def __init__(self, clients: list[BaseApiClient], storage: RatesStorage) -> None:
        self.clients = clients
        self.storage = storage
        self.logger = logging.getLogger(__name__)

    def run_update(self) -> dict[str, dict]:
        merged: dict[str, dict] = {}

        for client in self.clients:
            name = client.__class__.__name__
            try:
                self.logger.info("Fetching rates from %s ...", name)
                got = client.fetch_rates()
                self.logger.info("OK %s: %d rates", name, len(got))
                merged.update(got)
            except ApiRequestError as e:
                self.logger.error("Failed %s: %s", name, e)

        if not merged:
            raise ApiRequestError("не удалось обновить курсы: все источники недоступны")

        self.storage.write_rates_snapshot(merged)
        self.storage.append_history(merged)
        return merged
