from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class InstrumentSearchItem(BaseModel):
    symbol: str
    name: str
    currency: str | None = None
    exchange: str | None = None
    exchange_short_name: str | None = None
    instrument_type: str | None = Field(default=None, alias="type")


class InstrumentSearchResponse(BaseModel):
    query: str
    items: list[InstrumentSearchItem]
    total: int


class InstrumentProfile(BaseModel):
    symbol: str
    company_name: str
    currency: str | None = None
    exchange: str | None = None
    exchange_short_name: str | None = None
    industry: str | None = None
    sector: str | None = None
    country: str | None = None
    description: str | None = None
    website: str | None = None
    image: str | None = None
    market_cap: float | None = None
    price: float | None = None
    beta: float | None = None
    as_of: datetime | None = None


class CachedInstrumentProfile(BaseModel):
    profile: InstrumentProfile
    fetched_at: datetime


class NotFoundError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class BadRequestError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class UpstreamServiceError(Exception):
    def __init__(self, message: str = "Market data provider temporarily unavailable") -> None:
        self.message = message
        super().__init__(message)


def utcnow() -> datetime:
    return datetime.now(UTC)
