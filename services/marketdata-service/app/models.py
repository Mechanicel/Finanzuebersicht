from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class DataRange(StrEnum):
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    ONE_YEAR = "1Y"
    THREE_YEARS = "3Y"
    FIVE_YEARS = "5Y"


class DataInterval(StrEnum):
    ONE_DAY = "1d"
    ONE_WEEK = "1wk"
    ONE_MONTH = "1mo"



class InstrumentSummary(BaseModel):
    symbol: str
    isin: str | None = None
    company_name: str
    display_name: str | None = None
    wkn: str | None = None
    exchange: str
    currency: str
    quote_type: str | None = None
    asset_type: str | None = None
    country: str | None = None
    sector: str | None = None
    industry: str | None = None


class InstrumentSearchItem(BaseModel):
    symbol: str
    company_name: str
    display_name: str | None = None
    isin: str | None = None
    wkn: str | None = None
    exchange: str | None = None
    currency: str | None = None
    quote_type: str | None = None
    asset_type: str | None = None
    last_price: float | None = None
    country: str | None = None
    sector: str | None = None


class InstrumentSearchResponse(BaseModel):
    query: str
    items: list[InstrumentSearchItem]
    total: int



class InstrumentSelectionDetailsResponse(BaseModel):
    symbol: str
    isin: str | None = None
    wkn: str | None = None
    company_name: str
    display_name: str | None = None
    exchange: str
    currency: str
    quote_type: str | None = None
    asset_type: str | None = None
    last_price: float = Field(ge=0)
    change_1d_pct: float | None = None
    volume: int | None = None
    as_of: datetime | None = None


class InstrumentHydratedDocument(BaseModel):
    symbol: str
    identity: dict[str, str | None] = Field(default_factory=dict)
    summary: dict[str, object | None] = Field(default_factory=dict)
    snapshot: dict[str, object | None] = Field(default_factory=dict)
    fundamentals: dict[str, object | None] = Field(default_factory=dict)
    metrics: dict[str, object | None] = Field(default_factory=dict)
    risk: dict[str, object | None] = Field(default_factory=dict)
    provider_raw: dict[str, object | None] = Field(default_factory=dict)
    hydrated_at: datetime | None = None


class PricePoint(BaseModel):
    date: date
    close: float = Field(ge=0)


class PriceSeriesResponse(BaseModel):
    symbol: str
    currency: str
    range: DataRange
    interval: DataInterval
    points: list[PricePoint]


class BenchmarkOption(BaseModel):
    benchmark_id: str
    symbol: str
    label: str
    region: str
    asset_class: str


class BenchmarkOptionsResponse(BaseModel):
    items: list[BenchmarkOption]
    total: int


class ComparisonSeriesRequest(BaseModel):
    symbols: list[str] = Field(min_length=1, max_length=10)
    benchmark_id: str | None = None
    range: DataRange = DataRange.ONE_YEAR
    interval: DataInterval = DataInterval.ONE_DAY

    @field_validator("symbols")
    @classmethod
    def ensure_unique_symbols(cls, value: list[str]) -> list[str]:
        normalized = [item.upper() for item in value]
        if len(normalized) != len(set(normalized)):
            raise ValueError("symbols must be unique")
        return normalized


class SeriesPoint(BaseModel):
    date: date
    value: float


class ComparisonSeriesItem(BaseModel):
    series_id: str
    label: str
    kind: str
    currency: str | None = None
    points: list[SeriesPoint]


class ComparisonSeriesResponse(BaseModel):
    range: DataRange
    interval: DataInterval
    series: list[ComparisonSeriesItem]


class FundamentalsBlock(BaseModel):
    market_cap: float | None = None
    pe_ratio: float | None = None
    dividend_yield: float | None = None
    revenue_growth_yoy: float | None = None


class RiskBlock(BaseModel):
    beta: float | None = None
    volatility_30d: float | None = None
    max_drawdown_1y: float | None = None
    value_at_risk_95_1d: float | None = None


class SnapshotBlock(BaseModel):
    last_price: float
    change_1d_pct: float
    volume: int


class MetricsBlock(BaseModel):
    sma_50: float | None = None
    sma_200: float | None = None
    rsi_14: float | None = None


class InstrumentDataBlocksResponse(BaseModel):
    symbol: str
    snapshot: SnapshotBlock
    fundamentals: FundamentalsBlock
    metrics: MetricsBlock
    risk: RiskBlock


class InstrumentFullResponse(BaseModel):
    summary: InstrumentSummary
    snapshot: SnapshotBlock
    fundamentals: FundamentalsBlock
    metrics: MetricsBlock
    risk: RiskBlock


class BenchmarkSearchResponse(BaseModel):
    query: str
    items: list[BenchmarkOption]
    total: int


class CacheConfig(BaseModel):
    enabled: bool = True
    ttl_seconds: int = Field(default=60, ge=1)


class ProviderInstrumentData(BaseModel):
    summary: InstrumentSummary
    prices: list[PricePoint]
    snapshot: SnapshotBlock
    fundamentals: FundamentalsBlock
    metrics: MetricsBlock
    risk: RiskBlock


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
