from __future__ import annotations

from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from app.config import get_settings
from app.repositories.person_repository import MongoPersonRepository, PersonRepository
from app.services.person_service import PersonService


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    settings = get_settings()
    return MongoClient(settings.resolved_mongo_uri())


@lru_cache(maxsize=1)
def get_mongo_database() -> Database:
    settings = get_settings()
    return get_mongo_client()[settings.mongo_database]


@lru_cache(maxsize=1)
def get_repository() -> PersonRepository:
    settings = get_settings()
    return MongoPersonRepository(
        database=get_mongo_database(),
        person_collection=settings.mongo_person_collection,
        assignment_collection=settings.mongo_assignment_collection,
        allowance_collection=settings.mongo_allowance_collection,
    )


def get_person_service() -> PersonService:
    return PersonService(repository=get_repository())
