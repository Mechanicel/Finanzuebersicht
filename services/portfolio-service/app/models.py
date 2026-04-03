from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class PortfolioCreatePayload(BaseModel):
    person_id: UUID
    display_name: str = Field(min_length=1, max_length=150)

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("display_name darf nicht leer sein")
        return cleaned


class HoldingCreatePayload(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    isin: str | None = Field(default=None, min_length=12, max_length=12)
    wkn: str | None = Field(default=None, min_length=6, max_length=6)
    company_name: str | None = Field(default=None, max_length=200)
    display_name: str | None = Field(default=None, max_length=200)
    quantity: float = Field(gt=0)
    acquisition_price: float = Field(gt=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    buy_date: date
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("isin")
    @classmethod
    def normalize_isin(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value

    @field_validator("wkn")
    @classmethod
    def normalize_wkn(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("company_name", "display_name", "notes")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class HoldingUpdatePayload(BaseModel):
    quantity: float | None = Field(default=None, gt=0)
    acquisition_price: float | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    buy_date: date | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class Holding(BaseModel):
    holding_id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    symbol: str
    isin: str | None = None
    wkn: str | None = None
    company_name: str | None = None
    display_name: str | None = None
    quantity: float = Field(gt=0)
    acquisition_price: float = Field(gt=0)
    currency: str
    buy_date: date
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Portfolio(BaseModel):
    portfolio_id: UUID = Field(default_factory=uuid4)
    person_id: UUID
    display_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PortfolioDetailResponse(BaseModel):
    portfolio_id: UUID
    person_id: UUID
    display_name: str
    created_at: datetime
    updated_at: datetime
    holdings: list[Holding] = Field(default_factory=list)


class PortfolioListResponse(BaseModel):
    items: list[Portfolio]
    total: int


class HoldingsRefreshStubResponse(BaseModel):
    portfolio_id: UUID
    status: str
    accepted: bool
    detail: str
