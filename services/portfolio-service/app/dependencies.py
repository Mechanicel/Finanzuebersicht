from __future__ import annotations

from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from app.config import get_settings
from app.repositories import (
    InMemoryPortfolioRepository,
    MongoPortfolioRepository,
    PortfolioRepository,
)
from app.service import PortfolioService


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    settings = get_settings()
    return MongoClient(
        settings.resolved_mongo_uri(),
        serverSelectionTimeoutMS=settings.portfolio_mongo_server_selection_timeout_ms,
    )


@lru_cache(maxsize=1)
def get_mongo_database() -> Database:
    settings = get_settings()
    return get_mongo_client()[settings.mongo_database]


@lru_cache(maxsize=1)
def get_repository() -> PortfolioRepository:
    settings = get_settings()
    if settings.portfolio_repository_backend == "inmemory":
        return InMemoryPortfolioRepository()
    if settings.portfolio_repository_backend == "mongo":
        database = get_mongo_database()
        database.command("ping")
        return MongoPortfolioRepository(
            database=database,
            portfolio_collection=settings.mongo_portfolios_collection,
            holding_collection=settings.mongo_holdings_collection,
            benchmark_config_collection=settings.mongo_benchmark_configs_collection,
        )
    raise ValueError(f"Unsupported portfolio repository backend: {settings.portfolio_repository_backend}")


@lru_cache(maxsize=1)
def get_portfolio_service() -> PortfolioService:
    return PortfolioService(repository=get_repository())
