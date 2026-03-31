from __future__ import annotations

from functools import lru_cache

from finanzuebersicht_shared.config import ServiceSettings


class Settings(ServiceSettings):
    app_name: str = "marketdata-service"
    cache_enabled: bool = True
    marketdata_cache_search_ttl_seconds: int = 60
    marketdata_cache_summary_ttl_seconds: int = 120
    marketdata_cache_price_ttl_seconds: int = 45
    marketdata_cache_series_ttl_seconds: int = 30
    marketdata_cache_benchmark_ttl_seconds: int = 900


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
