from __future__ import annotations

from functools import lru_cache

from app.repositories.masterdata_repository import InMemoryMasterdataRepository, MasterdataRepository
from app.services.masterdata_service import MasterdataService


@lru_cache(maxsize=1)
def get_repository() -> MasterdataRepository:
    return InMemoryMasterdataRepository()


def get_masterdata_service() -> MasterdataService:
    return MasterdataService(repository=get_repository())
