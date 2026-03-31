from __future__ import annotations

from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from app.config import get_settings
from app.repositories import AccountRepository, InMemoryAccountRepository, MongoAccountRepository
from app.services import AccountService


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    settings = get_settings()
    return MongoClient(settings.resolved_mongo_uri())


@lru_cache(maxsize=1)
def get_mongo_database() -> Database:
    settings = get_settings()
    return get_mongo_client()[settings.mongo_database]


@lru_cache(maxsize=1)
def get_repository() -> AccountRepository:
    settings = get_settings()
    if settings.account_repository_backend == "inmemory":
        return InMemoryAccountRepository()
    if settings.account_repository_backend == "mongo":
        return MongoAccountRepository(
            database=get_mongo_database(),
            account_collection=settings.mongo_accounts_collection,
        )
    raise ValueError(
        f"Unsupported account repository backend: {settings.account_repository_backend}"
    )


@lru_cache(maxsize=1)
def get_account_service() -> AccountService:
    return AccountService(repository=get_repository())
