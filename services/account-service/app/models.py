from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class AccountType(StrEnum):
    GIROKONTO = "girokonto"
    TAGESGELDKONTO = "tagesgeldkonto"
    FESTGELDKONTO = "festgeldkonto"
    DEPOT = "depot"


class PersonAccount(BaseModel):
    account_id: UUID = Field(default_factory=uuid4)
    person_id: UUID
    bank_id: UUID
    account_type: AccountType
    label: str = Field(min_length=1, max_length=120)
    balance: Decimal = Field(max_digits=16, decimal_places=2)
    currency: str = Field(default="EUR", min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    created_at: str
    updated_at: str
    account_number: str | None = None
    depot_number: str | None = None
    iban: str | None = None
    opening_date: str | None = None
    interest_rate: Decimal | None = Field(default=None, max_digits=7, decimal_places=4)
    payout_account_iban: str | None = None
    settlement_account_iban: str | None = None
    portfolio_id: UUID | None = None


class PersonAccountCreate(BaseModel):
    bank_id: UUID
    account_type: AccountType
    label: str = Field(min_length=1, max_length=120)
    balance: Decimal = Field(max_digits=16, decimal_places=2)
    currency: str = Field(default="EUR", min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    account_number: str | None = None
    depot_number: str | None = None
    iban: str | None = None
    opening_date: str | None = None
    interest_rate: Decimal | None = Field(default=None, max_digits=7, decimal_places=4)
    payout_account_iban: str | None = None
    settlement_account_iban: str | None = None
    portfolio_id: UUID | None = None


class PersonAccountUpdate(BaseModel):
    bank_id: UUID | None = None
    account_type: AccountType | None = None
    label: str | None = Field(default=None, min_length=1, max_length=120)
    balance: Decimal | None = Field(default=None, max_digits=16, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    account_number: str | None = None
    depot_number: str | None = None
    iban: str | None = None
    opening_date: str | None = None
    interest_rate: Decimal | None = Field(default=None, max_digits=7, decimal_places=4)
    payout_account_iban: str | None = None
    settlement_account_iban: str | None = None
    portfolio_id: UUID | None = None

    @model_validator(mode="after")
    def require_any_field(self) -> PersonAccountUpdate:
        if self.model_dump(exclude_none=True) == {}:
            raise ValueError("Mindestens ein Feld muss gesetzt sein")
        return self
