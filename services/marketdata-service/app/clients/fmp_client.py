from __future__ import annotations

import logging
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.models import UpstreamServiceError

LOGGER = logging.getLogger(__name__)


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
        # pool_maxsize raised to 30 to handle concurrent per-holding profile fetches
        # without "Connection pool is full" warnings on large portfolios.
        adapter = HTTPAdapter(max_retries=retry, pool_connections=1, pool_maxsize=30)
        self._session = requests.Session()
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def search_name(self, *, query: str, limit: int) -> list[dict[str, Any]]:
        started_at = time.perf_counter()
        LOGGER.info('search_trace fmp_client_search_name_enter query="%s" limit=%s', query, limit)
        try:
            LOGGER.info('search_trace fmp_client_search_name_before_get_json path="/search-name" query="%s" limit=%s', query, limit)
            payload = self._get_json("/search-name", {"query": query, "limit": limit})
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            LOGGER.info(
                'search_trace fmp_client_search_name_exit success=true query="%s" limit=%s duration_ms=%s row_count=%s',
                query,
                limit,
                duration_ms,
                len(payload),
            )
            return payload
        except Exception:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            LOGGER.exception(
                'search_trace fmp_client_search_name_exit success=false query="%s" limit=%s duration_ms=%s',
                query,
                limit,
                duration_ms,
            )
            raise

    def profile(self, *, symbol: str) -> list[dict[str, Any]]:
        return self._get_json("/profile", {"symbol": symbol})

    def balance_sheet_statement(self, *, symbol: str, period: str) -> list[dict[str, Any]]:
        fmp_period = "annual" if period == "annual" else "quarter"
        return self._get_json(
            "/balance-sheet-statement",
            {"symbol": symbol, "period": fmp_period},
        )

    def _get_json(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        started_at = time.perf_counter()
        req_params = dict(params)
        if self.api_key:
            req_params["apikey"] = self.api_key
        try:
            safe_params = {k: v for k, v in req_params.items() if k != "apikey"}
            LOGGER.info(
                'search_trace fmp_client_http_start path="%s" params=%s timeout_seconds=%s',
                path,
                safe_params,
                self.timeout_seconds,
            )
            response = self._session.get(
                f"{self.base_url}{path}",
                params=req_params,
                timeout=self.timeout_seconds,
            )
            response_duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            LOGGER.info(
                'search_trace fmp_client_http_response path="%s" status_code=%s duration_ms=%s',
                path,
                response.status_code,
                response_duration_ms,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.HTTPError as exc:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            status_code = exc.response.status_code if exc.response is not None else None
            LOGGER.exception(
                'search_trace fmp_client_http_error path="%s" error_type=http status_code=%s duration_ms=%s',
                path,
                status_code,
                duration_ms,
            )
            raise UpstreamServiceError(
                f"Market data provider request failed with status {status_code or 'unknown'}"
            ) from exc
        except requests.RequestException as exc:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            LOGGER.exception(
                'search_trace fmp_client_http_error path="%s" error_type=request_exception duration_ms=%s exc_type=%s',
                path,
                duration_ms,
                type(exc).__name__,
            )
            raise UpstreamServiceError() from exc
        except ValueError as exc:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            LOGGER.exception(
                'search_trace fmp_client_http_error path="%s" error_type=invalid_json duration_ms=%s',
                path,
                duration_ms,
            )
            raise UpstreamServiceError("Invalid response from market data provider") from exc

        if not isinstance(payload, list):
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            LOGGER.error(
                'search_trace fmp_client_http_error path="%s" error_type=invalid_payload duration_ms=%s payload_type=%s',
                path,
                duration_ms,
                type(payload).__name__,
            )
            raise UpstreamServiceError("Invalid response payload from market data provider")
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.info(
            'search_trace fmp_client_http_done path="%s" duration_ms=%s row_count=%s',
            path,
            duration_ms,
            len(payload),
        )
        return [item for item in payload if isinstance(item, dict)]
