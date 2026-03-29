from __future__ import annotations

from functools import lru_cache

from app.repositories.person_repository import InMemoryPersonRepository, PersonRepository
from app.services.person_service import PersonService


@lru_cache(maxsize=1)
def get_repository() -> PersonRepository:
    return InMemoryPersonRepository()


def get_person_service() -> PersonService:
    return PersonService(repository=get_repository())
