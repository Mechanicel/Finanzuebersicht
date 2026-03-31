from __future__ import annotations

from functools import lru_cache

from app.repositories import InMemoryAccountRepository
from app.services import AccountService


@lru_cache(maxsize=1)
def get_repository() -> InMemoryAccountRepository:
    return InMemoryAccountRepository()


@lru_cache(maxsize=1)
def get_account_service() -> AccountService:
    return AccountService(repository=get_repository())
