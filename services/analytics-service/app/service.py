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
    PortfolioContributorItem,
    PortfolioContributorsReadModel,
    PortfolioDataCoverageReadModel,
    PortfolioExposureSlice,
    PortfolioExposuresReadModel,
    PortfolioHoldingItem,
    PortfolioHoldingsReadModel,
    PortfolioPerformanceReadModel,
    PortfolioPerformanceSummary,
    PortfolioRiskReadModel,
    PortfolioSummaryReadModel,
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


@dataclass(slots=True)
class PortfolioHoldingSnapshot:
    portfolio_id: str
    portfolio_name: str | None
    holding_id: str | None
    symbol: str | None
    display_name: str | None
    quantity: float
    acquisition_price: float
    current_price: float | None
    invested_value: float
    market_value: float
    unrealized_pnl: float
    unrealized_return_pct: float | None
    weight: float = 0.0
    sector: str | None = None
    country: str | None = None
    currency: str | None = None
    data_status: str = "ok"
    warnings: list[str] = field(default_factory=list)


class AnalyticsService:
    DEFAULT_BENCHMARK_SYMBOL = "SPY"
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

    def _load_instrument_profile(self, symbol: str, client: httpx.Client | None = None) -> dict:
        payload = self._request_json(
            f"{self._marketdata_base_url}/api/v1/marketdata/instruments/{symbol}/profile",
            client=client,
        )
        return payload if isinstance(payload, dict) else {}

    def _safe_load_instrument_profile(self, symbol: str, client: httpx.Client) -> dict:
        try:
            return self._load_instrument_profile(symbol, client=client)
        except httpx.HTTPError:
            return {}

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

    @staticmethod
    def _portfolio_returns(points: list[ChartPoint]) -> list[float]:
        returns: list[float] = []
        for idx in range(1, len(points)):
            prev = points[idx - 1].y
            curr = points[idx].y
            if prev > 0:
                returns.append((curr - prev) / prev)
        return returns

    @staticmethod
    def _portfolio_return_points(points: list[ChartPoint]) -> list[ChartPoint]:
        return_points: list[ChartPoint] = []
        for idx in range(1, len(points)):
            prev = points[idx - 1].y
            curr = points[idx].y
            if prev > 0:
                return_points.append(ChartPoint(x=points[idx].x, y=(curr - prev) / prev))
        return return_points

    @staticmethod
    def _volatility(values: list[float]) -> float | None:
        if len(values) < 2:
            return None
        avg = sum(values) / len(values)
        variance = sum((value - avg) ** 2 for value in values) / len(values)
        return variance ** 0.5

    @staticmethod
    def _max_drawdown(points: list[ChartPoint]) -> float | None:
        if not points:
            return None
        running_peak = points[0].y
        max_drawdown = 0.0
        for point in points:
            running_peak = max(running_peak, point.y)
            if running_peak <= 0:
                continue
            drawdown = (point.y / running_peak) - 1.0
            max_drawdown = min(max_drawdown, drawdown)
        return max_drawdown

    @staticmethod
    def _concentration_metrics(holdings: list[PortfolioHoldingSnapshot]) -> tuple[float | None, float | None, str | None]:
        ordered_weights = sorted((item.weight for item in holdings), reverse=True)
        top_position_weight = ordered_weights[0] if ordered_weights else None
        top3_weight = sum(ordered_weights[:3]) if ordered_weights else None
        concentration_note: str | None = None
        if top3_weight is not None and top3_weight >= 0.75:
            concentration_note = "very_high_top3_concentration"
        elif top3_weight is not None and top3_weight >= 0.65:
            concentration_note = "high_top3_concentration"
        elif top_position_weight is not None and top_position_weight >= 0.5:
            concentration_note = "single_position_dominates"
        return top_position_weight, top3_weight, concentration_note

    @staticmethod
    def _align_return_series(left: list[ChartPoint], right: list[ChartPoint]) -> tuple[list[float], list[float]]:
        right_by_date = {point.x: point.y for point in right}
        aligned_left: list[float] = []
        aligned_right: list[float] = []
        for point in left:
            if point.x not in right_by_date:
                continue
            aligned_left.append(point.y)
            aligned_right.append(right_by_date[point.x])
        return aligned_left, aligned_right

    def _compute_beta_and_correlation(self, portfolio_returns: list[float], benchmark_returns: list[float]) -> tuple[float | None, float | None]:
        if len(portfolio_returns) < 2 or len(benchmark_returns) < 2:
            return None, None
        size = min(len(portfolio_returns), len(benchmark_returns))
        left = portfolio_returns[-size:]
        right = benchmark_returns[-size:]
        avg_left = sum(left) / size
        avg_right = sum(right) / size
        covariance = sum((left[idx] - avg_left) * (right[idx] - avg_right) for idx in range(size)) / size
        var_left = sum((value - avg_left) ** 2 for value in left) / size
        var_right = sum((value - avg_right) ** 2 for value in right) / size
        beta = (covariance / var_right) if var_right > 0 else None
        correlation = covariance / ((var_left ** 0.5) * (var_right ** 0.5)) if var_left > 0 and var_right > 0 else None
        return beta, correlation

    def _build_portfolio_history_from_snapshots(
        self,
        holdings: list[PortfolioHoldingSnapshot],
        client: httpx.Client,
    ) -> tuple[list[ChartPoint], list[str]]:
        warnings: list[str] = []
        symbols = [item.symbol for item in holdings if item.symbol]
        unique_symbols = list(dict.fromkeys(symbols))
        histories: dict[str, list[dict]] = {}
        if unique_symbols:
            with ThreadPoolExecutor(max_workers=min(16, len(unique_symbols))) as executor:
                for symbol, history in zip(
                    unique_symbols,
                    executor.map(lambda s: self._safe_load_history_points(s, client=client), unique_symbols),
                    strict=True,
                ):
                    histories[symbol] = history
                    if not history:
                        warnings.append(f"missing_history:{symbol}")

        totals_by_day: dict[str, float] = defaultdict(float)
        for item in holdings:
            if not item.symbol:
                continue
            symbol_history = histories.get(item.symbol, [])
            if symbol_history:
                for point in symbol_history:
                    day = str(point.get("date", "")).strip()
                    close = self._as_float(point.get("close"))
                    if day:
                        totals_by_day[day] += close * item.quantity
            else:
                warnings.append(f"history_fallback_to_market_value:{item.symbol}")

        ordered_days = sorted(totals_by_day)
        points = [ChartPoint(x=day, y=round(totals_by_day[day], 2)) for day in ordered_days]
        return points, list(dict.fromkeys(warnings))

    @staticmethod
    def _coverage_summary(holdings: list[PortfolioHoldingSnapshot], base_warnings: list[str]) -> tuple[dict[str, int], list[str]]:
        missing_prices = sum(1 for item in holdings if item.current_price is None)
        missing_sectors = sum(1 for item in holdings if not item.sector)
        missing_countries = sum(1 for item in holdings if not item.country)
        missing_currencies = sum(1 for item in holdings if not item.currency)
        fallback_acquisition_prices = sum(1 for item in holdings if item.data_status == "fallback_acquisition_price")
        holdings_with_marketdata_warnings = sum(1 for item in holdings if len(item.warnings) > 0)

        warnings = list(base_warnings)
        if missing_sectors > 0:
            warnings.append("missing_sector_data")
        if missing_countries > 0:
            warnings.append("missing_country_data")
        if missing_currencies > 0:
            warnings.append("missing_currency_data")
        if fallback_acquisition_prices > 0:
            warnings.append("fallback_acquisition_price_used")
        if holdings_with_marketdata_warnings > 0:
            warnings.append("holdings_with_marketdata_warnings")

        counters = {
            "missing_prices": missing_prices,
            "missing_sectors": missing_sectors,
            "missing_countries": missing_countries,
            "missing_currencies": missing_currencies,
            "fallback_acquisition_prices": fallback_acquisition_prices,
            "holdings_with_marketdata_warnings": holdings_with_marketdata_warnings,
        }
        return counters, list(dict.fromkeys(warnings))

    def _load_person_holdings(self, person_id: UUID, client: httpx.Client) -> tuple[list[dict], list[dict]]:
        portfolios = self._load_portfolios(person_id, client=client)
        holdings_with_context: list[dict] = []
        for portfolio in portfolios:
            portfolio_id = str(portfolio.get("portfolio_id", "")).strip()
            if not portfolio_id:
                continue
            portfolio_name = (
                str(portfolio.get("display_name", "")).strip()
                or str(portfolio.get("name", "")).strip()
                or None
            )
            for holding in self._load_holdings(portfolio_id, client=client):
                enriched = dict(holding)
                enriched["portfolio_id"] = portfolio_id
                enriched["portfolio_name"] = portfolio_name
                holdings_with_context.append(enriched)
        return portfolios, holdings_with_context

    def _build_portfolio_holdings_snapshot(self, person_id: UUID) -> tuple[list[dict], list[PortfolioHoldingSnapshot], list[str]]:
        warnings: list[str] = []
        with httpx.Client(timeout=self._timeout) as client:
            self._person_exists(person_id, client=client)
            portfolios, holdings = self._load_person_holdings(person_id, client=client)

            symbol_sequence = [
                str(holding.get("symbol", "")).upper().strip()
                for holding in holdings
                if str(holding.get("symbol", "")).upper().strip()
            ]
            unique_symbols = list(dict.fromkeys(symbol_sequence))

            symbol_profiles: dict[str, dict] = {}
            if unique_symbols:
                with ThreadPoolExecutor(max_workers=min(16, len(unique_symbols))) as executor:
                    for symbol, profile in zip(
                        unique_symbols,
                        executor.map(lambda s: self._safe_load_instrument_profile(s, client=client), unique_symbols),
                        strict=True,
                    ):
                        symbol_profiles[symbol] = profile

            snapshots: list[PortfolioHoldingSnapshot] = []
            for holding in holdings:
                quantity = self._as_float(holding.get("quantity"))
                acquisition_price = self._as_float(holding.get("acquisition_price"))
                symbol = str(holding.get("symbol", "")).upper().strip() or None
                profile = symbol_profiles.get(symbol or "", {})
                current_price_raw = profile.get("price")
                current_price = self._as_float(current_price_raw) if current_price_raw is not None else None

                effective_price = current_price if current_price is not None else acquisition_price
                invested_value = quantity * acquisition_price
                market_value = quantity * effective_price
                unrealized_pnl = market_value - invested_value
                unrealized_return_pct = (unrealized_pnl / invested_value * 100) if invested_value > 0 else None

                item_warnings: list[str] = []
                data_status = "ok"
                if current_price is None:
                    data_status = "fallback_acquisition_price"
                    item_warnings.append("missing_current_price")
                if not symbol:
                    data_status = "missing_symbol"
                    item_warnings.append("missing_symbol")

                display_name = (
                    str(profile.get("name", "")).strip()
                    or str(profile.get("display_name", "")).strip()
                    or (symbol if symbol else None)
                )
                sector = str(profile.get("sector", "")).strip() or None
                country = str(profile.get("country", "")).strip() or None
                currency = str(profile.get("currency", "")).strip() or None

                snapshots.append(
                    PortfolioHoldingSnapshot(
                        portfolio_id=str(holding.get("portfolio_id", "")).strip(),
                        portfolio_name=holding.get("portfolio_name"),
                        holding_id=str(holding.get("holding_id", "")).strip() or None,
                        symbol=symbol,
                        display_name=display_name,
                        quantity=quantity,
                        acquisition_price=acquisition_price,
                        current_price=current_price,
                        invested_value=invested_value,
                        market_value=market_value,
                        unrealized_pnl=unrealized_pnl,
                        unrealized_return_pct=unrealized_return_pct,
                        sector=sector,
                        country=country,
                        currency=currency,
                        data_status=data_status,
                        warnings=item_warnings,
                    )
                )

            total_market_value = sum(item.market_value for item in snapshots)
            for item in snapshots:
                item.weight = (item.market_value / total_market_value) if total_market_value > 0 else 0.0

            if any("missing_current_price" in item.warnings for item in snapshots):
                warnings.append("price_fallback_used_for_some_holdings")

            if any(item.symbol is None for item in snapshots):
                warnings.append("holdings_with_missing_symbol")

        return portfolios, snapshots, warnings

    @staticmethod
    def _aggregate_exposure(
        holdings: list[PortfolioHoldingSnapshot],
        label_getter,
    ) -> list[PortfolioExposureSlice]:
        total_market_value = sum(item.market_value for item in holdings)
        grouped_values: dict[str, float] = defaultdict(float)
        for item in holdings:
            label = label_getter(item)
            grouped_values[label] += item.market_value
        slices = [
            PortfolioExposureSlice(
                label=label,
                market_value=round(value, 2),
                weight=round((value / total_market_value), 6) if total_market_value > 0 else 0.0,
            )
            for label, value in grouped_values.items()
        ]
        return sorted(slices, key=lambda item: item.market_value, reverse=True)

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

    def portfolio_summary(self, person_id: UUID) -> PortfolioSummaryReadModel:
        portfolios, holdings, warnings = self._build_portfolio_holdings_snapshot(person_id)
        total_market_value = sum(item.market_value for item in holdings)
        total_invested_value = sum(item.invested_value for item in holdings)
        total_unrealized_pnl = total_market_value - total_invested_value
        unrealized_return_pct = (
            total_unrealized_pnl / total_invested_value * 100 if total_invested_value > 0 else None
        )
        ordered_weights = sorted((item.weight for item in holdings), reverse=True)
        top_position_weight = ordered_weights[0] if ordered_weights else None
        top3_weight = sum(ordered_weights[:3]) if ordered_weights else None

        meta = {"loading": False, "error": ", ".join(warnings) if warnings else None}
        return PortfolioSummaryReadModel(
            person_id=person_id,
            as_of=datetime.now(UTC).date(),
            currency="EUR",
            market_value=round(total_market_value, 2),
            invested_value=round(total_invested_value, 2),
            unrealized_pnl=round(total_unrealized_pnl, 2),
            unrealized_return_pct=round(unrealized_return_pct, 4) if unrealized_return_pct is not None else None,
            portfolios_count=len(portfolios),
            holdings_count=len(holdings),
            top_position_weight=round(top_position_weight, 6) if top_position_weight is not None else None,
            top3_weight=round(top3_weight, 6) if top3_weight is not None else None,
            meta=meta,
        )

    def portfolio_performance(self, person_id: UUID, range_value: str = "3m") -> PortfolioPerformanceReadModel:
        _, holdings, warnings = self._build_portfolio_holdings_snapshot(person_id)
        with httpx.Client(timeout=self._timeout) as client:
            portfolio_points, history_warnings = self._build_portfolio_history_from_snapshots(holdings, client)
            benchmark_points_raw = self._safe_load_history_points(self.DEFAULT_BENCHMARK_SYMBOL, client)

        benchmark_points = [
            ChartPoint(x=str(point.get("date", "")), y=round(self._as_float(point.get("close")), 2))
            for point in benchmark_points_raw
            if str(point.get("date", "")).strip()
        ]
        benchmark_points = sorted(benchmark_points, key=lambda point: point.x)

        series = [ChartSeries(key="portfolio_value", label="Portfolio", points=portfolio_points)]
        if benchmark_points:
            series.append(
                ChartSeries(
                    key="benchmark_price",
                    label=f"Benchmark {self.DEFAULT_BENCHMARK_SYMBOL}",
                    points=benchmark_points,
                )
            )
        else:
            history_warnings.append(f"benchmark_history_unavailable:{self.DEFAULT_BENCHMARK_SYMBOL}")

        start_value = portfolio_points[0].y if portfolio_points else None
        end_value = portfolio_points[-1].y if portfolio_points else None
        absolute_change = (end_value - start_value) if start_value is not None and end_value is not None else None
        return_pct = (
            (absolute_change / start_value * 100)
            if absolute_change is not None and start_value is not None and start_value > 0
            else None
        )
        return PortfolioPerformanceReadModel(
            person_id=person_id,
            range=range_value,
            benchmark_symbol=self.DEFAULT_BENCHMARK_SYMBOL if benchmark_points else None,
            series=series,
            summary=PortfolioPerformanceSummary(
                start_value=round(start_value, 2) if start_value is not None else None,
                end_value=round(end_value, 2) if end_value is not None else None,
                absolute_change=round(absolute_change, 2) if absolute_change is not None else None,
                return_pct=round(return_pct, 4) if return_pct is not None else None,
            ),
            meta={"loading": False, "error": ", ".join(list(dict.fromkeys(warnings + history_warnings))) or None},
        )

    def portfolio_exposures(self, person_id: UUID) -> PortfolioExposuresReadModel:
        _, holdings, _ = self._build_portfolio_holdings_snapshot(person_id)
        by_position = self._aggregate_exposure(
            holdings,
            lambda item: item.display_name or item.symbol or "UNKNOWN",
        )
        by_sector = self._aggregate_exposure(holdings, lambda item: item.sector or "UNKNOWN")
        by_country = self._aggregate_exposure(holdings, lambda item: item.country or "UNKNOWN")
        by_currency = self._aggregate_exposure(holdings, lambda item: item.currency or "UNKNOWN")
        return PortfolioExposuresReadModel(
            person_id=person_id,
            by_position=by_position,
            by_sector=by_sector,
            by_country=by_country,
            by_currency=by_currency,
        )

    def portfolio_holdings(self, person_id: UUID) -> PortfolioHoldingsReadModel:
        _, holdings, warnings = self._build_portfolio_holdings_snapshot(person_id)
        summary = self.portfolio_summary(person_id)
        items = [
            PortfolioHoldingItem(
                portfolio_id=item.portfolio_id,
                portfolio_name=item.portfolio_name,
                holding_id=item.holding_id,
                symbol=item.symbol,
                display_name=item.display_name,
                quantity=round(item.quantity, 8),
                acquisition_price=round(item.acquisition_price, 8),
                current_price=round(item.current_price, 8) if item.current_price is not None else None,
                invested_value=round(item.invested_value, 2),
                market_value=round(item.market_value, 2),
                unrealized_pnl=round(item.unrealized_pnl, 2),
                unrealized_return_pct=round(item.unrealized_return_pct, 4)
                if item.unrealized_return_pct is not None
                else None,
                weight=round(item.weight, 6),
                sector=item.sector,
                country=item.country,
                currency=item.currency,
                data_status=item.data_status,
                warnings=item.warnings,
            )
            for item in sorted(holdings, key=lambda x: x.market_value, reverse=True)
        ]
        return PortfolioHoldingsReadModel(
            person_id=person_id,
            as_of=datetime.now(UTC).date(),
            currency="EUR",
            items=items,
            summary=summary,
            meta={"loading": False, "error": ", ".join(warnings) if warnings else None},
        )

    def portfolio_risk(self, person_id: UUID) -> PortfolioRiskReadModel:
        _, holdings, warnings = self._build_portfolio_holdings_snapshot(person_id)
        top_position_weight, top3_weight, concentration_note = self._concentration_metrics(holdings)

        with httpx.Client(timeout=self._timeout) as client:
            portfolio_points, history_warnings = self._build_portfolio_history_from_snapshots(holdings, client)
            benchmark_history = self._safe_load_history_points(self.DEFAULT_BENCHMARK_SYMBOL, client)

        portfolio_return_points = self._portfolio_return_points(portfolio_points)
        portfolio_returns = [point.y for point in portfolio_return_points]
        portfolio_volatility = self._volatility(portfolio_returns)
        max_drawdown = self._max_drawdown(portfolio_points)

        benchmark_points = [
            ChartPoint(x=str(point.get("date", "")), y=self._as_float(point.get("close")))
            for point in benchmark_history
            if str(point.get("date", "")).strip()
        ]
        benchmark_return_points = self._portfolio_return_points(sorted(benchmark_points, key=lambda point: point.x))
        aligned_portfolio_returns, aligned_benchmark_returns = self._align_return_series(
            portfolio_return_points,
            benchmark_return_points,
        )
        beta, correlation = self._compute_beta_and_correlation(aligned_portfolio_returns, aligned_benchmark_returns)
        tracking_error = None
        if aligned_portfolio_returns and aligned_benchmark_returns:
            size = min(len(aligned_portfolio_returns), len(aligned_benchmark_returns))
            active = [
                aligned_portfolio_returns[-size + idx] - aligned_benchmark_returns[-size + idx]
                for idx in range(size)
            ]
            tracking_error = self._volatility(active)

        return PortfolioRiskReadModel(
            person_id=person_id,
            as_of=datetime.now(UTC).date(),
            benchmark_symbol=self.DEFAULT_BENCHMARK_SYMBOL if aligned_benchmark_returns else None,
            portfolio_volatility=round(portfolio_volatility, 6) if portfolio_volatility is not None else None,
            max_drawdown=round(max_drawdown, 6) if max_drawdown is not None else None,
            correlation=round(correlation, 6) if correlation is not None else None,
            beta=round(beta, 6) if beta is not None else None,
            tracking_error=round(tracking_error, 6) if tracking_error is not None else None,
            top_position_weight=round(top_position_weight, 6) if top_position_weight is not None else None,
            top3_weight=round(top3_weight, 6) if top3_weight is not None else None,
            concentration_note=concentration_note,
            meta={"loading": False, "error": ", ".join(list(dict.fromkeys(warnings + history_warnings))) or None},
        )

    def portfolio_contributors(self, person_id: UUID) -> PortfolioContributorsReadModel:
        _, holdings, _ = self._build_portfolio_holdings_snapshot(person_id)
        enriched = sorted(holdings, key=lambda item: item.unrealized_pnl, reverse=True)
        top_positive = [item for item in enriched if item.unrealized_pnl > 0][:5]
        top_negative = [item for item in sorted(holdings, key=lambda item: item.unrealized_pnl) if item.unrealized_pnl < 0][:5]

        def to_item(item: PortfolioHoldingSnapshot) -> PortfolioContributorItem:
            contribution_weighted = item.weight * item.unrealized_pnl
            direction = "positive" if item.unrealized_pnl >= 0 else "negative"
            return PortfolioContributorItem(
                symbol=item.symbol,
                display_name=item.display_name,
                market_value=round(item.market_value, 2),
                weight=round(item.weight, 6),
                unrealized_pnl=round(item.unrealized_pnl, 2),
                contribution_weighted=round(contribution_weighted, 6),
                direction=direction,
            )

        return PortfolioContributorsReadModel(
            person_id=person_id,
            top_contributors=[to_item(item) for item in top_positive],
            top_detractors=[to_item(item) for item in top_negative],
        )

    def portfolio_data_coverage(self, person_id: UUID) -> PortfolioDataCoverageReadModel:
        _, holdings, warnings = self._build_portfolio_holdings_snapshot(person_id)
        counters, coverage_warnings = self._coverage_summary(holdings, warnings)

        return PortfolioDataCoverageReadModel(
            person_id=person_id,
            as_of=datetime.now(UTC).date(),
            total_holdings=len(holdings),
            missing_prices=counters["missing_prices"],
            missing_sectors=counters["missing_sectors"],
            missing_countries=counters["missing_countries"],
            missing_currencies=counters["missing_currencies"],
            fallback_acquisition_prices=counters["fallback_acquisition_prices"],
            holdings_with_marketdata_warnings=counters["holdings_with_marketdata_warnings"],
            warnings=coverage_warnings,
            meta={"loading": False, "error": None},
        )
