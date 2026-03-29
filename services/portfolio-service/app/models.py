from __future__ import annotations

from datetime import date, datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


ISIN_PATTERN = r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$"


class ResponseMode(StrEnum):
    COMPACT = "compact"
    DETAILED = "detailed"


class HoldingInput(BaseModel):
    isin: str = Field(min_length=12, max_length=12, pattern=ISIN_PATTERN)
    quantity: float = Field(gt=0)
    instrument_name: str | None = Field(default=None, max_length=200)

    @field_validator("isin")
    @classmethod
    def normalize_isin(cls, value: str) -> str:
        return value.strip().upper()


class HoldingsReplaceRequest(BaseModel):
    holdings: list[HoldingInput] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_duplicates(self) -> HoldingsReplaceRequest:
        seen: set[str] = set()
        for item in self.holdings:
            if item.isin in seen:
                raise ValueError(f"Doppelte ISIN im Holdings-Update: {item.isin}")
            seen.add(item.isin)
        return self


class SnapshotCreateRequest(BaseModel):
    snapshot_date: date
    note: str | None = Field(default=None, max_length=500)
    holdings: list[HoldingInput] = Field(min_length=1)

    @field_validator("snapshot_date")
    @classmethod
    def ensure_date_not_too_old(cls, value: date) -> date:
        if value.year < 1970:
            raise ValueError("snapshot_date muss >= 1970 sein")
        return value

    @model_validator(mode="after")
    def validate_duplicates(self) -> SnapshotCreateRequest:
        seen: set[str] = set()
        for item in self.holdings:
            if item.isin in seen:
                raise ValueError(f"Doppelte ISIN im Snapshot: {item.isin}")
            seen.add(item.isin)
        return self


class Holding(BaseModel):
    holding_id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    account_id: UUID
    isin: str
    quantity: float = Field(gt=0)
    instrument_name: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HoldingsSummary(BaseModel):
    holdings_count: int = Field(ge=0)
    total_quantity_summary: float = Field(ge=0)


class SnapshotSummary(BaseModel):
    snapshot_id: UUID
    snapshot_date: date
    holdings_count: int = Field(ge=0)
    total_quantity_summary: float = Field(ge=0)
    created_at: datetime


class HoldingSnapshot(BaseModel):
    snapshot_id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    account_id: UUID
    snapshot_date: date
    note: str | None = None
    holdings: list[HoldingInput]
    holdings_count: int = Field(ge=0)
    total_quantity_summary: float = Field(ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AccountSummary(BaseModel):
    account_id: UUID
    holdings_count: int = Field(ge=0)
    total_quantity_summary: float = Field(ge=0)


class Portfolio(BaseModel):
    portfolio_id: UUID = Field(default_factory=uuid4)
    account_id: UUID
    display_name: str
    account_summary: AccountSummary
    holdings_count: int = Field(ge=0)
    total_quantity_summary: float = Field(ge=0)
    latest_snapshot_summary: SnapshotSummary | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HoldingsResponse(BaseModel):
    portfolio_id: UUID
    account_id: UUID
    display_name: str
    holdings_count: int = Field(ge=0)
    total_quantity_summary: float = Field(ge=0)
    holdings: list[HoldingInput]


class PortfolioDetailResponse(BaseModel):
    portfolio_id: UUID
    account_id: UUID
    display_name: str
    account_summary: AccountSummary
    holdings_count: int = Field(ge=0)
    total_quantity_summary: float = Field(ge=0)
    latest_snapshot_summary: SnapshotSummary | None = None
    holdings: list[HoldingInput] | None = None
    snapshots: list[SnapshotSummary] | None = None


class SnapshotsResponse(BaseModel):
    account_id: UUID
    portfolio_id: UUID
    display_name: str
    latest_snapshot_summary: SnapshotSummary | None = None
    snapshots: list[HoldingSnapshot]
