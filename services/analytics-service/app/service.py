from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, date, datetime
from statistics import mean
from time import monotonic
from uuid import UUID

import httpx

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
    SummaryItem,
    TimeseriesReadModel,
)


@dataclass(slots=True)
class DashboardData:
    person_id: UUID
    account_count: int
    depot_count: int
    holdings_count: int
    invested_value: float
    current_value: float
    allocation_by_type: dict[str, float]
    timeseries_points: list[ChartPoint]


class AnalyticsService:
    def __init__(
        self,
        *,
        person_base_url: str,
        account_base_url: str,
        portfolio_base_url: str,
        marketdata_base_url: str,
        timeout_seconds: float,
        dashboard_cache_ttl_seconds: float = 45.0,
    ) -> None:
        self._person_base_url = person_base_url.rstrip("/")
        self._account_base_url = account_base_url.rstrip("/")
        self._portfolio_base_url = portfolio_base_url.rstrip("/")
        self._marketdata_base_url = marketdata_base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._dashboard_cache_ttl_seconds = dashboard_cache_ttl_seconds
        self._dashboard_cache: dict[UUID, tuple[float, DashboardData]] = {}

    def _request_json(self, url: str, client: httpx.Client | None = None) -> dict | list[dict]:
        if client is None:
            with httpx.Client(timeout=self._timeout) as local_client:
                response = local_client.get(url)
        else:
            response = client.get(url)
        response.raise_for_status()
        return response.json()["data"]

    def _person_exists(self, person_id: UUID, client: httpx.Client | None = None) -> None:
        try:
            self._request_json(f"{self._person_base_url}/api/v1/persons/{person_id}", client=client)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise KeyError(f"Unknown person_id: {person_id}") from exc
            raise

    def _load_accounts(self, person_id: UUID, client: httpx.Client | None = None) -> list[dict]:
        payload = self._request_json(f"{self._account_base_url}/api/v1/persons/{person_id}/accounts", client=client)
        return payload if isinstance(payload, list) else []

    def _load_portfolios(self, person_id: UUID, client: httpx.Client | None = None) -> list[dict]:
        payload = self._request_json(f"{self._portfolio_base_url}/api/v1/persons/{person_id}/portfolios", client=client)
        if not isinstance(payload, dict):
            return []
        return payload.get("items", [])

    def _load_holdings(self, portfolio_id: str, client: httpx.Client | None = None) -> list[dict]:
        payload = self._request_json(f"{self._portfolio_base_url}/api/v1/portfolios/{portfolio_id}", client=client)
        if not isinstance(payload, dict):
            return []
        holdings = payload.get("holdings", [])
        return holdings if isinstance(holdings, list) else []

    def _load_price(self, symbol: str, client: httpx.Client | None = None) -> float | None:
        payload = self._request_json(
            f"{self._marketdata_base_url}/api/v1/marketdata/instruments/{symbol}/profile",
            client=client,
        )
        if not isinstance(payload, dict):
            return None
        price = payload.get("price")
        return float(price) if isinstance(price, int | float) else None

    def _load_history_points(self, symbol: str, client: httpx.Client | None = None) -> list[dict]:
        payload = self._request_json(
            f"{self._marketdata_base_url}/api/v1/marketdata/instruments/{symbol}/history?range=3m",
            client=client,
        )
        if not isinstance(payload, dict):
            return []
        points = payload.get("points", [])
        return points if isinstance(points, list) else []

    def _safe_load_price(self, symbol: str, client: httpx.Client) -> float | None:
        try:
            return self._load_price(symbol, client=client)
        except httpx.HTTPError:
            return None

    def _safe_load_history_points(self, symbol: str, client: httpx.Client) -> list[dict]:
        try:
            return self._load_history_points(symbol, client=client)
        except httpx.HTTPError:
            return []

    @staticmethod
    def _as_float(value: object) -> float:
        if isinstance(value, int | float):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return 0.0
        return 0.0

    def _build_timeseries(self, holdings: list[dict], symbol_histories: dict[str, list[dict]]) -> list[ChartPoint]:
        totals_by_day: dict[str, float] = defaultdict(float)
        for holding in holdings:
            symbol = str(holding.get("symbol", "")).upper().strip()
            quantity = self._as_float(holding.get("quantity"))
            if not symbol or quantity <= 0:
                continue
            history = symbol_histories.get(symbol, [])
            for point in history:
                day = str(point.get("date", ""))
                close = self._as_float(point.get("close"))
                if day:
                    totals_by_day[day] += close * quantity

        if not totals_by_day:
            return []

        ordered_days = sorted(totals_by_day)
        return [ChartPoint(x=day, y=round(totals_by_day[day], 2)) for day in ordered_days]

    def _build_dashboard_data(self, person_id: UUID) -> DashboardData:
        with httpx.Client(timeout=self._timeout) as client:
            self._person_exists(person_id, client=client)
            accounts = self._load_accounts(person_id, client=client)
            portfolios = self._load_portfolios(person_id, client=client)

            portfolio_ids = [
                str(portfolio.get("portfolio_id", "")).strip()
                for portfolio in portfolios
                if str(portfolio.get("portfolio_id", "")).strip()
            ]

            holdings: list[dict] = []
            if portfolio_ids:
                with ThreadPoolExecutor(max_workers=min(8, len(portfolio_ids))) as executor:
                    for portfolio_holdings in executor.map(
                        lambda pid: self._load_holdings(pid, client=client),
                        portfolio_ids,
                    ):
                        holdings.extend(portfolio_holdings)

            account_allocation: dict[str, float] = defaultdict(float)
            for account in accounts:
                account_type = str(account.get("account_type", "unknown")).lower()
                account_allocation[account_type] += self._as_float(account.get("balance"))

            symbol_sequence = [
                str(holding.get("symbol", "")).upper().strip()
                for holding in holdings
                if str(holding.get("symbol", "")).upper().strip()
            ]
            unique_symbols = list(dict.fromkeys(symbol_sequence))

            symbol_prices: dict[str, float | None] = {}
            symbol_histories: dict[str, list[dict]] = {}
            if unique_symbols:
                with ThreadPoolExecutor(max_workers=min(16, len(unique_symbols))) as executor:
                    for symbol, price in zip(
                        unique_symbols,
                        executor.map(lambda s: self._safe_load_price(s, client=client), unique_symbols),
                        strict=True,
                    ):
                        symbol_prices[symbol] = price

                with ThreadPoolExecutor(max_workers=min(16, len(unique_symbols))) as executor:
                    for symbol, history in zip(
                        unique_symbols,
                        executor.map(lambda s: self._safe_load_history_points(s, client=client), unique_symbols),
                        strict=True,
                    ):
                        symbol_histories[symbol] = history

            invested_value = 0.0
            current_value = 0.0
            for holding in holdings:
                quantity = self._as_float(holding.get("quantity"))
                acquisition_price = self._as_float(holding.get("acquisition_price"))
                symbol = str(holding.get("symbol", "")).upper().strip()
                invested_value += quantity * acquisition_price
                current_price = symbol_prices.get(symbol) if symbol else None
                current_value += quantity * (current_price if current_price is not None else acquisition_price)

            timeseries_points = self._build_timeseries(holdings, symbol_histories)

        return DashboardData(
            person_id=person_id,
            account_count=len(accounts),
            depot_count=len(portfolios),
            holdings_count=len(holdings),
            invested_value=round(invested_value, 2),
            current_value=round(current_value, 2),
            allocation_by_type=dict(account_allocation),
            timeseries_points=timeseries_points,
        )

    def _dashboard_data(self, person_id: UUID) -> DashboardData:
        now = monotonic()
        cached = self._dashboard_cache.get(person_id)
        if cached and now - cached[0] <= self._dashboard_cache_ttl_seconds:
            return cached[1]

        data = self._build_dashboard_data(person_id)
        self._dashboard_cache[person_id] = (now, data)
        return data

    def _kpis(self, data: DashboardData) -> list[KpiBlock]:
        gain = data.current_value - data.invested_value
        gain_pct = (gain / data.invested_value * 100) if data.invested_value else 0
        return [
            KpiBlock(key="accounts_count", label="Konten", value=data.account_count, unit="COUNT"),
            KpiBlock(key="depots_count", label="Depots", value=data.depot_count, unit="COUNT"),
            KpiBlock(key="holdings_count", label="Holdings", value=data.holdings_count, unit="COUNT"),
            KpiBlock(
                key="invested_portfolio_value",
                label="Investierter Depotwert",
                value=data.invested_value,
                unit="EUR",
            ),
            KpiBlock(
                key="current_portfolio_value",
                label="Aktueller Depotwert",
                value=data.current_value,
                unit="EUR",
                trend=gain,
            ),
            KpiBlock(key="portfolio_gain_percent", label="Depotrendite %", value=gain_pct, unit="PERCENT", trend=gain_pct),
        ]

    def overview(self, person_id: UUID) -> OverviewReadModel:
        data = self._dashboard_data(person_id)
        labels = [point.x for point in data.timeseries_points]
        series = [ChartSeries(key="portfolio_value", label="Depotwert", points=data.timeseries_points)]
        return OverviewReadModel(
            person_id=person_id,
            labels=labels,
            summaries=[SummaryItem(label="Aktueller Depotwert", value=data.current_value)],
            kpis=self._kpis(data),
            series=series,
        )

    def allocation(self, person_id: UUID) -> AllocationReadModel:
        data = self._dashboard_data(person_id)
        total = sum(data.allocation_by_type.values())
        slices = [
            AllocationSlice(
                label=allocation_type,
                category=allocation_type,
                value=round(value, 2),
                percentage=round((value / total * 100), 2) if total else 0,
            )
            for allocation_type, value in sorted(data.allocation_by_type.items())
        ]
        return AllocationReadModel(
            person_id=person_id,
            labels=[item.label for item in slices],
            slices=slices,
            summary=SummaryItem(label="Konten-Allokation", value=round(total, 2)),
        )

    def timeseries(self, person_id: UUID) -> TimeseriesReadModel:
        data = self._dashboard_data(person_id)
        return TimeseriesReadModel(
            person_id=person_id,
            labels=[point.x for point in data.timeseries_points],
            granularity="daily",
            series=[ChartSeries(key="portfolio_value", label="Depotwert", points=data.timeseries_points)],
            summary=SummaryItem(label="Aktueller Depotwert", value=data.current_value),
        )

    def monthly_comparison(self, person_id: UUID) -> MonthlyComparisonReadModel:
        data = self._dashboard_data(person_id)
        monthly_values: dict[str, float] = {}
        for point in data.timeseries_points:
            month = point.x[:7]
            monthly_values[month] = point.y

        bars: list[MonthlyComparisonItem] = []
        for month in sorted(monthly_values):
            current = monthly_values[month]
            previous = bars[-1].value if bars else current
            delta = current - previous
            delta_pct = (delta / previous * 100) if previous else 0
            bars.append(
                MonthlyComparisonItem(
                    month=month,
                    value=current,
                    previous_month=previous,
                    delta=round(delta, 2),
                    delta_percentage=round(delta_pct, 2),
                )
            )

        summary_value = bars[-1].delta if bars else 0
        return MonthlyComparisonReadModel(
            person_id=person_id,
            labels=[item.month for item in bars],
            bars=bars,
            summary=SummaryItem(label="Monatliche Veränderung", value=summary_value),
        )

    def metrics(self, person_id: UUID) -> MetricsReadModel:
        data = self._dashboard_data(person_id)
        series_values = [point.y for point in data.timeseries_points]
        average = mean(series_values) if series_values else 0
        band = (max(series_values) - min(series_values)) if len(series_values) > 1 else 0
        return MetricsReadModel(
            person_id=person_id,
            as_of=datetime.now(UTC).date(),
            kpis=self._kpis(data),
            summary=[
                SummaryItem(label="Durchschnittlicher Depotwert", value=round(average, 2)),
                SummaryItem(label="Bandbreite Depotwert", value=round(band, 2)),
            ],
        )

    def heatmap(self, person_id: UUID) -> HeatmapReadModel:
        data = self._dashboard_data(person_id)
        cells = [
            HeatmapCell(
                date=point.x,
                weekday=date.fromisoformat(point.x).strftime("%A"),
                hour_bucket="12:00",
                intensity=point.y,
            )
            for point in data.timeseries_points
        ]
        return HeatmapReadModel(
            person_id=person_id,
            labels=["date", "weekday", "hour_bucket", "intensity"],
            cells=cells,
            summary=SummaryItem(label="Heatmap-Zellen", value=float(len(cells))),
        )

    def forecast(self, person_id: UUID) -> ForecastReadModel:
        data = self._dashboard_data(person_id)
        values = [point.y for point in data.timeseries_points]
        deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
        avg_delta = mean(deltas) if deltas else 0
        running = values[-1] if values else data.current_value
        start_date = datetime.now(UTC).date()

        points: list[ForecastPoint] = []
        for step in range(1, 4):
            month = ((start_date.month + step - 1) % 12) + 1
            year = start_date.year + ((start_date.month + step - 1) // 12)
            running += avg_delta
            points.append(
                ForecastPoint(
                    month=f"{year}-{month:02d}",
                    forecast_value=round(running, 2),
                    lower_bound=round(running * 0.97, 2),
                    upper_bound=round(running * 1.03, 2),
                )
            )

        summary_value = points[-1].forecast_value if points else 0
        return ForecastReadModel(
            person_id=person_id,
            labels=[point.month for point in points],
            horizon_months=len(points),
            points=points,
            summary=SummaryItem(label="Forecast letzter Punkt", value=summary_value),
        )
