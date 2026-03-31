from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from pymongo import ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.models import PersonAccount


class AccountRepositoryError(Exception):
    pass


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


class MongoAccountRepository(AccountRepository):
    def __init__(self, database: Database, *, account_collection: str) -> None:
        self._accounts: Collection = database[account_collection]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self._accounts.create_index(
            [("person_id", ASCENDING), ("account_id", ASCENDING)],
            unique=True,
        )
        self._accounts.create_index([("person_id", ASCENDING), ("created_at", ASCENDING)])

    def list_person_accounts(self, person_id: UUID) -> list[PersonAccount]:
        try:
            docs = self._accounts.find(
                {"person_id": str(person_id)},
                {"_id": 0},
            ).sort("created_at", ASCENDING)
            return [self._from_doc(doc) for doc in docs]
        except PyMongoError as exc:
            raise AccountRepositoryError("Failed to list accounts") from exc

    def get_person_account(self, person_id: UUID, account_id: UUID) -> PersonAccount | None:
        try:
            doc = self._accounts.find_one(
                {"person_id": str(person_id), "account_id": str(account_id)},
                {"_id": 0},
            )
        except PyMongoError as exc:
            raise AccountRepositoryError("Failed to load account") from exc
        if doc is None:
            return None
        return self._from_doc(doc)

    def create_person_account(self, account: PersonAccount) -> PersonAccount:
        try:
            self._accounts.insert_one(self._to_doc(account))
            return account
        except PyMongoError as exc:
            raise AccountRepositoryError("Failed to create account") from exc

    def update_person_account(self, account: PersonAccount) -> PersonAccount:
        try:
            self._accounts.replace_one(
                {"person_id": str(account.person_id), "account_id": str(account.account_id)},
                self._to_doc(account),
                upsert=False,
            )
            return account
        except PyMongoError as exc:
            raise AccountRepositoryError("Failed to update account") from exc

    @staticmethod
    def _to_doc(account: PersonAccount) -> dict[str, object]:
        return {
            "account_id": str(account.account_id),
            "person_id": str(account.person_id),
            "bank_id": str(account.bank_id),
            "account_type": account.account_type.value,
            "label": account.label,
            "balance": str(account.balance),
            "currency": account.currency,
            "created_at": account.created_at,
            "updated_at": account.updated_at,
            "account_number": account.account_number,
            "depot_number": account.depot_number,
            "iban": account.iban,
            "opening_date": account.opening_date,
            "interest_rate": (
                str(account.interest_rate) if account.interest_rate is not None else None
            ),
            "payout_account_iban": account.payout_account_iban,
            "settlement_account_iban": account.settlement_account_iban,
        }

    @staticmethod
    def _from_doc(doc: dict[str, object]) -> PersonAccount:
        account_doc = dict(doc)
        account_doc["balance"] = Decimal(str(account_doc["balance"]))
        interest_rate = account_doc.get("interest_rate")
        account_doc["interest_rate"] = (
            Decimal(str(interest_rate)) if interest_rate is not None else None
        )
        return PersonAccount.model_validate(account_doc)
