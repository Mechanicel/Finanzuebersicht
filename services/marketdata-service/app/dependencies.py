from __future__ import annotations

from functools import lru_cache
import logging
import time

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.clients.fmp_client import FMPClient
from app.config import get_settings
from app.repositories import (
    CurrentPriceCacheRepository,
    FinancialsCacheRepository,
    InMemoryCurrentPriceCacheRepository,
    InMemoryFinancialsCacheRepository,
    InMemoryInstrumentProfileCacheRepository,
    InMemoryPriceHistoryCacheRepository,
    InstrumentProfileCacheRepository,
    PriceHistoryCacheRepository,
)
from app.service import MarketDataService

LOGGER = logging.getLogger(__name__)


@lru_cache
def get_fmp_client() -> FMPClient:
    started_at = time.perf_counter()
    LOGGER.info("search_trace dependency_get_fmp_client_start")
    settings = get_settings()
    client = FMPClient(
        base_url=settings.fmp_base_url,
        api_key=settings.fmp_api_key,
        timeout_seconds=settings.fmp_request_timeout_seconds,
        retries=settings.fmp_request_retries,
        backoff_factor=settings.fmp_request_backoff_factor,
    )
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    LOGGER.info("search_trace dependency_get_fmp_client_end duration_ms=%s", duration_ms)
    return client


@lru_cache
def get_profile_repository() -> InstrumentProfileCacheRepository | InMemoryInstrumentProfileCacheRepository:
    started_at = time.perf_counter()
    LOGGER.info("search_trace dependency_profile_repo_start")
    settings = get_settings()
    if not settings.marketdata_mongo_enabled:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.info(
            "search_trace dependency_profile_repo_end backend=inmemory mongo_enabled=false duration_ms=%s",
            duration_ms,
        )
        return InMemoryInstrumentProfileCacheRepository()

    try:
        client = MongoClient(
            settings.resolved_mongo_uri(),
            serverSelectionTimeoutMS=settings.marketdata_mongo_server_selection_timeout_ms,
        )
        ping_started_at = time.perf_counter()
        LOGGER.info("search_trace dependency_profile_repo_mongo_ping_start")
        client.admin.command("ping")
        ping_duration_ms = round((time.perf_counter() - ping_started_at) * 1000, 2)
        LOGGER.info("search_trace dependency_profile_repo_mongo_ping_done duration_ms=%s", ping_duration_ms)
        collection = client[settings.mongo_database][settings.marketdata_profile_cache_collection]
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.info("search_trace dependency_profile_repo_end backend=mongo duration_ms=%s", duration_ms)
        return InstrumentProfileCacheRepository(collection=collection)
    except PyMongoError:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.warning(
            "search_trace dependency_profile_repo_end backend=inmemory mongo_error=true duration_ms=%s",
            duration_ms,
            exc_info=True,
        )
        return InMemoryInstrumentProfileCacheRepository()


@lru_cache
def get_current_price_repository() -> CurrentPriceCacheRepository | InMemoryCurrentPriceCacheRepository:
    started_at = time.perf_counter()
    LOGGER.info("search_trace dependency_current_price_repo_start")
    settings = get_settings()
    if not settings.marketdata_mongo_enabled:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.info(
            "search_trace dependency_current_price_repo_end backend=inmemory mongo_enabled=false duration_ms=%s",
            duration_ms,
        )
        return InMemoryCurrentPriceCacheRepository()

    try:
        client = MongoClient(
            settings.resolved_mongo_uri(),
            serverSelectionTimeoutMS=settings.marketdata_mongo_server_selection_timeout_ms,
        )
        ping_started_at = time.perf_counter()
        LOGGER.info("search_trace dependency_current_price_repo_mongo_ping_start")
        client.admin.command("ping")
        ping_duration_ms = round((time.perf_counter() - ping_started_at) * 1000, 2)
        LOGGER.info("search_trace dependency_current_price_repo_mongo_ping_done duration_ms=%s", ping_duration_ms)
        collection = client[settings.mongo_database][settings.marketdata_current_price_cache_collection]
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.info("search_trace dependency_current_price_repo_end backend=mongo duration_ms=%s", duration_ms)
        return CurrentPriceCacheRepository(collection=collection)
    except PyMongoError:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.warning(
            "search_trace dependency_current_price_repo_end backend=inmemory mongo_error=true duration_ms=%s",
            duration_ms,
            exc_info=True,
        )
        return InMemoryCurrentPriceCacheRepository()


