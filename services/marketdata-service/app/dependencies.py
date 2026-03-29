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
        cache_ttl_seconds=settings.cache_ttl_seconds,
    )
