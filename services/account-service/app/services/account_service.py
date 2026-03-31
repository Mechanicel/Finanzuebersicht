from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import TypeVar
from uuid import UUID

from fastapi import HTTPException, status

from app.models import PersonAccount, PersonAccountCreate, PersonAccountUpdate
from app.repositories.account_repository import AccountRepository, AccountRepositoryError

RepositoryResult = TypeVar("RepositoryResult")


class AccountService:
    def __init__(self, repository: AccountRepository) -> None:
        self.repository = repository

    def list_person_accounts(self, person_id: UUID) -> list[PersonAccount]:
        return self._with_repository_error_handling(
            lambda: self.repository.list_person_accounts(person_id)
        )

    def get_person_account(self, person_id: UUID, account_id: UUID) -> PersonAccount:
        account = self._with_repository_error_handling(
            lambda: self.repository.get_person_account(person_id, account_id)
        )
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Konto nicht gefunden")
        return account

    def create_person_account(self, person_id: UUID, payload: PersonAccountCreate) -> PersonAccount:
        now = self._now()
        account = PersonAccount(
            person_id=person_id,
            created_at=now,
            updated_at=now,
            **payload.model_dump(),
        )
        return self._with_repository_error_handling(
            lambda: self.repository.create_person_account(account)
        )

    def update_person_account(
        self,
        person_id: UUID,
        account_id: UUID,
        payload: PersonAccountUpdate,
    ) -> PersonAccount:
        current = self.get_person_account(person_id, account_id)
        merged = current.model_copy(update=payload.model_dump(exclude_none=True))
        merged.updated_at = self._now()
        return self._with_repository_error_handling(
            lambda: self.repository.update_person_account(merged)
        )

    def delete_person_account(self, person_id: UUID, account_id: UUID) -> None:
        deleted = self._with_repository_error_handling(
            lambda: self.repository.delete_person_account(person_id, account_id)
        )
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Konto nicht gefunden")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _with_repository_error_handling(call: Callable[[], RepositoryResult]) -> RepositoryResult:
        try:
            return call()
        except AccountRepositoryError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Kontospeicher derzeit nicht verfügbar",
            ) from exc
