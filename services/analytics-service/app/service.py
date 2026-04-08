from __future__ import annotations

from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from statistics import mean
from threading import Lock
from uuid import UUID

import httpx

from app.models import (
    AllocationReadModel,
    AllocationSlice,
    ChartPoint,
    ChartSeries,
    DashboardSectionName,
    DashboardSectionReadModel,
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


@dataclass(slots=True)
class SectionCacheEntry:
    payload: dict
    generated_at: datetime | None = None
    stale_at: datetime | None = None
    refresh_in_progress: bool = False
    warnings: list[str] = field(default_factory=list)
    has_error: bool = False


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
        section_refresh_workers: int = 8,
    ) -> None:
        self._person_base_url = person_base_url.rstrip("/")
        self._account_base_url = account_base_url.rstrip("/")
        self._portfolio_base_url = portfolio_base_url.rstrip("/")
        self._marketdata_base_url = marketdata_base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._dashboard_cache_ttl_seconds = dashboard_cache_ttl_seconds
        self._section_cache: dict[tuple[UUID, DashboardSectionName], SectionCacheEntry] = {}
        self._cache_lock = Lock()
        self._refresh_executor = ThreadPoolExecutor(max_workers=max(1, section_refresh_workers))
        self._known_persons: set[UUID] = set()
        self._unknown_persons: set[UUID] = set()

    def _request_json(self, url: str, client: httpx.Client | None = None) -> dict | list[dict]:
        if client is None:
            with httpx.Client(timeout=self._timeout) as local_client:
                response = local_client.get(url)
        else:
            response = client.get(url)
        response.raise_for_status()
        return response.json()["data"]

    def _person_exists(self, person_id: UUID, client: httpx.Client | None = None) -> None:
        if person_id in self._known_persons:
            return
        if person_id in self._unknown_persons:
            raise KeyError(f"Unknown person_id: {person_id}")
        try:
            self._request_json(f"{self._person_base_url}/api/v1/persons/{person_id}", client=client)
            self._known_persons.add(person_id)
            self._unknown_persons.discard(person_id)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                self._unknown_persons.add(person_id)
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
        return self._build_dashboard_data(person_id)

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

    def _build_overview_payload(self, person_id: UUID, data: DashboardData) -> dict:
        model = OverviewReadModel(
            person_id=person_id,
            labels=[point.x for point in data.timeseries_points],
            summaries=[SummaryItem(label="Aktueller Depotwert", value=data.current_value)],
            kpis=self._kpis(data),
            series=[ChartSeries(key="portfolio_value", label="Depotwert", points=data.timeseries_points)],
        )
        return model.model_dump(mode="json")

    def _build_allocation_payload(self, person_id: UUID, data: DashboardData) -> dict:
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
        model = AllocationReadModel(
            person_id=person_id,
            labels=[item.label for item in slices],
            slices=slices,
            summary=SummaryItem(label="Konten-Allokation", value=round(total, 2)),
        )
        return model.model_dump(mode="json")

    def _build_timeseries_payload(self, person_id: UUID, data: DashboardData) -> dict:
        model = TimeseriesReadModel(
            person_id=person_id,
            labels=[point.x for point in data.timeseries_points],
            granularity="daily",
            series=[ChartSeries(key="portfolio_value", label="Depotwert", points=data.timeseries_points)],
            summary=SummaryItem(label="Aktueller Depotwert", value=data.current_value),
        )
        return model.model_dump(mode="json")

    def _build_metrics_payload(self, person_id: UUID, data: DashboardData) -> dict:
        series_values = [point.y for point in data.timeseries_points]
        average = mean(series_values) if series_values else 0
        band = (max(series_values) - min(series_values)) if len(series_values) > 1 else 0
        model = MetricsReadModel(
            person_id=person_id,
            as_of=datetime.now(UTC).date(),
            kpis=self._kpis(data),
            summary=[
                SummaryItem(label="Durchschnittlicher Depotwert", value=round(average, 2)),
                SummaryItem(label="Bandbreite Depotwert", value=round(band, 2)),
            ],
        )
        return model.model_dump(mode="json")

    def _build_section_payload(self, person_id: UUID, section: DashboardSectionName) -> dict:
        data = self._build_dashboard_data(person_id)
        if section == "overview":
            return self._build_overview_payload(person_id, data)
        if section == "allocation":
            return self._build_allocation_payload(person_id, data)
        if section == "timeseries":
            return self._build_timeseries_payload(person_id, data)
        if section == "metrics":
            return self._build_metrics_payload(person_id, data)
        raise ValueError(f"Unsupported section: {section}")

    def _empty_section_payload(self, person_id: UUID, section: DashboardSectionName) -> dict:
        if section == "overview":
            return self._build_overview_payload(
                person_id,
                DashboardData(person_id, 0, 0, 0, 0.0, 0.0, {}, []),
            )
        if section == "allocation":
            return self._build_allocation_payload(
                person_id,
                DashboardData(person_id, 0, 0, 0, 0.0, 0.0, {}, []),
            )
        if section == "timeseries":
            return self._build_timeseries_payload(
                person_id,
                DashboardData(person_id, 0, 0, 0, 0.0, 0.0, {}, []),
            )
        if section == "metrics":
            return self._build_metrics_payload(
                person_id,
                DashboardData(person_id, 0, 0, 0, 0.0, 0.0, {}, []),
            )
        raise ValueError(f"Unsupported section: {section}")

    def _cache_key(self, person_id: UUID, section: DashboardSectionName) -> tuple[UUID, DashboardSectionName]:
        return (person_id, section)

    def _trigger_background_refresh(self, person_id: UUID, section: DashboardSectionName) -> Future | None:
        key = self._cache_key(person_id, section)
        with self._cache_lock:
            entry = self._section_cache.get(key)
            if entry is None:
                entry = SectionCacheEntry(payload=self._empty_section_payload(person_id, section))
                self._section_cache[key] = entry
            if entry.refresh_in_progress:
                return None
            entry.refresh_in_progress = True
        return self._refresh_executor.submit(self._refresh_section_cache, person_id, section)

    def _refresh_section_cache(self, person_id: UUID, section: DashboardSectionName) -> None:
        key = self._cache_key(person_id, section)
        try:
            self._person_exists(person_id)
            payload = self._build_section_payload(person_id, section)
            now = datetime.now(UTC)
            with self._cache_lock:
                self._section_cache[key] = SectionCacheEntry(
                    payload=payload,
                    generated_at=now,
                    stale_at=now + timedelta(seconds=self._dashboard_cache_ttl_seconds),
                    refresh_in_progress=False,
                    warnings=[],
                    has_error=False,
                )
        except KeyError:
            with self._cache_lock:
                self._section_cache.pop(key, None)
            self._unknown_persons.add(person_id)
        except Exception:
            with self._cache_lock:
                existing = self._section_cache.get(key)
                if existing is None:
                    existing = SectionCacheEntry(payload=self._empty_section_payload(person_id, section))
                existing.refresh_in_progress = False
                existing.has_error = existing.generated_at is None
                if "refresh_failed" not in existing.warnings:
                    existing.warnings.append("refresh_failed")
                self._section_cache[key] = existing

    def get_dashboard_section(self, person_id: UUID, section: DashboardSectionName) -> DashboardSectionReadModel:
        self._person_exists(person_id)
        key = self._cache_key(person_id, section)
        now = datetime.now(UTC)

        with self._cache_lock:
            entry = self._section_cache.get(key)
            if entry is None:
                entry = SectionCacheEntry(payload=self._empty_section_payload(person_id, section))
                self._section_cache[key] = entry

            if entry.generated_at and entry.stale_at and now < entry.stale_at:
                state = "ready"
            elif entry.generated_at:
                state = "stale"
            elif entry.has_error:
                state = "error"
            else:
                state = "pending"

            should_refresh = state in {"pending", "stale"} and not entry.refresh_in_progress

        if should_refresh:
            self._trigger_background_refresh(person_id, section)
            with self._cache_lock:
                entry = self._section_cache[key]

        return DashboardSectionReadModel(
            person_id=person_id,
            section=section,
            state=state,
            generated_at=entry.generated_at,
            stale_at=entry.stale_at,
            refresh_in_progress=entry.refresh_in_progress,
            warnings=list(entry.warnings),
            payload=entry.payload,
        )

    def overview(self, person_id: UUID) -> OverviewReadModel:
        self._person_exists(person_id)
        return OverviewReadModel.model_validate(
            self._build_overview_payload(person_id, self._build_dashboard_data(person_id))
        )

    def allocation(self, person_id: UUID) -> AllocationReadModel:
        self._person_exists(person_id)
        return AllocationReadModel.model_validate(
            self._build_allocation_payload(person_id, self._build_dashboard_data(person_id))
        )

    def timeseries(self, person_id: UUID) -> TimeseriesReadModel:
        self._person_exists(person_id)
        return TimeseriesReadModel.model_validate(
            self._build_timeseries_payload(person_id, self._build_dashboard_data(person_id))
        )

    def monthly_comparison(self, person_id: UUID) -> MonthlyComparisonReadModel:
        data = self._build_dashboard_data(person_id)
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
        self._person_exists(person_id)
        return MetricsReadModel.model_validate(
            self._build_metrics_payload(person_id, self._build_dashboard_data(person_id))
        )

    def heatmap(self, person_id: UUID) -> HeatmapReadModel:
        data = self._build_dashboard_data(person_id)
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
        data = self._build_dashboard_data(person_id)
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
