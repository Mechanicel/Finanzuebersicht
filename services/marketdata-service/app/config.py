from __future__ import annotations

from functools import lru_cache

from finanzuebersicht_shared.config import ServiceSettings


class Settings(ServiceSettings):
    app_name: str = "marketdata-service"
    cache_enabled: bool = True
    marketdata_provider: str = "yfinance"
    marketdata_request_timeout_seconds: float = 8.0
    marketdata_request_retries: int = 2
    marketdata_request_backoff_factor: float = 0.3
    marketdata_cache_search_ttl_seconds: int = 60
    marketdata_cache_summary_ttl_seconds: int = 120
    marketdata_cache_price_ttl_seconds: int = 45
    marketdata_cache_series_ttl_seconds: int = 30
    marketdata_cache_benchmark_ttl_seconds: int = 900
    marketdata_cache_selection_ttl_seconds: int = 60
    marketdata_selection_cache_db_path: str = ".cache/marketdata_selection_cache.sqlite3"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
