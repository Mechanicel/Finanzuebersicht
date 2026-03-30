from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status

from app.models import PersonAccount, PersonAccountCreate, PersonAccountUpdate
from app.repositories.account_repository import AccountRepository


class AccountService:
    def __init__(self, repository: AccountRepository) -> None:
        self.repository = repository

    def list_person_accounts(self, person_id: UUID) -> list[PersonAccount]:
        return self.repository.list_person_accounts(person_id)

    def get_person_account(self, person_id: UUID, account_id: UUID) -> PersonAccount:
        account = self.repository.get_person_account(person_id, account_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Konto nicht gefunden")
        return account

    def create_person_account(self, person_id: UUID, payload: PersonAccountCreate) -> PersonAccount:
        now = self._now()
        account = PersonAccount(person_id=person_id, created_at=now, updated_at=now, **payload.model_dump())
        return self.repository.create_person_account(account)

    def update_person_account(self, person_id: UUID, account_id: UUID, payload: PersonAccountUpdate) -> PersonAccount:
        current = self.get_person_account(person_id, account_id)
        merged = current.model_copy(update=payload.model_dump(exclude_none=True))
        merged.updated_at = self._now()
        return self.repository.update_person_account(merged)

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()
