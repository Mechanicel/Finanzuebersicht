from __future__ import annotations

from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from app.config import get_settings
from app.repositories.masterdata_repository import MasterdataRepository, MongoMasterdataRepository
from app.services.masterdata_service import MasterdataService


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    settings = get_settings()
    return MongoClient(settings.resolved_mongo_uri())


@lru_cache(maxsize=1)
def get_mongo_database() -> Database:
    settings = get_settings()
    return get_mongo_client()[settings.mongo_database]


@lru_cache(maxsize=1)
def get_repository() -> MasterdataRepository:
    settings = get_settings()
    return MongoMasterdataRepository(
        database=get_mongo_database(),
        bank_collection=settings.mongo_bank_collection,
        account_type_collection=settings.mongo_account_type_collection,
    )


def get_masterdata_service() -> MasterdataService:
    return MasterdataService(repository=get_repository())
