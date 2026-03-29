from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status

from app.models import (
    AccountType,
    AccountTypeCreate,
    AccountTypeListResponse,
    AccountTypeUpdate,
    Bank,
    BankCreate,
    BankListResponse,
    BankUpdate,
)
from app.repositories.masterdata_repository import MasterdataRepository


class MasterdataService:
    def __init__(self, repository: MasterdataRepository) -> None:
        self.repository = repository

    def list_banks(self) -> BankListResponse:
        items = self.repository.list_banks()
        return BankListResponse(items=items, total=len(items))

    def create_bank(self, payload: BankCreate) -> Bank:
        self._assert_bank_uniqueness(bic=payload.bic, blz=payload.blz)
        bank = Bank(**payload.model_dump())
        return self.repository.create_bank(bank)

    def get_bank(self, bank_id: UUID) -> Bank:
        bank = self.repository.get_bank(bank_id)
        if bank is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank nicht gefunden")
        return bank

    def update_bank(self, bank_id: UUID, payload: BankUpdate) -> Bank:
        current = self.get_bank(bank_id)
        update_data = payload.model_dump(exclude_none=True)
        merged = current.model_copy(update=update_data)
        self._assert_bank_uniqueness(bic=merged.bic, blz=merged.blz, exclude_id=bank_id)
        return self.repository.update_bank(merged)

    def delete_bank(self, bank_id: UUID) -> None:
        deleted = self.repository.delete_bank(bank_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank nicht gefunden")

    def list_account_types(self) -> AccountTypeListResponse:
        items = self.repository.list_account_types()
        return AccountTypeListResponse(items=items, total=len(items))

    def create_account_type(self, payload: AccountTypeCreate) -> AccountType:
        self._assert_account_type_key_uniqueness(payload.key)
        account_type = AccountType(**payload.model_dump())
        account_type.schema_fields.sort(key=lambda item: item.order)
        return self.repository.create_account_type(account_type)

    def get_account_type(self, account_type_id: UUID) -> AccountType:
        account_type = self.repository.get_account_type(account_type_id)
        if account_type is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kontotyp nicht gefunden")
        return account_type

    def update_account_type(self, account_type_id: UUID, payload: AccountTypeUpdate) -> AccountType:
        current = self.get_account_type(account_type_id)
        merged = current.model_copy(update=payload.model_dump(exclude_none=True))
        self._assert_account_type_key_uniqueness(merged.key, exclude_id=account_type_id)
        merged.schema_fields.sort(key=lambda item: item.order)
        return self.repository.update_account_type(merged)

    def delete_account_type(self, account_type_id: UUID) -> None:
        deleted = self.repository.delete_account_type(account_type_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kontotyp nicht gefunden")

    def _assert_bank_uniqueness(self, *, bic: str, blz: str, exclude_id: UUID | None = None) -> None:
        for bank in self.repository.list_banks():
            if exclude_id is not None and bank.bank_id == exclude_id:
                continue
            if bank.bic == bic:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="BIC bereits vorhanden")
            if bank.blz == blz:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="BLZ bereits vorhanden")

    def _assert_account_type_key_uniqueness(self, key: str, exclude_id: UUID | None = None) -> None:
        for account_type in self.repository.list_account_types():
            if exclude_id is not None and account_type.account_type_id == exclude_id:
                continue
            if account_type.key == key:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Kontotyp-Key bereits vorhanden")
