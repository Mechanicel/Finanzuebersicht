from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.models import UpstreamServiceError


class FMPClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None,
        timeout_seconds: float,
        retries: int,
        backoff_factor: float,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key.strip() if api_key else None
        self.timeout_seconds = timeout_seconds
        retry = Retry(
            total=max(0, retries),
            backoff_factor=max(0.0, backoff_factor),
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session = requests.Session()
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def search_name(self, *, query: str, limit: int) -> list[dict[str, Any]]:
        return self._get_json("/search-name", {"query": query, "limit": limit})

    def profile(self, *, symbol: str) -> list[dict[str, Any]]:
        return self._get_json("/profile", {"symbol": symbol})

    def _get_json(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        req_params = dict(params)
        if self.api_key:
            req_params["apikey"] = self.api_key
        try:
            response = self._session.get(
                f"{self.base_url}{path}",
                params=req_params,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            raise UpstreamServiceError(
                f"Market data provider request failed with status {status_code or 'unknown'}"
            ) from exc
        except requests.RequestException as exc:
            raise UpstreamServiceError() from exc
        except ValueError as exc:
            raise UpstreamServiceError("Invalid response from market data provider") from exc

        if not isinstance(payload, list):
            raise UpstreamServiceError("Invalid response payload from market data provider")
        return [item for item in payload if isinstance(item, dict)]
