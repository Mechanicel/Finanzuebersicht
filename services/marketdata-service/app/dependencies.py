from __future__ import annotations

from functools import lru_cache

from pymongo import MongoClient

from app.config import get_settings
from app.identity import IdentifierResolver, NoopIdentifierResolver, OpenFigiClient, OpenFigiIdentifierResolver
from app.providers import InMemoryMarketDataProvider, MarketDataProvider, YFinanceMarketDataProvider
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
    openfigi_enabled = settings.openfigi_enabled and resolver_name in {"openfigi", "auto"}
    if not openfigi_enabled:
        return NoopIdentifierResolver()

    if not settings.openfigi_api_key:
        return NoopIdentifierResolver()

    client = OpenFigiClient(
        base_url=settings.openfigi_base_url,
        api_key=settings.openfigi_api_key,
        timeout_seconds=settings.openfigi_request_timeout_seconds,
    )
    return OpenFigiIdentifierResolver(client=client)


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
