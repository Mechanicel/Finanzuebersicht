from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.providers import InMemoryMarketDataProvider, MarketDataProvider, YFinanceMarketDataProvider
from app.repositories import InstrumentSelectionCacheRepository
from app.service import MarketDataService


@lru_cache
def get_provider() -> MarketDataProvider:
    settings = get_settings()
    provider_name = settings.marketdata_provider.strip().lower()
    if provider_name == "inmemory":
        return InMemoryMarketDataProvider()
    if provider_name == "yfinance":
        return YFinanceMarketDataProvider(
            timeout_seconds=settings.marketdata_request_timeout_seconds,
            retries=settings.marketdata_request_retries,
            backoff_factor=settings.marketdata_request_backoff_factor,
        )
    raise RuntimeError(f"Unsupported marketdata_provider '{settings.marketdata_provider}'")


@lru_cache
def get_selection_cache_repository() -> InstrumentSelectionCacheRepository:
    settings = get_settings()
    return InstrumentSelectionCacheRepository(db_path=settings.marketdata_selection_cache_db_path)


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
        selection_cache_repository=get_selection_cache_repository(),
        selection_cache_ttl_seconds=settings.marketdata_cache_selection_ttl_seconds,
    )
