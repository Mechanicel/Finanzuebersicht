from __future__ import annotations

from datetime import date, datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

from finanzuebersicht_shared.base_models import SharedModel


class ErrorDetail(SharedModel):
    code: str
    message: str
    field: str | None = None


class ErrorResponse(SharedModel):
    error: str
    request_id: str | None = None
    details: list[ErrorDetail] = Field(default_factory=list)


class HealthResponse(SharedModel):
    status: str
    service: str
    version: str
    timestamp: datetime


T = TypeVar("T")


class ApiResponse(SharedModel, Generic[T]):
    data: T
    request_id: str | None = None
    correlation_id: str | None = None


# ---------------------------------------------------------------------------
# Portfolio analytics shared models
# Produced by analytics-service, consumed by api-gateway.
# Keeping them here eliminates manual synchronisation between the two.
# ---------------------------------------------------------------------------

class LoadingMeta(BaseModel):
    loading: bool = False
    error: str | None = None
    generated_at: datetime | None = None


class ChartPoint(BaseModel):
    x: str
    y: float


class ChartSeries(BaseModel):
    key: str
    label: str
    points: list[ChartPoint]


class PortfolioSummaryReadModel(BaseModel):
    person_id: UUID
    as_of: date
    summary_kind: str = "snapshot"
    return_basis: str = "since_cost_basis"
    currency: str = "EUR"
    market_value: float
    invested_value: float
    unrealized_pnl: float
    unrealized_return_pct: float | None = None
    portfolios_count: int
    holdings_count: int
    top_position_weight: float | None = None
    top3_weight: float | None = None
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


class PortfolioPerformanceSummary(BaseModel):
    summary_kind: str = "range"
    return_basis: str = "range_start_value"
    start_value: float | None = None
    end_value: float | None = None
    absolute_change: float | None = None
    return_pct: float | None = None


class PortfolioPerformanceReadModel(BaseModel):
    person_id: UUID
    range: str
    range_label: str | None = None
    benchmark_symbol: str | None = None
    series: list[ChartSeries] = Field(default_factory=list)
    summary: PortfolioPerformanceSummary
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


class PortfolioExposureSlice(BaseModel):
    label: str
    market_value: float
    weight: float


class PortfolioExposuresReadModel(BaseModel):
    person_id: UUID
    by_position: list[PortfolioExposureSlice] = Field(default_factory=list)
    by_sector: list[PortfolioExposureSlice] = Field(default_factory=list)
    by_country: list[PortfolioExposureSlice] = Field(default_factory=list)
    by_currency: list[PortfolioExposureSlice] = Field(default_factory=list)
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


class PortfolioHoldingItem(BaseModel):
    portfolio_id: str
    portfolio_name: str | None = None
    holding_id: str | None = None
    symbol: str | None = None
    display_name: str | None = None
    quantity: float
    acquisition_price: float | None = None
    current_price: float | None = None
    invested_value: float
    market_value: float
    unrealized_pnl: float
    unrealized_return_pct: float | None = None
    weight: float
    sector: str | None = None
    country: str | None = None
    currency: str | None = None
    data_status: str
    warnings: list[str] = Field(default_factory=list)


class PortfolioHoldingsReadModel(BaseModel):
    person_id: UUID
    as_of: date
    currency: str = "EUR"
    items: list[PortfolioHoldingItem] = Field(default_factory=list)
    summary: PortfolioSummaryReadModel
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


class PortfolioRiskReadModel(BaseModel):
    person_id: UUID
    as_of: date
    range: str = "3m"
    range_label: str | None = None
    methodology: str = "daily_returns_on_range"
    benchmark_relation: str = "relative_to_benchmark"
    benchmark_symbol: str | None = None
    portfolio_volatility: float | None = None
    max_drawdown: float | None = None
    correlation: float | None = None
    beta: float | None = None
    tracking_error: float | None = None
    annualized_volatility: float | None = None
    annualized_tracking_error: float | None = None
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    information_ratio: float | None = None
    active_return: float | None = None
    best_day_return: float | None = None
    worst_day_return: float | None = None
    aligned_points: int | None = None
    top_position_weight: float | None = None
    top3_weight: float | None = None
    concentration_note: str | None = None
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


