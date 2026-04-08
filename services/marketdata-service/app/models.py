from __future__ import annotations

from datetime import UTC, datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from typing import Literal


class InstrumentSearchItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    symbol: str
    company_name: str
    display_name: str
    currency: str | None = None
    exchange: str | None = None
    exchange_full_name: str | None = None


class InstrumentSearchResponse(BaseModel):
    query: str
    items: list[InstrumentSearchItem]
    total: int


class InstrumentProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    symbol: str
    company_name: str = Field(validation_alias=AliasChoices("companyName", "company_name"))
    price: float | None = None
    currency: str | None = None
    isin: str | None = None
    exchange: str | None = None
    exchange_full_name: str | None = Field(default=None, validation_alias=AliasChoices("exchangeFullName", "exchange_full_name"))
    industry: str | None = None
    website: str | None = None
    description: str | None = None
    ceo: str | None = None
    sector: str | None = None
    country: str | None = None
    phone: str | None = None
    image: str | None = None
    address: str | None = None
    city: str | None = None
    zip: str | None = None
    address_line: str | None = None


class PersistenceOnlyInstrumentProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ipo_date: str | None = Field(default=None, validation_alias=AliasChoices("ipoDate", "ipo_date"))
    default_image: bool | None = Field(default=None, validation_alias=AliasChoices("defaultImage", "default_image"))
    is_etf: bool | None = Field(default=None, validation_alias=AliasChoices("isEtf", "is_etf"))
    is_actively_trading: bool | None = Field(default=None, validation_alias=AliasChoices("isActivelyTrading", "is_actively_trading"))
    is_adr: bool | None = Field(default=None, validation_alias=AliasChoices("isAdr", "is_adr"))
    is_fund: bool | None = Field(default=None, validation_alias=AliasChoices("isFund", "is_fund"))
    market_cap: float | None = Field(default=None, validation_alias=AliasChoices("marketCap", "mktCap"))
    beta: float | None = None
    last_dividend: float | None = Field(default=None, validation_alias=AliasChoices("lastDividend", "lastDiv"))
    range: str | None = None
    change: float | None = Field(default=None, validation_alias=AliasChoices("change", "changes"))
    change_percentage: float | str | None = Field(default=None, validation_alias=AliasChoices("changePercentage", "changesPercentage"))
    volume: float | None = None
    average_volume: float | None = Field(default=None, validation_alias=AliasChoices("averageVolume", "volAvg"))
    cusip: str | None = None


class FMPInstrumentProfile(InstrumentProfile, PersistenceOnlyInstrumentProfile):
    pass


class CachedInstrumentProfile(BaseModel):
    symbol: str
    source: str
    visible_profile: InstrumentProfile
    persistence_only_profile: PersistenceOnlyInstrumentProfile
    fetched_at: datetime


class InstrumentPriceRefreshResponse(BaseModel):
    symbol: str
    trade_date: str
    current_price: float
    price_source: Literal["cache_today", "yfinance_1d_1m"]
    price_cache_hit: bool
    history_cache_present: bool
    history_action: Literal["seed_max_in_background", "enrich_in_background"]
    fetched_at: datetime


class CurrentPriceCacheDocument(BaseModel):
    symbol: str
    trade_date: str
    current_price: float
    source: Literal["yfinance_1d_1m"]
    fetched_at: datetime


class PriceHistoryRow(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class PriceHistoryCacheDocument(BaseModel):
    symbol: str
    interval: Literal["1d"]
    period_seeded: Literal["max"]
    history_rows: list[PriceHistoryRow]
    first_date: str
    last_date: str
    updated_at: datetime


HistoryRange = Literal["1m", "3m", "6m", "ytd", "1y", "max"]


class InstrumentHistoryPoint(BaseModel):
    date: str
    close: float


class InstrumentHistoryResponse(BaseModel):
    symbol: str
    range: HistoryRange
    currency: str | None = None
    points: list[InstrumentHistoryPoint]
    cache_present: bool
    updated_at: datetime


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
