from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from uuid import UUID

from app.models import PersonAccount


class AccountRepository(ABC):
    @abstractmethod
    def list_person_accounts(self, person_id: UUID) -> list[PersonAccount]: ...

    @abstractmethod
    def get_person_account(self, person_id: UUID, account_id: UUID) -> PersonAccount | None: ...

    @abstractmethod
    def create_person_account(self, account: PersonAccount) -> PersonAccount: ...

    @abstractmethod
    def update_person_account(self, account: PersonAccount) -> PersonAccount: ...


class InMemoryAccountRepository(AccountRepository):
    def __init__(self) -> None:
        self._accounts_by_person: dict[UUID, dict[UUID, PersonAccount]] = defaultdict(dict)

    def list_person_accounts(self, person_id: UUID) -> list[PersonAccount]:
        accounts = self._accounts_by_person.get(person_id, {})
        return sorted(accounts.values(), key=lambda item: item.created_at)

    def get_person_account(self, person_id: UUID, account_id: UUID) -> PersonAccount | None:
        return self._accounts_by_person.get(person_id, {}).get(account_id)

    def create_person_account(self, account: PersonAccount) -> PersonAccount:
        self._accounts_by_person[account.person_id][account.account_id] = account
        return account

    def update_person_account(self, account: PersonAccount) -> PersonAccount:
        self._accounts_by_person[account.person_id][account.account_id] = account
        return account
