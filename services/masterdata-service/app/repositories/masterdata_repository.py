from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from pymongo import ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.models import AccountType, Bank


class MasterdataRepository(ABC):
    @abstractmethod
    def list_banks(self) -> list[Bank]: ...

    @abstractmethod
    def create_bank(self, bank: Bank) -> Bank: ...

    @abstractmethod
    def get_bank(self, bank_id: UUID) -> Bank | None: ...

    @abstractmethod
    def update_bank(self, bank: Bank) -> Bank: ...

    @abstractmethod
    def delete_bank(self, bank_id: UUID) -> bool: ...

    @abstractmethod
    def list_account_types(self) -> list[AccountType]: ...

    @abstractmethod
    def create_account_type(self, account_type: AccountType) -> AccountType: ...

    @abstractmethod
    def get_account_type(self, account_type_id: UUID) -> AccountType | None: ...

    @abstractmethod
    def update_account_type(self, account_type: AccountType) -> AccountType: ...

    @abstractmethod
    def delete_account_type(self, account_type_id: UUID) -> bool: ...


class InMemoryMasterdataRepository(MasterdataRepository):
    def __init__(self) -> None:
        self._banks: dict[UUID, Bank] = {}
        self._account_types: dict[UUID, AccountType] = {}

    def list_banks(self) -> list[Bank]:
        return sorted(self._banks.values(), key=lambda x: x.name.lower())

    def create_bank(self, bank: Bank) -> Bank:
        self._banks[bank.bank_id] = bank
        return bank

    def get_bank(self, bank_id: UUID) -> Bank | None:
        return self._banks.get(bank_id)

    def update_bank(self, bank: Bank) -> Bank:
        self._banks[bank.bank_id] = bank
        return bank

    def delete_bank(self, bank_id: UUID) -> bool:
        return self._banks.pop(bank_id, None) is not None

    def list_account_types(self) -> list[AccountType]:
        return sorted(self._account_types.values(), key=lambda x: x.name.lower())

    def create_account_type(self, account_type: AccountType) -> AccountType:
        self._account_types[account_type.account_type_id] = account_type
        return account_type

    def get_account_type(self, account_type_id: UUID) -> AccountType | None:
        return self._account_types.get(account_type_id)

    def update_account_type(self, account_type: AccountType) -> AccountType:
        self._account_types[account_type.account_type_id] = account_type
        return account_type

    def delete_account_type(self, account_type_id: UUID) -> bool:
        return self._account_types.pop(account_type_id, None) is not None


class MongoMasterdataRepository(MasterdataRepository):
    def __init__(self, database: Database, *, bank_collection: str, account_type_collection: str) -> None:
        self._banks: Collection = database[bank_collection]
        self._account_types: Collection = database[account_type_collection]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self._banks.create_index([("bank_id", ASCENDING)], unique=True)
        self._banks.create_index([("bic", ASCENDING)], unique=True)
        self._banks.create_index([("blz", ASCENDING)], unique=True)
        self._account_types.create_index([("account_type_id", ASCENDING)], unique=True)
        self._account_types.create_index([("key", ASCENDING)], unique=True)

    def list_banks(self) -> list[Bank]:
        docs = self._banks.find({}, {"_id": 0})
        return sorted((self._bank_from_doc(doc) for doc in docs), key=lambda item: item.name.lower())

    def create_bank(self, bank: Bank) -> Bank:
        self._banks.insert_one(self._bank_to_doc(bank))
        return bank

    def get_bank(self, bank_id: UUID) -> Bank | None:
        doc = self._banks.find_one({"bank_id": str(bank_id)}, {"_id": 0})
        if doc is None:
            return None
        return self._bank_from_doc(doc)

    def update_bank(self, bank: Bank) -> Bank:
        self._banks.replace_one({"bank_id": str(bank.bank_id)}, self._bank_to_doc(bank), upsert=False)
        return bank

    def delete_bank(self, bank_id: UUID) -> bool:
        return self._banks.delete_one({"bank_id": str(bank_id)}).deleted_count > 0

    def list_account_types(self) -> list[AccountType]:
        docs = self._account_types.find({}, {"_id": 0})
        return sorted((self._account_type_from_doc(doc) for doc in docs), key=lambda item: item.name.lower())

    def create_account_type(self, account_type: AccountType) -> AccountType:
        self._account_types.insert_one(self._account_type_to_doc(account_type))
        return account_type

    def get_account_type(self, account_type_id: UUID) -> AccountType | None:
        doc = self._account_types.find_one({"account_type_id": str(account_type_id)}, {"_id": 0})
        if doc is None:
            return None
        return self._account_type_from_doc(doc)

    def update_account_type(self, account_type: AccountType) -> AccountType:
        self._account_types.replace_one(
            {"account_type_id": str(account_type.account_type_id)},
            self._account_type_to_doc(account_type),
            upsert=False,
        )
        return account_type

    def delete_account_type(self, account_type_id: UUID) -> bool:
        return self._account_types.delete_one({"account_type_id": str(account_type_id)}).deleted_count > 0

    @staticmethod
    def is_duplicate_error(exc: Exception) -> bool:
        return isinstance(exc, DuplicateKeyError)

    @staticmethod
    def _bank_to_doc(bank: Bank) -> dict[str, str]:
        return {
            "bank_id": str(bank.bank_id),
            "name": bank.name,
            "bic": bank.bic,
            "blz": bank.blz,
            "country_code": bank.country_code,
        }

    @staticmethod
    def _bank_from_doc(doc: dict) -> Bank:
        return Bank.model_validate(doc)

    @staticmethod
    def _account_type_to_doc(account_type: AccountType) -> dict:
        payload = account_type.model_dump(mode="json")
        payload["account_type_id"] = str(account_type.account_type_id)
        return payload

    @staticmethod
    def _account_type_from_doc(doc: dict) -> AccountType:
        return AccountType.model_validate(doc)
