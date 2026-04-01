from __future__ import annotations

from functools import lru_cache

from pymongo import MongoClient

from app.config import get_settings
from app.identity import FmpClient, FmpIdentifierResolver, IdentifierResolver, NoopIdentifierResolver
from app.providers import MarketDataProvider, YFinanceMarketDataProvider
from app.repositories import (
    InstrumentHydratedRepository,
    InstrumentSelectionCacheRepository,
    SecurityIdentityRepository,
)
from app.service import MarketDataService


@lru_cache
def get_provider() -> MarketDataProvider:
    settings = get_settings()
    provider_name = settings.marketdata_provider.strip().lower()
    if provider_name != "yfinance":
        raise RuntimeError(f"Unsupported marketdata_provider '{settings.marketdata_provider}'")

    return YFinanceMarketDataProvider(
        timeout_seconds=settings.marketdata_request_timeout_seconds,
        retries=settings.marketdata_request_retries,
        backoff_factor=settings.marketdata_request_backoff_factor,
    )


@lru_cache
def get_selection_cache_repository() -> InstrumentSelectionCacheRepository:
    settings = get_settings()
    client = MongoClient(settings.resolved_mongo_uri())
    collection = client[settings.mongo_database][settings.marketdata_selection_cache_collection]
    return InstrumentSelectionCacheRepository(collection=collection)


@lru_cache
def get_hydrated_repository() -> InstrumentHydratedRepository:
    settings = get_settings()
    client = MongoClient(settings.resolved_mongo_uri())
    collection = client[settings.mongo_database][settings.marketdata_hydrated_collection]
    return InstrumentHydratedRepository(collection=collection)


@lru_cache
def get_security_identity_repository() -> SecurityIdentityRepository:
    settings = get_settings()
    client = MongoClient(settings.resolved_mongo_uri())
    collection = client[settings.mongo_database][settings.marketdata_security_identity_collection]
    return SecurityIdentityRepository(collection=collection)


@lru_cache
def get_identifier_resolver() -> IdentifierResolver:
    settings = get_settings()
    resolver_name = settings.identifier_resolver.strip().lower()

    fmp_enabled = settings.fmp_enabled and resolver_name in {"fmp", "auto"}
    if fmp_enabled and settings.fmp_api_key:
        fmp_client = FmpClient(
            base_url=settings.fmp_base_url,
            api_key=settings.fmp_api_key,
            timeout_seconds=settings.fmp_request_timeout_seconds,
        )
        return FmpIdentifierResolver(client=fmp_client)

    return NoopIdentifierResolver()


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
        security_identity_repository=get_security_identity_repository(),
        identifier_resolver=get_identifier_resolver(),
    )