class PortfolioContributorItem(BaseModel):
    symbol: str | None = None
    display_name: str | None = None
    market_value: float
    weight: float
    unrealized_pnl: float
    contribution_weighted: float
    direction: str | None = None
    contribution_return: float | None = None
    contribution_pct_points: float | None = None
    periods_used: int = 0
    history_available: bool = False


class PortfolioContributorsReadModel(BaseModel):
    person_id: UUID
    as_of: date | None = None
    range: str = "3m"
    range_label: str | None = None
    summary_kind: str = "range"
    return_basis: str = "range_contribution"
    methodology: str = "static_quantity_return_contribution"
    total_contribution_return: float | None = None
    total_contribution_pct_points: float | None = None
    warnings: list[str] = Field(default_factory=list)
    top_contributors: list[PortfolioContributorItem] = Field(default_factory=list)
    top_detractors: list[PortfolioContributorItem] = Field(default_factory=list)
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


class PortfolioAttributionMethodology(BaseModel):
    key: str = "holdings_based_static_return_contribution"
    label: str = "Holdings-based static return contribution"
    description: str = (
        "Uses current portfolio holdings with static quantities and instrument price history over the selected range. "
        "Contributions are additive percentage-point return contributions."
    )
    contribution_basis: str = "return contribution over selected range"
    contribution_unit: str = "percentage_points"


class PortfolioAttributionSummary(BaseModel):
    portfolio_return_pct: float | None = None
    total_contribution_pct_points: float = 0.0
    residual_pct_points: float | None = None
    covered_positions: int = 0
    total_positions: int = 0
    unattributed_positions: int = 0


class PortfolioAttributionItem(BaseModel):
    label: str
    contribution_pct_points: float
    return_pct: float | None = None
    weight: float | None = None
    market_value: float | None = None
    direction: str | None = None
    symbol: str | None = None


class PortfolioAttributionReadModel(BaseModel):
    person_id: UUID
    as_of: date
    range: str = "3m"
    range_label: str | None = None
    benchmark_symbol: str | None = None
    methodology: PortfolioAttributionMethodology = Field(default_factory=PortfolioAttributionMethodology)
    summary: PortfolioAttributionSummary = Field(default_factory=PortfolioAttributionSummary)
    by_position: list[PortfolioAttributionItem] = Field(default_factory=list)
    by_sector: list[PortfolioAttributionItem] = Field(default_factory=list)
    by_country: list[PortfolioAttributionItem] = Field(default_factory=list)
    by_currency: list[PortfolioAttributionItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


class PortfolioDataCoverageReadModel(BaseModel):
    person_id: UUID
    as_of: date
    total_holdings: int
    missing_prices: int
    missing_sectors: int
    missing_countries: int
    missing_currencies: int
    fallback_acquisition_prices: int = 0
    holdings_with_marketdata_warnings: int = 0
    warnings: list[str] = Field(default_factory=list)
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


class PortfolioDashboardMetaReadModel(LoadingMeta):
    warnings: list[str] = Field(default_factory=list)


class PortfolioDashboardReadModel(BaseModel):
    person_id: UUID
    as_of: date
    range: str
    benchmark_symbol: str | None = None
    summary: PortfolioSummaryReadModel
    performance: PortfolioPerformanceReadModel
    exposures: PortfolioExposuresReadModel
    holdings: PortfolioHoldingsReadModel
    risk: PortfolioRiskReadModel
    coverage: PortfolioDataCoverageReadModel
    contributors: PortfolioContributorsReadModel
    attribution: PortfolioAttributionReadModel | None = None
    meta: PortfolioDashboardMetaReadModel = Field(default_factory=PortfolioDashboardMetaReadModel)
