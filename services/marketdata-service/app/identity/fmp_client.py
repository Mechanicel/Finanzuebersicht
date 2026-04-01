from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import requests


class FmpClient:
    """Defensive HTTP client for FMP symbol search used in identifier resolution."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None,
        timeout_seconds: float,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key.strip() if api_key else None
        self._timeout_seconds = timeout_seconds
        self._session = requests.Session()

    def search_instrument(
        self,
        *,
        symbol: str,
        exchange: str | None = None,
        company_name: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str | int] = {
            "query": symbol,
            "limit": 10,
        }
        if self._api_key:
            params["apikey"] = self._api_key
        if exchange and exchange.strip():
            params["exchange"] = exchange.strip()

        self._logger.debug(
            "fmp search request",
            extra={"symbol": symbol, "exchange": exchange, "company_name": company_name},
        )

        try:
            response = self._session.get(
                f"{self._base_url}/search-ticker",
                params=params,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException:
            self._logger.debug("fmp request failed", exc_info=True)
            return []

        try:
            parsed = response.json()
        except ValueError:
            self._logger.debug("fmp returned non-json response")
            return []

        if not isinstance(parsed, list):
            return []

        items: list[dict[str, Any]] = []
        for item in parsed:
            if isinstance(item, Mapping):
                items.append(dict(item))
        return items
