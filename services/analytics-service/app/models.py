from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChartPoint(BaseModel):
    x: str
    y: float


class ChartSeries(BaseModel):
    key: str
    label: str
    points: list[ChartPoint]


class SummaryItem(BaseModel):
    label: str
    value: float
    currency: str = "EUR"


class KpiBlock(BaseModel):
    key: str
    label: str
    value: float
    unit: str
    trend: float | None = None


class LoadingMeta(BaseModel):
    loading: bool = False
    error: str | None = None
    generated_at: datetime | None = None



class OverviewReadModel(BaseModel):
    person_id: UUID
    labels: list[str]
    summaries: list[SummaryItem]
    kpis: list[KpiBlock]
    series: list[ChartSeries]
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


class AllocationSlice(BaseModel):
    label: str
    category: str
    value: float
    percentage: float


class AllocationReadModel(BaseModel):
    person_id: UUID
    labels: list[str]
    slices: list[AllocationSlice]
    summary: SummaryItem
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


class TimeseriesReadModel(BaseModel):
    person_id: UUID
    labels: list[str]
    granularity: str
    series: list[ChartSeries]
    summary: SummaryItem
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


class MonthlyComparisonItem(BaseModel):
    month: str
    value: float
    previous_month: float
    delta: float
    delta_percentage: float


class MonthlyComparisonReadModel(BaseModel):
    person_id: UUID
    labels: list[str]
    bars: list[MonthlyComparisonItem]
    summary: SummaryItem
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


class MetricsReadModel(BaseModel):
    person_id: UUID
    as_of: date
    kpis: list[KpiBlock]
    summary: list[SummaryItem]
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


class HeatmapCell(BaseModel):
    date: str
    weekday: str
    hour_bucket: str
    intensity: float


class HeatmapReadModel(BaseModel):
    person_id: UUID
    labels: list[str]
    cells: list[HeatmapCell]
    summary: SummaryItem
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


class ForecastPoint(BaseModel):
    month: str
    forecast_value: float
    lower_bound: float
    upper_bound: float


class ForecastReadModel(BaseModel):
    person_id: UUID
    labels: list[str]
    horizon_months: int
    points: list[ForecastPoint]
    summary: SummaryItem
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


DashboardSectionName = Literal["overview", "allocation", "timeseries", "metrics"]
DashboardSectionState = Literal["ready", "stale", "pending", "error"]


class DashboardSectionReadModel(BaseModel):
    person_id: UUID
    section: DashboardSectionName
    state: DashboardSectionState
    generated_at: datetime | None = None
    stale_at: datetime | None = None
    refresh_in_progress: bool = False
    warnings: list[str] = Field(default_factory=list)
    payload: dict[str, Any]


class PortfolioSummaryReadModel(BaseModel):
    person_id: UUID
    as_of: date
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


class PortfolioPerformancePoint(BaseModel):
    date: str
    value: float


class PortfolioPerformanceSummary(BaseModel):
    start_value: float | None = None
    end_value: float | None = None
    absolute_change: float | None = None
    return_pct: float | None = None


class PortfolioPerformanceReadModel(BaseModel):
    person_id: UUID
    range: str
    benchmark_symbol: str | None = None
    series: list[ChartSeries]
    summary: PortfolioPerformanceSummary
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


class PortfolioExposureSlice(BaseModel):
    label: str
    market_value: float
    weight: float


class PortfolioExposuresReadModel(BaseModel):
    person_id: UUID
    by_position: list[PortfolioExposureSlice]
    by_sector: list[PortfolioExposureSlice]
    by_country: list[PortfolioExposureSlice]
    by_currency: list[PortfolioExposureSlice]
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
    items: list[PortfolioHoldingItem]
    summary: PortfolioSummaryReadModel
    meta: LoadingMeta = Field(default_factory=LoadingMeta)


class PortfolioRiskReadModel(BaseModel):
    person_id: UUID
    as_of: date
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
    as_of: date
    range: str = "3m"
    methodology: str = "static_quantity_return_contribution"
    total_contribution_return: float | None = None
    total_contribution_pct_points: float | None = None
    warnings: list[str] = Field(default_factory=list)
    top_contributors: list[PortfolioContributorItem]
    top_detractors: list[PortfolioContributorItem]
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
    meta: PortfolioDashboardMetaReadModel = Field(default_factory=PortfolioDashboardMetaReadModel)
