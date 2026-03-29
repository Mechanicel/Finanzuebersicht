from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

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
