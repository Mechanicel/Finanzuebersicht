from __future__ import annotations

from functools import lru_cache
import logging

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.config import get_settings
from app.providers import InMemoryMarketDataProvider, MarketDataProvider, YFinanceMarketDataProvider
from app.repositories import (
    InstrumentHydratedRepository,
    InstrumentSelectionCacheRepository,
    NoOpInstrumentHydratedRepository,
    NoOpInstrumentSelectionCacheRepository,
)
from app.service import MarketDataService

LOGGER = logging.getLogger(__name__)


@lru_cache
def get_provider() -> MarketDataProvider:
    settings = get_settings()
    marketdata_provider_name = settings.marketdata_provider.strip().lower()
    if marketdata_provider_name == "inmemory":
        return InMemoryMarketDataProvider()
    if marketdata_provider_name == "yfinance":
        return YFinanceMarketDataProvider(
            timeout_seconds=settings.marketdata_request_timeout_seconds,
            retries=settings.marketdata_request_retries,
            backoff_factor=settings.marketdata_request_backoff_factor,
            openfigi_base_url=settings.openfigi_base_url,
            openfigi_api_key=settings.openfigi_api_key,
            openfigi_timeout_seconds=settings.openfigi_request_timeout_seconds,
            openfigi_retries=settings.openfigi_request_retries,
            openfigi_backoff_factor=settings.openfigi_request_backoff_factor,
            openfigi_search_result_limit=settings.openfigi_search_result_limit,
            openfigi_default_market_sec_des=settings.openfigi_search_default_market_sec_des,
        )
    raise RuntimeError(f"Unsupported marketdata_provider '{settings.marketdata_provider}'")


@lru_cache
def get_selection_cache_repository() -> InstrumentSelectionCacheRepository | NoOpInstrumentSelectionCacheRepository:
    settings = get_settings()
    if not settings.marketdata_mongo_enabled:
        LOGGER.info("marketdata mongo is disabled, using in-memory/no-op selection cache repository")
        return NoOpInstrumentSelectionCacheRepository()

    try:
        client = MongoClient(
            settings.resolved_mongo_uri(),
            serverSelectionTimeoutMS=settings.marketdata_mongo_server_selection_timeout_ms,
        )
        client.admin.command("ping")
        collection = client[settings.mongo_database][settings.marketdata_selection_cache_collection]
        return InstrumentSelectionCacheRepository(collection=collection)
    except PyMongoError:
        LOGGER.warning(
            "marketdata mongo unavailable, falling back to no-op selection cache repository",
            exc_info=True,
        )
        return NoOpInstrumentSelectionCacheRepository()


@lru_cache
def get_hydrated_repository() -> InstrumentHydratedRepository | NoOpInstrumentHydratedRepository:
    settings = get_settings()
    if not settings.marketdata_mongo_enabled:
        LOGGER.info("marketdata mongo is disabled, using no-op hydrated repository")
        return NoOpInstrumentHydratedRepository()

    try:
        client = MongoClient(
            settings.resolved_mongo_uri(),
            serverSelectionTimeoutMS=settings.marketdata_mongo_server_selection_timeout_ms,
        )
        client.admin.command("ping")
        collection = client[settings.mongo_database][settings.marketdata_hydrated_collection]
        return InstrumentHydratedRepository(collection=collection)
    except PyMongoError:
        LOGGER.warning("marketdata mongo unavailable, falling back to no-op hydrated repository", exc_info=True)
        return NoOpInstrumentHydratedRepository()


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
        hydrated_repository=get_hydrated_repository(),
        selection_cache_ttl_seconds=settings.marketdata_cache_selection_ttl_seconds,
        hydrated_freshness_ttl_seconds=settings.marketdata_hydrated_freshness_ttl_seconds,
    )
