from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import requests


class OpenFigiClient:
    """Small defensive HTTP client for OpenFIGI mapping requests."""

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

    def map_instrument(
        self,
        *,
        symbol: str,
        exchange_code: str | None = None,
        company_name: str | None = None,
    ) -> list[dict[str, Any]]:
        payload = {
            "idType": "TICKER",
            "idValue": symbol,
        }
        if exchange_code and exchange_code.strip():
            payload["exchCode"] = exchange_code.strip()
        if company_name and company_name.strip():
            payload["securityDescription"] = company_name.strip()

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self._api_key:
            headers["X-OPENFIGI-APIKEY"] = self._api_key

        try:
            response = self._session.post(
                f"{self._base_url}/mapping",
                headers=headers,
                json=[payload],
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException:
            self._logger.debug("openfigi request failed", exc_info=True)
            return []

        try:
            parsed = response.json()
        except ValueError:
            self._logger.debug("openfigi returned non-json response")
            return []

        if not isinstance(parsed, list) or not parsed:
            return []

        first = parsed[0]
        if not isinstance(first, Mapping):
            return []

        data = first.get("data")
        if not isinstance(data, list):
            return []

        valid_items: list[dict[str, Any]] = []
        for item in data:
            if isinstance(item, Mapping):
                valid_items.append(dict(item))
        return valid_items
