from __future__ import annotations

from functools import lru_cache
import logging

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.clients.fmp_client import FMPClient
from app.config import get_settings
from app.repositories import InMemoryInstrumentProfileCacheRepository, InstrumentProfileCacheRepository
from app.service import MarketDataService

LOGGER = logging.getLogger(__name__)


@lru_cache
def get_fmp_client() -> FMPClient:
    settings = get_settings()
    return FMPClient(
        base_url=settings.fmp_base_url,
        api_key=settings.fmp_api_key,
        timeout_seconds=settings.fmp_request_timeout_seconds,
        retries=settings.fmp_request_retries,
        backoff_factor=settings.fmp_request_backoff_factor,
    )


@lru_cache
def get_profile_repository() -> InstrumentProfileCacheRepository | InMemoryInstrumentProfileCacheRepository:
    settings = get_settings()
    if not settings.marketdata_mongo_enabled:
        LOGGER.info("marketdata mongo is disabled, using in-memory profile cache repository")
        return InMemoryInstrumentProfileCacheRepository()

    try:
        client = MongoClient(
            settings.resolved_mongo_uri(),
            serverSelectionTimeoutMS=settings.marketdata_mongo_server_selection_timeout_ms,
        )
        client.admin.command("ping")
        collection = client[settings.mongo_database][settings.marketdata_profile_cache_collection]
        return InstrumentProfileCacheRepository(collection=collection)
    except PyMongoError:
        LOGGER.warning(
            "marketdata mongo unavailable, falling back to in-memory profile cache repository",
            exc_info=True,
        )
        return InMemoryInstrumentProfileCacheRepository()


@lru_cache
def get_marketdata_service() -> MarketDataService:
    settings = get_settings()
    return MarketDataService(
        fmp_client=get_fmp_client(),
        profile_repository=get_profile_repository(),
        cache_enabled=settings.cache_enabled,
        profile_cache_ttl_seconds=settings.marketdata_profile_cache_ttl_seconds,
    )
