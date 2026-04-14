from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class FieldType(StrEnum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    SELECT = "select"
    EMAIL = "email"


class FieldOption(BaseModel):
    value: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=120)


class AccountTypeFieldBase(BaseModel):
    feldname: str = Field(min_length=1, max_length=80, pattern=r"^[a-z][a-z0-9_]*$")
    label: str = Field(min_length=1, max_length=120)
    typ: FieldType
    required: bool = False
    placeholder: str | None = Field(default=None, max_length=180)
    default: Any | None = None
    options: list[FieldOption] = Field(default_factory=list)
    help_text: str | None = Field(default=None, max_length=400)
    order: int = Field(ge=0, le=10_000)

    @model_validator(mode="after")
    def validate_options_for_type(self) -> AccountTypeFieldBase:
        if self.typ == FieldType.SELECT and len(self.options) == 0:
            raise ValueError("select-Felder benötigen mindestens eine Option")
        if self.typ != FieldType.SELECT and self.options:
            raise ValueError("options sind nur für typ=select erlaubt")
        return self


class BankCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    bic: str = Field(min_length=8, max_length=11, pattern=r"^[A-Z0-9]{8}([A-Z0-9]{3})?$")
    blz: str = Field(min_length=8, max_length=8, pattern=r"^[0-9]{8}$")
    country_code: str = Field(default="DE", min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")


class BankUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    bic: str | None = Field(default=None, min_length=8, max_length=11, pattern=r"^[A-Z0-9]{8}([A-Z0-9]{3})?$")
    blz: str | None = Field(default=None, min_length=8, max_length=8, pattern=r"^[0-9]{8}$")
    country_code: str | None = Field(default=None, min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")

    @model_validator(mode="after")
    def require_any_field(self) -> BankUpdate:
        if self.model_dump(exclude_none=True) == {}:
            raise ValueError("Mindestens ein Feld muss gesetzt sein")
        return self


class Bank(BaseModel):
    bank_id: UUID = Field(default_factory=uuid4)
    name: str
    bic: str
    blz: str
    country_code: str


class AccountTypeCreate(BaseModel):
    key: str = Field(min_length=2, max_length=80, pattern=r"^[a-z][a-z0-9_\-]*$")
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=600)
    schema_fields: list[AccountTypeFieldBase] = Field(default_factory=list)

    @field_validator("schema_fields")
    @classmethod
    def validate_unique_field_names(cls, value: list[AccountTypeFieldBase]) -> list[AccountTypeFieldBase]:
        names = [item.feldname for item in value]
        if len(names) != len(set(names)):
            raise ValueError("feldname muss innerhalb eines Kontotyps eindeutig sein")
        return value


class AccountTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=600)
    schema_fields: list[AccountTypeFieldBase] | None = None

    @model_validator(mode="after")
    def require_any_field(self) -> AccountTypeUpdate:
        if self.model_dump(exclude_none=True) == {}:
            raise ValueError("Mindestens ein Feld muss gesetzt sein")
        return self

    @field_validator("schema_fields")
    @classmethod
    def validate_unique_field_names(
        cls, value: list[AccountTypeFieldBase] | None
    ) -> list[AccountTypeFieldBase] | None:
        if value is None:
            return value
        names = [item.feldname for item in value]
        if len(names) != len(set(names)):
            raise ValueError("feldname muss innerhalb eines Kontotyps eindeutig sein")
        return value


class AccountType(BaseModel):
    account_type_id: UUID = Field(default_factory=uuid4)
    key: str
    name: str
    description: str | None = None
    schema_fields: list[AccountTypeFieldBase] = Field(default_factory=list)


class BankListResponse(BaseModel):
    items: list[Bank]
    total: int


class AccountTypeListResponse(BaseModel):
    items: list[AccountType]
    total: int
