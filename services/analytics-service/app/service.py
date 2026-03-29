from __future__ import annotations

from collections import defaultdict
from datetime import date
from statistics import mean
from uuid import UUID

from app.models import (
    AllocationReadModel,
    AllocationSlice,
    ChartPoint,
    ChartSeries,
    ForecastPoint,
    ForecastReadModel,
    HeatmapCell,
    HeatmapReadModel,
    KpiBlock,
    MetricsReadModel,
    MonthlyComparisonItem,
    MonthlyComparisonReadModel,
    OverviewReadModel,
    PersonSnapshots,
    SummaryItem,
    TimeseriesReadModel,
)


class AnalyticsService:
    def __init__(self, snapshots_by_person: dict[UUID, PersonSnapshots]) -> None:
        self._snapshots_by_person = snapshots_by_person

    def _person_data(self, person_id: UUID) -> PersonSnapshots:
        if person_id not in self._snapshots_by_person:
            raise KeyError(f"Unknown person_id: {person_id}")
        return self._snapshots_by_person[person_id]

    def overview(self, person_id: UUID) -> OverviewReadModel:
        person = self._person_data(person_id)
        labels = [s.date.isoformat() for s in person.snapshots]
        wealth_points = [
            ChartPoint(x=s.date.isoformat(), y=s.total_value) for s in person.snapshots
        ]
        latest = person.snapshots[-1].total_value
        first = person.snapshots[0].total_value
        growth = latest - first
        growth_pct = (growth / first * 100) if first else 0

        return OverviewReadModel(
            person_id=person_id,
            labels=labels,
            summaries=[SummaryItem(label="Total Wealth", value=latest)],
            kpis=[
                KpiBlock(key="total_wealth", label="Gesamtvermögen", value=latest, unit="EUR"),
                KpiBlock(
                    key="growth_absolute",
                    label="Wachstum absolut",
                    value=growth,
                    unit="EUR",
                    trend=growth,
                ),
                KpiBlock(
                    key="growth_percent",
                    label="Wachstum %",
                    value=growth_pct,
                    unit="PERCENT",
                    trend=growth_pct,
                ),
            ],
            series=[ChartSeries(key="wealth", label="Gesamtvermögen", points=wealth_points)],
        )

    def allocation(self, person_id: UUID) -> AllocationReadModel:
        person = self._person_data(person_id)
        latest = person.snapshots[-1]
        total = latest.total_value
        slices = [
            AllocationSlice(
                label=category,
                category=category,
                value=value,
                percentage=(value / total * 100) if total else 0,
            )
            for category, value in latest.holdings.items()
        ]
        labels = [item.label for item in slices]
        return AllocationReadModel(
            person_id=person_id,
            labels=labels,
            slices=slices,
            summary=SummaryItem(label="Allokiertes Gesamtvermögen", value=total),
        )

    def timeseries(self, person_id: UUID) -> TimeseriesReadModel:
        person = self._person_data(person_id)
        labels = [s.date.isoformat() for s in person.snapshots]
        totals = [ChartPoint(x=s.date.isoformat(), y=s.total_value) for s in person.snapshots]
        return TimeseriesReadModel(
            person_id=person_id,
            labels=labels,
            granularity="monthly",
            series=[ChartSeries(key="net_worth", label="Net Worth", points=totals)],
            summary=SummaryItem(label="Aktueller Stand", value=person.snapshots[-1].total_value),
        )

    def monthly_comparison(self, person_id: UUID) -> MonthlyComparisonReadModel:
        person = self._person_data(person_id)
        bars: list[MonthlyComparisonItem] = []
        for index, snapshot in enumerate(person.snapshots):
            previous = (
                person.snapshots[index - 1].total_value if index > 0 else snapshot.total_value
            )
            delta = snapshot.total_value - previous
            delta_pct = (delta / previous * 100) if previous else 0
            bars.append(
                MonthlyComparisonItem(
                    month=snapshot.date.strftime("%Y-%m"),
                    value=snapshot.total_value,
                    previous_month=previous,
                    delta=delta,
                    delta_percentage=delta_pct,
                )
            )

        return MonthlyComparisonReadModel(
            person_id=person_id,
            labels=[item.month for item in bars],
            bars=bars,
            summary=SummaryItem(label="Monatlicher Vergleich letzter Monat", value=bars[-1].delta),
        )

    def metrics(self, person_id: UUID) -> MetricsReadModel:
        person = self._person_data(person_id)
        values = [snapshot.total_value for snapshot in person.snapshots]
        latest = values[-1]
        avg = mean(values)
        volatility = max(values) - min(values)

        return MetricsReadModel(
            person_id=person_id,
            as_of=date.fromisoformat(person.snapshots[-1].date.isoformat()),
            kpis=[
                KpiBlock(key="wealth_latest", label="Aktuelles Vermögen", value=latest, unit="EUR"),
                KpiBlock(key="wealth_average", label="Durchschnitt", value=avg, unit="EUR"),
                KpiBlock(key="wealth_volatility", label="Bandbreite", value=volatility, unit="EUR"),
            ],
            summary=[
                SummaryItem(label="Average Wealth", value=avg),
                SummaryItem(label="Volatility", value=volatility),
            ],
        )

    def heatmap(self, person_id: UUID) -> HeatmapReadModel:
        person = self._person_data(person_id)
        cells: list[HeatmapCell] = []
        for snapshot in person.snapshots:
            distribution = defaultdict(float)
            for value in snapshot.holdings.values():
                distribution["12:00"] += value / max(len(snapshot.holdings), 1)
            for hour_bucket, intensity in distribution.items():
                cells.append(
                    HeatmapCell(
                        date=snapshot.date.isoformat(),
                        weekday=snapshot.date.strftime("%A"),
                        hour_bucket=hour_bucket,
                        intensity=round(intensity, 2),
                    )
                )

        return HeatmapReadModel(
            person_id=person_id,
            labels=["date", "weekday", "hour_bucket", "intensity"],
            cells=cells,
            summary=SummaryItem(label="Heatmap-Zellen", value=float(len(cells))),
        )

    def forecast(self, person_id: UUID) -> ForecastReadModel:
        person = self._person_data(person_id)
        values = [snapshot.total_value for snapshot in person.snapshots]
        deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
        avg_delta = mean(deltas) if deltas else 0
        last_month = person.snapshots[-1].date
        points: list[ForecastPoint] = []
        running = values[-1]
        for step in range(1, 4):
            month = (last_month.month + step - 1) % 12 + 1
            year = last_month.year + ((last_month.month + step - 1) // 12)
            running += avg_delta
            points.append(
                ForecastPoint(
                    month=f"{year}-{month:02d}",
                    forecast_value=round(running, 2),
                    lower_bound=round(running * 0.97, 2),
                    upper_bound=round(running * 1.03, 2),
                )
            )

        return ForecastReadModel(
            person_id=person_id,
            labels=[point.month for point in points],
            horizon_months=len(points),
            points=points,
            summary=SummaryItem(label="Forecast letzter Punkt", value=points[-1].forecast_value),
        )
