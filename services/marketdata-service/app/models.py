from __future__ import annotations

from datetime import UTC, datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


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
