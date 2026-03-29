from __future__ import annotations

from datetime import date
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


class HoldingSnapshot(BaseModel):
    date: date
    total_value: float
    holdings: dict[str, float]


class PersonSnapshots(BaseModel):
    person_id: UUID
    currency: str = "EUR"
    snapshots: list[HoldingSnapshot]