@lru_cache
def get_price_history_repository() -> PriceHistoryCacheRepository | InMemoryPriceHistoryCacheRepository:
    started_at = time.perf_counter()
    LOGGER.info("search_trace dependency_price_history_repo_start")
    settings = get_settings()
    if not settings.marketdata_mongo_enabled:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.info(
            "search_trace dependency_price_history_repo_end backend=inmemory mongo_enabled=false duration_ms=%s",
            duration_ms,
        )
        return InMemoryPriceHistoryCacheRepository()

    try:
        client = MongoClient(
            settings.resolved_mongo_uri(),
            serverSelectionTimeoutMS=settings.marketdata_mongo_server_selection_timeout_ms,
        )
        ping_started_at = time.perf_counter()
        LOGGER.info("search_trace dependency_price_history_repo_mongo_ping_start")
        client.admin.command("ping")
        ping_duration_ms = round((time.perf_counter() - ping_started_at) * 1000, 2)
        LOGGER.info("search_trace dependency_price_history_repo_mongo_ping_done duration_ms=%s", ping_duration_ms)
        collection = client[settings.mongo_database][settings.marketdata_price_history_cache_collection]
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.info("search_trace dependency_price_history_repo_end backend=mongo duration_ms=%s", duration_ms)
        return PriceHistoryCacheRepository(collection=collection)
    except PyMongoError:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.warning(
            "search_trace dependency_price_history_repo_end backend=inmemory mongo_error=true duration_ms=%s",
            duration_ms,
            exc_info=True,
        )
        return InMemoryPriceHistoryCacheRepository()


@lru_cache
def get_financials_repository() -> FinancialsCacheRepository | InMemoryFinancialsCacheRepository:
    started_at = time.perf_counter()
    LOGGER.info("search_trace dependency_financials_repo_start")
    settings = get_settings()
    if not settings.marketdata_mongo_enabled:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.info(
            "search_trace dependency_financials_repo_end backend=inmemory mongo_enabled=false duration_ms=%s",
            duration_ms,
        )
        return InMemoryFinancialsCacheRepository()

    try:
        client = MongoClient(
            settings.resolved_mongo_uri(),
            serverSelectionTimeoutMS=settings.marketdata_mongo_server_selection_timeout_ms,
        )
        ping_started_at = time.perf_counter()
        LOGGER.info("search_trace dependency_financials_repo_mongo_ping_start")
        client.admin.command("ping")
        ping_duration_ms = round((time.perf_counter() - ping_started_at) * 1000, 2)
        LOGGER.info("search_trace dependency_financials_repo_mongo_ping_done duration_ms=%s", ping_duration_ms)
        collection = client[settings.mongo_database][settings.marketdata_financials_cache_collection]
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.info("search_trace dependency_financials_repo_end backend=mongo duration_ms=%s", duration_ms)
        return FinancialsCacheRepository(collection=collection)
    except PyMongoError:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.warning(
            "search_trace dependency_financials_repo_end backend=inmemory mongo_error=true duration_ms=%s",
            duration_ms,
            exc_info=True,
        )
        return InMemoryFinancialsCacheRepository()

@lru_cache
def get_marketdata_service() -> MarketDataService:
    started_at = time.perf_counter()
    LOGGER.info("search_trace dependency_get_marketdata_service_start")
    settings = get_settings()
    service = MarketDataService(
        fmp_client=get_fmp_client(),
        profile_repository=get_profile_repository(),
        current_price_repository=get_current_price_repository(),
        price_history_repository=get_price_history_repository(),
        financials_repository=get_financials_repository(),
        cache_enabled=settings.cache_enabled,
        profile_cache_ttl_seconds=settings.marketdata_profile_cache_ttl_seconds,
        financials_cache_ttl_seconds=settings.marketdata_financials_cache_ttl_seconds,
    )
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    LOGGER.info("search_trace dependency_get_marketdata_service_end duration_ms=%s", duration_ms)
    return service
