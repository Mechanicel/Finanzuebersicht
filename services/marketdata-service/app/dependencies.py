from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.providers import InMemoryMarketDataProvider
from app.service import MarketDataService


@lru_cache
def get_provider() -> InMemoryMarketDataProvider:
    return InMemoryMarketDataProvider()


@lru_cache
def get_marketdata_service() -> MarketDataService:
    settings = get_settings()
    return MarketDataService(
        provider=get_provider(),
        cache_enabled=settings.cache_enabled,
        cache_search_ttl_seconds=settings.marketdata_cache_search_ttl_seconds,
        cache_summary_ttl_seconds=settings.marketdata_cache_summary_ttl_seconds,
        cache_price_ttl_seconds=settings.marketdata_cache_price_ttl_seconds,
        cache_series_ttl_seconds=settings.marketdata_cache_series_ttl_seconds,
        cache_benchmark_ttl_seconds=settings.marketdata_cache_benchmark_ttl_seconds,
    )
