from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

# Portfolio analytics models are canonical in finanzuebersicht_shared so that
# api-gateway can consume them without maintaining a parallel copy.
from finanzuebersicht_shared.models import (
    BenchmarkComponent,
    BenchmarkConfig,
    BenchmarkSuggestionReadModel,
    ChartPoint,
    ChartSeries,
    LoadingMeta,
    PortfolioAttributionItem,
    PortfolioAttributionMethodology,
    PortfolioAttributionReadModel,
    PortfolioAttributionSummary,
    PortfolioContributorItem,
    PortfolioContributorsReadModel,
    PortfolioDashboardMetaReadModel,
    PortfolioDashboardReadModel,
    PortfolioDataCoverageReadModel,
    PortfolioExposureSlice,
    PortfolioExposuresReadModel,
    PortfolioHoldingItem,
    PortfolioHoldingsReadModel,
    PortfolioPerformanceReadModel,
    PortfolioPerformanceSummary,
    PortfolioRiskReadModel,
    PortfolioSummaryReadModel,
)

__all__ = [
    # re-exported from shared
    "BenchmarkComponent",
    "BenchmarkConfig",
    "BenchmarkSuggestionReadModel",
    "ChartPoint",
    "ChartSeries",
    "LoadingMeta",
    "PortfolioAttributionItem",
    "PortfolioAttributionMethodology",
    "PortfolioAttributionReadModel",
    "PortfolioAttributionSummary",
    "PortfolioContributorItem",
    "PortfolioContributorsReadModel",
    "PortfolioDashboardMetaReadModel",
    "PortfolioDashboardReadModel",
    "PortfolioDataCoverageReadModel",
    "PortfolioExposureSlice",
    "PortfolioExposuresReadModel",
    "PortfolioHoldingItem",
    "PortfolioHoldingsReadModel",
    "PortfolioPerformanceReadModel",
    "PortfolioPerformanceSummary",
    "PortfolioRiskReadModel",
    "PortfolioSummaryReadModel",
    # analytics-service–specific
    "SummaryItem",
    "KpiBlock",
    "OverviewReadModel",
    "AllocationSlice",
    "AllocationReadModel",
    "TimeseriesReadModel",
    "MonthlyComparisonItem",
    "MonthlyComparisonReadModel",
    "MetricsReadModel",
    "HeatmapCell",
    "HeatmapReadModel",
    "ForecastPoint",
    "ForecastReadModel",
    "DashboardSectionName",
    "DashboardSectionState",
    "DashboardSectionReadModel",
]


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
