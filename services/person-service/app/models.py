from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class PersonSortField(StrEnum):
    CREATED_AT = "created_at"
    LAST_NAME = "last_name"
    FIRST_NAME = "first_name"


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class PersonBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=254)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip().lower()


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=254)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip().lower()

    @model_validator(mode="after")
    def require_any_field(self) -> PersonUpdate:
        if self.model_dump(exclude_none=True) == {}:
            raise ValueError("Mindestens ein Feld muss gesetzt sein")
        return self


class Person(PersonBase):
    person_id: UUID = Field(default_factory=uuid4)
    created_at: str
    updated_at: str


class PersonBankAssignment(BaseModel):
    person_id: UUID
    bank_id: UUID
    assigned_at: str


class TaxAllowance(BaseModel):
    person_id: UUID
    bank_id: UUID
    amount: Decimal = Field(ge=Decimal("0"), max_digits=12, decimal_places=2)
    currency: str = Field(default="EUR", min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    updated_at: str


class PaginationMeta(BaseModel):
    limit: int = Field(ge=1, le=200)
    offset: int = Field(ge=0)
    returned: int = Field(ge=0)
    total: int = Field(ge=0)


class PersonListItem(BaseModel):
    person_id: UUID
    first_name: str
    last_name: str
    email: str | None
    bank_count: int = Field(ge=0)
    allowance_total: Decimal = Field(ge=Decimal("0"), max_digits=12, decimal_places=2)


class PersonListResponse(BaseModel):
    items: list[PersonListItem]
    pagination: PaginationMeta


class PersonDetailResponse(BaseModel):
    person: Person
    stats: PersonListItem


class AssignmentListResponse(BaseModel):
    items: list[PersonBankAssignment]
    total: int


class AllowanceListResponse(BaseModel):
    items: list[TaxAllowance]
    total: int
    amount_total: Decimal = Field(ge=Decimal("0"), max_digits=12, decimal_places=2)


class AllowanceSummaryBankItem(BaseModel):
    bank_id: UUID
    amount: Decimal = Field(ge=Decimal("0"), max_digits=12, decimal_places=2)


class AllowanceSummaryResponse(BaseModel):
    person_id: UUID
    banks: list[AllowanceSummaryBankItem]
    total_amount: Decimal = Field(ge=Decimal("0"), max_digits=12, decimal_places=2)
    currency: str
