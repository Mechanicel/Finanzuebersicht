from __future__ import annotations

from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from math import sqrt
from statistics import mean
from threading import Lock
from uuid import UUID

import httpx

from app.ttl_lru_cache import TtlLruCache
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
    PortfolioAttributionItem,
    PortfolioAttributionReadModel,
    PortfolioAttributionSummary,
    PortfolioContributorItem,
    PortfolioContributorsReadModel,
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


@dataclass(slots=True)
class PortfolioSnapshotCacheEntry:
    snapshot: tuple[list[dict], list[PortfolioHoldingSnapshot], list[str]]
    stale_at: datetime


@dataclass(slots=True)
class PortfolioHistoryContext:
    holdings: list[PortfolioHoldingSnapshot]
    snapshot_warnings: list[str]
    portfolio_points: list[ChartPoint]
    history_warnings: list[str]
    benchmark_points: list[ChartPoint]
    history_by_symbol: dict[str, list[ChartPoint]]


@dataclass(slots=True)
class PortfolioHistoryCacheEntry:
    context: PortfolioHistoryContext
    stale_at: datetime


@dataclass(slots=True)
class PortfolioAttributionPosition:
    symbol: str
    label: str
    contribution_pct_points: float
    return_pct: float | None
    weight: float
    market_value: float
    sector: str
    country: str
    currency: str
    periods_used: int


@dataclass(slots=True)
class PortfolioDashboardCacheEntry:
    payload: PortfolioDashboardReadModel
    generated_at: datetime
    stale_at: datetime


class AnalyticsService:
    DEFAULT_BENCHMARK_SYMBOL = "SPY"
    KNOWN_PERSONS_CACHE_MAX_SIZE = 2048
    KNOWN_PERSONS_CACHE_TTL_SECONDS = 3600
    UNKNOWN_PERSONS_CACHE_MAX_SIZE = 2048
    UNKNOWN_PERSONS_CACHE_TTL_SECONDS = 900
    PORTFOLIO_DASHBOARD_CACHE_TTL_SECONDS = 15.0
    PORTFOLIO_DASHBOARD_CACHE_MAX_SIZE = 256

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
        portfolio_snapshot_cache_ttl_seconds: float = 10.0,
        portfolio_dashboard_cache_ttl_seconds: float = PORTFOLIO_DASHBOARD_CACHE_TTL_SECONDS,
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
        self._known_persons = TtlLruCache(
            max_size=self.KNOWN_PERSONS_CACHE_MAX_SIZE,
            ttl_seconds=self.KNOWN_PERSONS_CACHE_TTL_SECONDS,
        )
        self._unknown_persons = TtlLruCache(
            max_size=self.UNKNOWN_PERSONS_CACHE_MAX_SIZE,
            ttl_seconds=self.UNKNOWN_PERSONS_CACHE_TTL_SECONDS,
        )
        self._portfolio_snapshot_cache_ttl_seconds = portfolio_snapshot_cache_ttl_seconds
        self._portfolio_snapshot_cache: dict[UUID, PortfolioSnapshotCacheEntry] = {}
        self._portfolio_snapshot_inflight: dict[
            UUID,
            Future[tuple[list[dict], list[PortfolioHoldingSnapshot], list[str]]],
        ] = {}
        self._portfolio_snapshot_lock = Lock()
        self._portfolio_history_cache: dict[tuple[UUID, str], PortfolioHistoryCacheEntry] = {}
        self._portfolio_history_inflight: dict[tuple[UUID, str], Future[PortfolioHistoryContext]] = {}
        self._portfolio_history_lock = Lock()
        self._portfolio_dashboard_cache_ttl_seconds = portfolio_dashboard_cache_ttl_seconds
        self._portfolio_dashboard_cache: dict[tuple[UUID, str], PortfolioDashboardCacheEntry] = {}
        self._portfolio_dashboard_inflight: dict[tuple[UUID, str], Future[PortfolioDashboardCacheEntry]] = {}
        self._portfolio_dashboard_lock = Lock()

    def _request_json(self, url: str, client: httpx.Client | None = None) -> dict | list[dict]:
        if client is None:
            with httpx.Client(timeout=self._timeout) as local_client:
                response = local_client.get(url)
        else:
            response = client.get(url)
        response.raise_for_status()
        return response.json()["data"]

    @staticmethod
    def _range_label(range_value: str) -> str:
        labels = {
            "1m": "1 month",
            "3m": "3 months",
            "6m": "6 months",
            "ytd": "year to date",
            "1y": "1 year",
            "max": "max",
        }
        return labels.get(range_value, range_value)

    def _person_exists(self, person_id: UUID, client: httpx.Client | None = None) -> None:
        if self._known_persons.get(person_id):
            return
        if self._unknown_persons.get(person_id):
            raise KeyError(f"Unknown person_id: {person_id}")
        try:
            self._request_json(f"{self._person_base_url}/api/v1/persons/{person_id}", client=client)
            self._known_persons.set(person_id, True)
            self._unknown_persons.delete(person_id)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                self._unknown_persons.set(person_id, True)
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

    def _load_holdings_summary_batch(self, symbols: list[str], client: httpx.Client) -> list[dict]:
        if not symbols:
            return []
        payload = self._request_json(
            f"{self._marketdata_base_url}/api/v1/marketdata/depot/holdings-summary?symbols={','.join(symbols)}",
            client=client,
        )
        if not isinstance(payload, dict):
            return []
        items = payload.get("items", [])
        return items if isinstance(items, list) else []

    def _load_batch_history(self, symbols: list[str], client: httpx.Client, range_value: str = "3m") -> list[dict]:
        if not symbols:
            return []
        payload = self._request_json(
            f"{self._marketdata_base_url}/api/v1/marketdata/batch/history?symbols={','.join(symbols)}&range={range_value}",
            client=client,
        )
        if not isinstance(payload, dict):
            return []
        items = payload.get("items", [])
        return items if isinstance(items, list) else []

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
                return_points.append(ChartPoint(x=points[idx - 1].x, y=(curr - prev) / prev))
        return return_points

    @staticmethod
    def _volatility(values: list[float]) -> float | None:
        if len(values) < 2:
            return None
        avg = sum(values) / len(values)
        variance = sum((value - avg) ** 2 for value in values) / (len(values) - 1)
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
        histories: dict[str, list[dict]],
    ) -> tuple[list[ChartPoint], list[str]]:
        warnings: list[str] = []
        totals_by_day: dict[str, float] = defaultdict(float)
        for item in holdings:
            if not item.symbol:
                continue
            symbol_history = histories.get(item.symbol, [])
            if not symbol_history:
                warnings.append(f"missing_history:{item.symbol}")
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

    def _sanitize_history_points(self, symbol: str, points: list[dict]) -> tuple[list[dict], list[str]]:
        warnings: list[str] = []
        sanitized: list[dict] = []
        previous_close: float | None = None
        for point in points:
            day = str(point.get("date", "")).strip()
            close = self._as_float(point.get("close"))
            if not day or close <= 0:
                warnings.append(f"history_invalid_price_filtered:{symbol}")
                continue
            if previous_close is not None and previous_close > 0:
                ratio = close / previous_close
                if ratio > 5.0 or ratio < 0.2:
                    warnings.append(f"history_outlier_filtered:{symbol}")
                    continue
            sanitized.append({"date": day, "close": close})
            previous_close = close
        return sanitized, list(dict.fromkeys(warnings))

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
        valid_portfolios: list[tuple[str, str | None]] = []
        for portfolio in portfolios:
            portfolio_id = str(portfolio.get("portfolio_id", "")).strip()
            if not portfolio_id:
                continue
            portfolio_name = (
                str(portfolio.get("display_name", "")).strip()
                or str(portfolio.get("name", "")).strip()
                or None
            )
            valid_portfolios.append((portfolio_id, portfolio_name))

        if not valid_portfolios:
            return portfolios, []

        holdings_by_portfolio: dict[str, list[dict]] = {}
        with ThreadPoolExecutor(max_workers=min(8, len(valid_portfolios))) as executor:
            for (portfolio_id, _), portfolio_holdings in zip(
                valid_portfolios,
                executor.map(lambda p: self._load_holdings(p[0], client=client), valid_portfolios),
                strict=True,
            ):
                holdings_by_portfolio[portfolio_id] = portfolio_holdings

        holdings_with_context: list[dict] = []
        for portfolio_id, portfolio_name in valid_portfolios:
            for holding in holdings_by_portfolio.get(portfolio_id, []):
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
            profile_items = self._load_holdings_summary_batch(unique_symbols, client=client)
            symbol_profiles: dict[str, dict] = {
                str(item.get("symbol", "")).upper().strip(): item
                for item in profile_items
                if str(item.get("symbol", "")).upper().strip()
            }

            snapshots: list[PortfolioHoldingSnapshot] = []
            for holding in holdings:
                quantity = self._as_float(holding.get("quantity"))
                acquisition_price = self._as_float(holding.get("acquisition_price"))
                symbol = str(holding.get("symbol", "")).upper().strip() or None
                profile = symbol_profiles.get(symbol or "", {})
                current_price_raw = profile.get("price")
                if current_price_raw is None:
                    current_price_raw = profile.get("current_price")
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
                coverage = str(profile.get("coverage", "")).strip().lower()
                if coverage and coverage not in {"full", "ok"}:
                    data_status = coverage
                    item_warnings.append(f"marketdata_coverage:{coverage}")
                cache_status = str(profile.get("cache_status", "")).strip().lower()
                if cache_status and cache_status not in {"fresh_cache", "stale_cache"}:
                    item_warnings.append(f"marketdata_cache_status:{cache_status}")
                if not symbol:
                    data_status = "missing_symbol"
                    item_warnings.append("missing_symbol")
                if symbol and not profile:
                    item_warnings.append("missing_marketdata_summary")

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

    def _get_portfolio_holdings_snapshot(self, person_id: UUID) -> tuple[list[dict], list[PortfolioHoldingSnapshot], list[str]]:
        now = datetime.now(UTC)
        with self._portfolio_snapshot_lock:
            cache_entry = self._portfolio_snapshot_cache.get(person_id)
            if cache_entry is not None and now < cache_entry.stale_at:
                return cache_entry.snapshot

            inflight = self._portfolio_snapshot_inflight.get(person_id)
            should_build = inflight is None
            if inflight is None:
                inflight = Future()
                self._portfolio_snapshot_inflight[person_id] = inflight

        if not should_build:
            return inflight.result()

        try:
            snapshot = self._build_portfolio_holdings_snapshot(person_id)
            stale_at = datetime.now(UTC) + timedelta(seconds=self._portfolio_snapshot_cache_ttl_seconds)
            with self._portfolio_snapshot_lock:
                self._portfolio_snapshot_cache[person_id] = PortfolioSnapshotCacheEntry(
                    snapshot=snapshot,
                    stale_at=stale_at,
                )
                self._portfolio_snapshot_inflight.pop(person_id, None)
                inflight.set_result(snapshot)
            return snapshot
        except Exception as exc:
            with self._portfolio_snapshot_lock:
                self._portfolio_snapshot_inflight.pop(person_id, None)
                inflight.set_exception(exc)
            raise

    def _get_portfolio_history_context(self, person_id: UUID, range_value: str = "3m") -> PortfolioHistoryContext:
        now = datetime.now(UTC)
        cache_key = (person_id, range_value)
        with self._portfolio_history_lock:
            cache_entry = self._portfolio_history_cache.get(cache_key)
            if cache_entry is not None and now < cache_entry.stale_at:
                return cache_entry.context

            inflight = self._portfolio_history_inflight.get(cache_key)
            should_build = inflight is None
            if inflight is None:
                inflight = Future()
                self._portfolio_history_inflight[cache_key] = inflight

        if not should_build:
            return inflight.result()

        try:
            _, holdings, snapshot_warnings = self._get_portfolio_holdings_snapshot(person_id)
            with httpx.Client(timeout=self._timeout) as client:
                symbols = [item.symbol for item in holdings if item.symbol]
                batch_symbols = list(dict.fromkeys(symbols + [self.DEFAULT_BENCHMARK_SYMBOL]))
                batch_history_items = self._load_batch_history(batch_symbols, client=client, range_value=range_value)
                raw_history_by_symbol: dict[str, list[dict]] = {}
                history_warnings: list[str] = []
                for item in batch_history_items:
                    symbol = str(item.get("symbol", "")).upper().strip()
                    if not symbol:
                        continue
                    points_raw = item.get("points", [])
                    points = points_raw if isinstance(points_raw, list) else []
                    points, filtered_warnings = self._sanitize_history_points(symbol, points)
                    history_warnings.extend(filtered_warnings)
                    raw_history_by_symbol[symbol] = points
                    if not points:
                        history_warnings.append(f"missing_history:{symbol}")
                portfolio_points, series_warnings = self._build_portfolio_history_from_snapshots(holdings, raw_history_by_symbol)
                history_warnings.extend(series_warnings)
                benchmark_points_raw = raw_history_by_symbol.get(self.DEFAULT_BENCHMARK_SYMBOL, [])

            benchmark_points = sorted(
                [
                    ChartPoint(x=str(point.get("date", "")), y=round(self._as_float(point.get("close")), 2))
                    for point in benchmark_points_raw
                    if str(point.get("date", "")).strip()
                ],
                key=lambda point: point.x,
            )
            history_by_symbol: dict[str, list[ChartPoint]] = {}
            for symbol, points in raw_history_by_symbol.items():
                history_by_symbol[symbol] = sorted(
                    [
                        ChartPoint(x=str(point.get("date", "")).strip(), y=round(self._as_float(point.get("close")), 8))
                        for point in points
                        if str(point.get("date", "")).strip()
                    ],
                    key=lambda point: point.x,
                )
            context = PortfolioHistoryContext(
                holdings=holdings,
                snapshot_warnings=snapshot_warnings,
                portfolio_points=portfolio_points,
                history_warnings=history_warnings,
                benchmark_points=benchmark_points,
                history_by_symbol=history_by_symbol,
            )
            stale_at = datetime.now(UTC) + timedelta(seconds=self._portfolio_snapshot_cache_ttl_seconds)
            with self._portfolio_history_lock:
                self._portfolio_history_cache[cache_key] = PortfolioHistoryCacheEntry(context=context, stale_at=stale_at)
                self._portfolio_history_inflight.pop(cache_key, None)
                inflight.set_result(context)
            return context
        except Exception as exc:
            with self._portfolio_history_lock:
                self._portfolio_history_inflight.pop(cache_key, None)
                self._portfolio_history_cache.pop(cache_key, None)
                inflight.set_exception(exc)
            raise

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
            self._unknown_persons.set(person_id, True)
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
        portfolios, holdings, warnings = self._get_portfolio_holdings_snapshot(person_id)
        return self._build_portfolio_summary_from_snapshot(person_id, portfolios, holdings, warnings)

    def _build_portfolio_summary_from_snapshot(
        self,
        person_id: UUID,
        portfolios: list[dict],
        holdings: list[PortfolioHoldingSnapshot],
        warnings: list[str],
    ) -> PortfolioSummaryReadModel:
        total_market_value = sum(item.market_value for item in holdings)
        total_invested_value = sum(item.invested_value for item in holdings)
        total_unrealized_pnl = total_market_value - total_invested_value
        unrealized_return_pct = (
            total_unrealized_pnl / total_invested_value * 100 if total_invested_value > 0 else None
        )
        ordered_weights = sorted((item.weight for item in holdings), reverse=True)
        top_position_weight = ordered_weights[0] if ordered_weights else None
        top3_weight = sum(ordered_weights[:3]) if ordered_weights else None

        all_warnings = list(warnings)
        non_eur_currencies = {
            item.currency
            for item in holdings
            if item.currency and item.currency.upper() != "EUR"
        }
        if non_eur_currencies:
            all_warnings.append(
                "mixed_currency_no_conversion:"
                + ",".join(sorted(non_eur_currencies))
            )

        meta = {"loading": False, "error": ", ".join(all_warnings) if all_warnings else None}
        return PortfolioSummaryReadModel(
            person_id=person_id,
            as_of=datetime.now(UTC).date(),
            summary_kind="snapshot",
            return_basis="since_cost_basis",
            currency="EUR",
            market_value=round(total_market_value, 2),
            invested_value=round(total_invested_value, 2),
            unrealized_pnl=round(total_unrealized_pnl, 2),
            unrealized_return_pct=round(unrealized_return_pct, 4) if unrealized_return_pct is not None else None,
            portfolios_count=len(portfolios),
            holdings_count=len(holdings),
            top_position_weight=round(top_position_weight, 6) if top_position_weight is not None else None,
            top3_weight=round(top3_weight, 6) if top3_weight is not None else None,
            warnings=all_warnings,
            meta=meta,
        )

    def portfolio_performance(self, person_id: UUID, range_value: str = "3m") -> PortfolioPerformanceReadModel:
        history_context = self._get_portfolio_history_context(person_id, range_value=range_value)
        return self._build_portfolio_performance_from_history_context(
            person_id=person_id,
            range_value=range_value,
            history_context=history_context,
        )

    def _build_portfolio_performance_from_history_context(
        self,
        *,
        person_id: UUID,
        range_value: str,
        history_context: PortfolioHistoryContext,
    ) -> PortfolioPerformanceReadModel:
        warnings = list(history_context.snapshot_warnings)
        history_warnings = list(history_context.history_warnings)
        portfolio_points = history_context.portfolio_points
        benchmark_points = history_context.benchmark_points

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
            range_label=self._range_label(range_value),
            benchmark_symbol=self.DEFAULT_BENCHMARK_SYMBOL if benchmark_points else None,
            series=series,
            summary=PortfolioPerformanceSummary(
                summary_kind="range",
                return_basis="range_start_value",
                start_value=round(start_value, 2) if start_value is not None else None,
                end_value=round(end_value, 2) if end_value is not None else None,
                absolute_change=round(absolute_change, 2) if absolute_change is not None else None,
                return_pct=round(return_pct, 4) if return_pct is not None else None,
            ),
            meta={"loading": False, "error": ", ".join(list(dict.fromkeys(warnings + history_warnings))) or None},
        )

    def portfolio_exposures(self, person_id: UUID) -> PortfolioExposuresReadModel:
        _, holdings, _ = self._get_portfolio_holdings_snapshot(person_id)
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
        portfolios, holdings, warnings = self._get_portfolio_holdings_snapshot(person_id)
        summary = self._build_portfolio_summary_from_snapshot(person_id, portfolios, holdings, warnings)
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

    def portfolio_risk(self, person_id: UUID, range_value: str = "3m") -> PortfolioRiskReadModel:
        history_context = self._get_portfolio_history_context(person_id, range_value=range_value)
        return self._build_portfolio_risk_from_history_context(
            person_id=person_id,
            range_value=range_value,
            history_context=history_context,
        )

    def _build_portfolio_risk_from_history_context(
        self,
        *,
        person_id: UUID,
        range_value: str,
        history_context: PortfolioHistoryContext,
    ) -> PortfolioRiskReadModel:
        holdings = history_context.holdings
        warnings = list(history_context.snapshot_warnings)
        history_warnings = list(history_context.history_warnings)
        portfolio_points = history_context.portfolio_points
        top_position_weight, top3_weight, concentration_note = self._concentration_metrics(holdings)

        portfolio_return_points = self._portfolio_return_points(portfolio_points)
        portfolio_returns = [point.y for point in portfolio_return_points]
        portfolio_volatility = self._volatility(portfolio_returns)
        annualized_volatility = (portfolio_volatility * sqrt(252)) if portfolio_volatility is not None else None
        max_drawdown = self._max_drawdown(portfolio_points)
        best_day_return = max(portfolio_returns) if portfolio_returns else None
        worst_day_return = min(portfolio_returns) if portfolio_returns else None
        mean_portfolio_return = (sum(portfolio_returns) / len(portfolio_returns)) if portfolio_returns else None

        benchmark_points = history_context.benchmark_points
        benchmark_return_points = self._portfolio_return_points(sorted(benchmark_points, key=lambda point: point.x))
        aligned_portfolio_returns, aligned_benchmark_returns = self._align_return_series(
            portfolio_return_points,
            benchmark_return_points,
        )
        aligned_points = min(len(aligned_portfolio_returns), len(aligned_benchmark_returns))
        beta, correlation = self._compute_beta_and_correlation(aligned_portfolio_returns, aligned_benchmark_returns)
        tracking_error = None
        annualized_tracking_error = None
        information_ratio = None
        active_return = None
        if aligned_portfolio_returns and aligned_benchmark_returns:
            size = min(len(aligned_portfolio_returns), len(aligned_benchmark_returns))
            active = [
                aligned_portfolio_returns[-size + idx] - aligned_benchmark_returns[-size + idx]
                for idx in range(size)
            ]
            tracking_error = self._volatility(active)
            annualized_tracking_error = (tracking_error * sqrt(252)) if tracking_error is not None else None
            if annualized_tracking_error is not None and annualized_tracking_error > 0:
                mean_active = sum(active) / len(active)
                information_ratio = (mean_active * 252) / annualized_tracking_error
                mean_benchmark = sum(aligned_benchmark_returns) / len(aligned_benchmark_returns)
                if mean_portfolio_return is not None:
                    active_return = (mean_portfolio_return - mean_benchmark) * 252

        downside_returns = [value for value in portfolio_returns if value < 0]
        downside_vol = self._volatility(downside_returns)
        annualized_downside_vol = (downside_vol * sqrt(252)) if downside_vol is not None else None
        sharpe_ratio = None
        sortino_ratio = None
        if mean_portfolio_return is not None and annualized_volatility is not None and annualized_volatility > 0:
            sharpe_ratio = (mean_portfolio_return * 252) / annualized_volatility
        if mean_portfolio_return is not None and annualized_downside_vol is not None and annualized_downside_vol > 0:
            sortino_ratio = (mean_portfolio_return * 252) / annualized_downside_vol

        if aligned_points < 2:
            beta = None
            correlation = None
            tracking_error = None
            annualized_tracking_error = None
            information_ratio = None
            active_return = None
            history_warnings.append("insufficient_benchmark_overlap")

        return PortfolioRiskReadModel(
            person_id=person_id,
            as_of=datetime.now(UTC).date(),
            range=range_value,
            range_label=self._range_label(range_value),
            methodology="daily_returns_on_range",
            benchmark_relation="relative_to_benchmark",
            benchmark_symbol=self.DEFAULT_BENCHMARK_SYMBOL if aligned_benchmark_returns else None,
            portfolio_volatility=round(portfolio_volatility, 6) if portfolio_volatility is not None else None,
            max_drawdown=round(max_drawdown, 6) if max_drawdown is not None else None,
            correlation=round(correlation, 6) if correlation is not None else None,
            beta=round(beta, 6) if beta is not None else None,
            tracking_error=round(tracking_error, 6) if tracking_error is not None else None,
            annualized_volatility=round(annualized_volatility, 6) if annualized_volatility is not None else None,
            annualized_tracking_error=round(annualized_tracking_error, 6) if annualized_tracking_error is not None else None,
            sharpe_ratio=round(sharpe_ratio, 6) if sharpe_ratio is not None else None,
            sortino_ratio=round(sortino_ratio, 6) if sortino_ratio is not None else None,
            information_ratio=round(information_ratio, 6) if information_ratio is not None else None,
            active_return=round(active_return, 6) if active_return is not None else None,
            best_day_return=round(best_day_return, 6) if best_day_return is not None else None,
            worst_day_return=round(worst_day_return, 6) if worst_day_return is not None else None,
            aligned_points=aligned_points,
            top_position_weight=round(top_position_weight, 6) if top_position_weight is not None else None,
            top3_weight=round(top3_weight, 6) if top3_weight is not None else None,
            concentration_note=concentration_note,
            meta={"loading": False, "error": ", ".join(list(dict.fromkeys(warnings + history_warnings))) or None},
        )

    @staticmethod
    def _direction(value: float | None) -> str:
        if value is None or value == 0:
            return "neutral"
        return "positive" if value > 0 else "negative"

    @staticmethod
    def _portfolio_range_return_pct(points: list[ChartPoint]) -> float | None:
        if len(points) < 2:
            return None
        start_value = points[0].y
        end_value = points[-1].y
        if start_value <= 0:
            return None
        return (end_value - start_value) / start_value * 100

    def _build_position_attribution(
        self,
        history_context: PortfolioHistoryContext,
    ) -> tuple[list[PortfolioAttributionPosition], list[str]]:
        holdings = history_context.holdings
        history_by_symbol = history_context.history_by_symbol
        warnings: list[str] = []

        holdings_by_symbol: dict[str, list[PortfolioHoldingSnapshot]] = defaultdict(list)
        unknown_holdings: list[PortfolioHoldingSnapshot] = []
        for holding in holdings:
            if holding.symbol:
                holdings_by_symbol[holding.symbol].append(holding)
            else:
                unknown_holdings.append(holding)

        points_by_date: dict[str, dict[str, float]] = defaultdict(dict)
        for symbol in holdings_by_symbol:
            points = history_by_symbol.get(symbol, [])
            if len(points) < 2:
                warnings.append(f"attribution_history_missing:{symbol}")
                continue
            for point in points:
                points_by_date[point.x][symbol] = point.y

        ordered_days = sorted(points_by_date)
        contribution_by_symbol: dict[str, float] = defaultdict(float)
        periods_by_symbol: dict[str, int] = defaultdict(int)

        for idx in range(1, len(ordered_days)):
            previous_day = ordered_days[idx - 1]
            current_day = ordered_days[idx]
            previous_values: dict[str, float] = {}
            current_values: dict[str, float] = {}

            for symbol, position_items in holdings_by_symbol.items():
                previous_close = points_by_date[previous_day].get(symbol)
                current_close = points_by_date[current_day].get(symbol)
                if previous_close is None or current_close is None or previous_close <= 0:
                    continue
                quantity = sum(item.quantity for item in position_items)
                previous_values[symbol] = previous_close * quantity
                current_values[symbol] = current_close * quantity

            previous_portfolio_value = sum(previous_values.values())
            if previous_portfolio_value <= 0:
                continue

            for symbol, previous_position_value in previous_values.items():
                current_position_value = current_values.get(symbol)
                if current_position_value is None or previous_position_value <= 0:
                    continue
                asset_return = (current_position_value - previous_position_value) / previous_position_value
                contribution_by_symbol[symbol] += (previous_position_value / previous_portfolio_value) * asset_return * 100
                periods_by_symbol[symbol] += 1

        positions: list[PortfolioAttributionPosition] = []
        for symbol, position_items in holdings_by_symbol.items():
            representative = max(position_items, key=lambda item: item.market_value)
            points = history_by_symbol.get(symbol, [])
            return_pct = None
            if len(points) >= 2 and points[0].y > 0:
                return_pct = ((points[-1].y - points[0].y) / points[0].y) * 100
            contribution = contribution_by_symbol.get(symbol, 0.0)
            positions.append(
                PortfolioAttributionPosition(
                    symbol=symbol,
                    label=representative.display_name or symbol,
                    contribution_pct_points=round(contribution, 6),
                    return_pct=round(return_pct, 4) if return_pct is not None else None,
                    weight=round(sum(item.weight for item in position_items), 6),
                    market_value=round(sum(item.market_value for item in position_items), 2),
                    sector=representative.sector or "UNKNOWN",
                    country=representative.country or "UNKNOWN",
                    currency=representative.currency or "UNKNOWN",
                    periods_used=periods_by_symbol.get(symbol, 0),
                )
            )

        for holding in unknown_holdings:
            warnings.append("attribution_missing_symbol")
            positions.append(
                PortfolioAttributionPosition(
                    symbol="",
                    label=holding.display_name or holding.holding_id or "UNKNOWN",
                    contribution_pct_points=0.0,
                    return_pct=None,
                    weight=round(holding.weight, 6),
                    market_value=round(holding.market_value, 2),
                    sector=holding.sector or "UNKNOWN",
                    country=holding.country or "UNKNOWN",
                    currency=holding.currency or "UNKNOWN",
                    periods_used=0,
                )
            )

        return positions, list(dict.fromkeys(warnings))

    def _position_to_attribution_item(self, position: PortfolioAttributionPosition) -> PortfolioAttributionItem:
        return PortfolioAttributionItem(
            label=position.label,
            symbol=position.symbol or None,
            contribution_pct_points=position.contribution_pct_points,
            return_pct=position.return_pct,
            weight=position.weight,
            market_value=position.market_value,
            direction=self._direction(position.contribution_pct_points),
        )

    def _aggregate_attribution(
        self,
        positions: list[PortfolioAttributionPosition],
        label_getter,
    ) -> list[PortfolioAttributionItem]:
        grouped: dict[str, list[PortfolioAttributionPosition]] = defaultdict(list)
        for position in positions:
            grouped[label_getter(position)].append(position)

        items: list[PortfolioAttributionItem] = []
        for label, group in grouped.items():
            contribution = sum(item.contribution_pct_points for item in group)
            weight = sum(item.weight for item in group)
            market_value = sum(item.market_value for item in group)
            weighted_return_sum = sum(
                item.return_pct * item.weight
                for item in group
                if item.return_pct is not None and item.weight > 0
            )
            return_weight = sum(item.weight for item in group if item.return_pct is not None and item.weight > 0)
            return_pct = (weighted_return_sum / return_weight) if return_weight > 0 else None
            items.append(
                PortfolioAttributionItem(
                    label=label,
                    contribution_pct_points=round(contribution, 6),
                    return_pct=round(return_pct, 4) if return_pct is not None else None,
                    weight=round(weight, 6),
                    market_value=round(market_value, 2),
                    direction=self._direction(contribution),
                )
            )

        return sorted(items, key=lambda item: abs(item.contribution_pct_points), reverse=True)

    def portfolio_attribution(self, person_id: UUID, range_value: str = "3m") -> PortfolioAttributionReadModel:
        history_context = self._get_portfolio_history_context(person_id, range_value=range_value)
        positions, attribution_warnings = self._build_position_attribution(history_context)
        by_position = sorted(
            [self._position_to_attribution_item(position) for position in positions],
            key=lambda item: abs(item.contribution_pct_points),
            reverse=True,
        )
        total_contribution_pct_points = round(sum(item.contribution_pct_points for item in by_position), 6)
        portfolio_return_pct = self._portfolio_range_return_pct(history_context.portfolio_points)
        residual_pct_points = (
            round(portfolio_return_pct - total_contribution_pct_points, 6)
            if portfolio_return_pct is not None
            else None
        )
        covered_positions = sum(1 for position in positions if position.periods_used > 0)
        warnings = self._collect_warnings(
            history_context.snapshot_warnings,
            history_context.history_warnings,
            attribution_warnings,
        )

        return PortfolioAttributionReadModel(
            person_id=person_id,
            as_of=datetime.now(UTC).date(),
            range=range_value,
            range_label=self._range_label(range_value),
            benchmark_symbol=self.DEFAULT_BENCHMARK_SYMBOL if history_context.benchmark_points else None,
            summary=PortfolioAttributionSummary(
                portfolio_return_pct=round(portfolio_return_pct, 4) if portfolio_return_pct is not None else None,
                total_contribution_pct_points=total_contribution_pct_points,
                residual_pct_points=residual_pct_points,
                covered_positions=covered_positions,
                total_positions=len(positions),
                unattributed_positions=max(0, len(positions) - covered_positions),
            ),
            by_position=by_position,
            by_sector=self._aggregate_attribution(positions, lambda item: item.sector),
            by_country=self._aggregate_attribution(positions, lambda item: item.country),
            by_currency=self._aggregate_attribution(positions, lambda item: item.currency),
            warnings=warnings,
            meta={"loading": False, "error": ", ".join(warnings) or None},
        )

    def portfolio_contributors(self, person_id: UUID, range_value: str = "3m") -> PortfolioContributorsReadModel:
        history_context = self._get_portfolio_history_context(person_id, range_value=range_value)
        return self._build_portfolio_contributors_from_history_context(
            person_id=person_id,
            range_value=range_value,
            history_context=history_context,
        )

    def _build_portfolio_contributors_from_history_context(
        self,
        *,
        person_id: UUID,
        range_value: str,
        history_context: PortfolioHistoryContext,
    ) -> PortfolioContributorsReadModel:
        holdings = history_context.holdings
        history_by_symbol = dict(history_context.history_by_symbol)
        history_warnings: list[str] = list(history_context.history_warnings)

        points_by_date: dict[str, dict[str, float]] = defaultdict(dict)
        symbols_with_history: set[str] = set()
        for symbol, points in history_by_symbol.items():
            if len(points) < 2:
                history_warnings.append(f"contributor_history_missing:{symbol}")
                continue
            symbols_with_history.add(symbol)
            for point in points:
                points_by_date[point.x][symbol] = point.y

        ordered_days = sorted(points_by_date)
        contribution_by_symbol: dict[str, float] = defaultdict(float)
        periods_by_symbol: dict[str, int] = defaultdict(int)

        holdings_by_symbol: dict[str, list[PortfolioHoldingSnapshot]] = defaultdict(list)
        for holding in holdings:
            if holding.symbol:
                holdings_by_symbol[holding.symbol].append(holding)

        for symbol in holdings_by_symbol:
            if symbol not in history_by_symbol:
                history_warnings.append(f"contributor_history_missing:{symbol}")

        for idx in range(1, len(ordered_days)):
            prev_day = ordered_days[idx - 1]
            day = ordered_days[idx]
            prev_values: dict[str, float] = {}
            curr_values: dict[str, float] = {}
            for symbol, position_items in holdings_by_symbol.items():
                prev_close = points_by_date[prev_day].get(symbol)
                curr_close = points_by_date[day].get(symbol)
                if prev_close is None or curr_close is None or prev_close <= 0:
                    continue
                quantity = sum(item.quantity for item in position_items)
                prev_values[symbol] = prev_close * quantity
                curr_values[symbol] = curr_close * quantity
            prev_portfolio_value = sum(prev_values.values())
            if prev_portfolio_value <= 0:
                continue
            for symbol, prev_position_value in prev_values.items():
                curr_position_value = curr_values.get(symbol)
                if curr_position_value is None or prev_position_value <= 0:
                    continue
                asset_return = (curr_position_value - prev_position_value) / prev_position_value
                contribution = (prev_position_value / prev_portfolio_value) * asset_return
                contribution_by_symbol[symbol] += contribution
                periods_by_symbol[symbol] += 1

        def to_item(item: PortfolioHoldingSnapshot) -> PortfolioContributorItem:
            symbol = item.symbol or ""
            contribution_return = contribution_by_symbol.get(symbol)
            periods_used = periods_by_symbol.get(symbol, 0)
            history_available = symbol in symbols_with_history
            contribution_weighted = item.weight * item.unrealized_pnl
            direction = "positive" if (contribution_return or 0.0) >= 0 else "negative"
            return PortfolioContributorItem(
                symbol=item.symbol,
                display_name=item.display_name,
                market_value=round(item.market_value, 2),
                weight=round(item.weight, 6),
                unrealized_pnl=round(item.unrealized_pnl, 2),
                contribution_weighted=round(contribution_weighted, 6),
                direction=direction,
                contribution_return=round(contribution_return, 10) if contribution_return is not None else None,
                contribution_pct_points=round((contribution_return or 0.0) * 100, 6) if contribution_return is not None else None,
                periods_used=periods_used,
                history_available=history_available and periods_used > 0,
            )

        contributor_items = [to_item(item) for item in holdings]
        top_positive = [item for item in sorted(contributor_items, key=lambda x: x.contribution_return or 0.0, reverse=True) if (item.contribution_return or 0.0) > 0][:5]
        top_negative = [item for item in sorted(contributor_items, key=lambda x: x.contribution_return or 0.0) if (item.contribution_return or 0.0) < 0][:5]
        total_contribution_return = sum((item.contribution_return or 0.0) for item in contributor_items if item.contribution_return is not None)

        deduped_warnings = list(dict.fromkeys(history_warnings))
        return PortfolioContributorsReadModel(
            person_id=person_id,
            as_of=datetime.now(UTC).date(),
            range=range_value,
            range_label=self._range_label(range_value),
            summary_kind="range",
            return_basis="range_contribution",
            methodology="static_quantity_return_contribution",
            total_contribution_return=round(total_contribution_return, 10),
            total_contribution_pct_points=round(total_contribution_return * 100, 6),
            warnings=deduped_warnings,
            top_contributors=top_positive,
            top_detractors=top_negative,
            meta={"loading": False, "error": ", ".join(deduped_warnings) or None},
        )

    def portfolio_data_coverage(self, person_id: UUID) -> PortfolioDataCoverageReadModel:
        _, holdings, warnings = self._get_portfolio_holdings_snapshot(person_id)
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

    @staticmethod
    def _collect_warnings(*warning_lists: list[str]) -> list[str]:
        collected: list[str] = []
        for warning_list in warning_lists:
            collected.extend(warning_list)
        return list(dict.fromkeys(collected))

    def portfolio_dashboard(self, person_id: UUID, range_value: str = "3m") -> PortfolioDashboardReadModel:
        entry = self._get_or_build_portfolio_dashboard_entry(person_id, range_value=range_value)
        payload = entry.payload.model_copy(deep=True)
        self._apply_generated_at_to_model_meta(payload, entry.generated_at)
        return payload

    def _dashboard_cache_key(self, person_id: UUID, range_value: str) -> tuple[UUID, str]:
        return (person_id, range_value)

    def _apply_generated_at_to_model_meta(self, model: object, generated_at: datetime) -> None:
        meta = getattr(model, "meta", None)
        if meta is not None and hasattr(meta, "generated_at"):
            meta.generated_at = generated_at

    def _apply_generated_at_to_dashboard_meta(
        self,
        payload: PortfolioDashboardReadModel,
        generated_at: datetime,
    ) -> PortfolioDashboardReadModel:
        self._apply_generated_at_to_model_meta(payload, generated_at)
        self._apply_generated_at_to_model_meta(payload.summary, generated_at)
        self._apply_generated_at_to_model_meta(payload.performance, generated_at)
        self._apply_generated_at_to_model_meta(payload.exposures, generated_at)
        self._apply_generated_at_to_model_meta(payload.holdings, generated_at)
        self._apply_generated_at_to_model_meta(payload.risk, generated_at)
        self._apply_generated_at_to_model_meta(payload.coverage, generated_at)
        self._apply_generated_at_to_model_meta(payload.contributors, generated_at)
        if payload.attribution is not None:
            self._apply_generated_at_to_model_meta(payload.attribution, generated_at)
        return payload

    def _get_or_build_portfolio_dashboard_entry(
        self,
        person_id: UUID,
        range_value: str,
    ) -> PortfolioDashboardCacheEntry:
        key = self._dashboard_cache_key(person_id, range_value)
        now = datetime.now(UTC)
        owner = False
        with self._portfolio_dashboard_lock:
            cached = self._portfolio_dashboard_cache.get(key)
            if cached is not None and cached.stale_at > now:
                return cached
            inflight = self._portfolio_dashboard_inflight.get(key)
            if inflight is None:
                inflight = Future()
                self._portfolio_dashboard_inflight[key] = inflight
                owner = True

        if owner:
            try:
                generated_at = datetime.now(UTC)
                payload = self._build_portfolio_dashboard(person_id, range_value=range_value)
                payload = self._apply_generated_at_to_dashboard_meta(payload, generated_at)
                entry = PortfolioDashboardCacheEntry(
                    payload=payload,
                    generated_at=generated_at,
                    stale_at=generated_at + timedelta(seconds=self._portfolio_dashboard_cache_ttl_seconds),
                )
                with self._portfolio_dashboard_lock:
                    self._portfolio_dashboard_cache[key] = entry
                    if len(self._portfolio_dashboard_cache) > self.PORTFOLIO_DASHBOARD_CACHE_MAX_SIZE:
                        oldest_key = min(
                            self._portfolio_dashboard_cache,
                            key=lambda cache_key: self._portfolio_dashboard_cache[cache_key].generated_at,
                        )
                        self._portfolio_dashboard_cache.pop(oldest_key, None)
                    self._portfolio_dashboard_inflight.pop(key, None)
                inflight.set_result(entry)
                return entry
            except Exception as exc:
                with self._portfolio_dashboard_lock:
                    self._portfolio_dashboard_inflight.pop(key, None)
                inflight.set_exception(exc)
                raise
        return inflight.result()

    def _build_portfolio_dashboard(self, person_id: UUID, range_value: str = "3m") -> PortfolioDashboardReadModel:
        portfolios, holdings, snapshot_warnings = self._get_portfolio_holdings_snapshot(person_id)
        history_context = self._get_portfolio_history_context(person_id, range_value=range_value)

        summary = self._build_portfolio_summary_from_snapshot(person_id, portfolios, holdings, snapshot_warnings)
        performance = self._build_portfolio_performance_from_history_context(
            person_id=person_id,
            range_value=range_value,
            history_context=history_context,
        )

        by_position = self._aggregate_exposure(holdings, lambda item: item.display_name or item.symbol or "UNKNOWN")
        by_sector = self._aggregate_exposure(holdings, lambda item: item.sector or "UNKNOWN")
        by_country = self._aggregate_exposure(holdings, lambda item: item.country or "UNKNOWN")
        by_currency = self._aggregate_exposure(holdings, lambda item: item.currency or "UNKNOWN")
        exposures = PortfolioExposuresReadModel(
            person_id=person_id,
            by_position=by_position,
            by_sector=by_sector,
            by_country=by_country,
            by_currency=by_currency,
        )

        holding_items = [
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
        holdings_model = PortfolioHoldingsReadModel(
            person_id=person_id,
            as_of=datetime.now(UTC).date(),
            currency="EUR",
            items=holding_items,
            summary=summary,
            meta={"loading": False, "error": ", ".join(snapshot_warnings) if snapshot_warnings else None},
        )

        top_position_weight, top3_weight, concentration_note = self._concentration_metrics(holdings)
        risk = self._build_portfolio_risk_from_history_context(
            person_id=person_id,
            range_value=range_value,
            history_context=history_context,
        )
        risk.top_position_weight = round(top_position_weight, 6) if top_position_weight is not None else None
        risk.top3_weight = round(top3_weight, 6) if top3_weight is not None else None
        risk.concentration_note = concentration_note

        contributors = self._build_portfolio_contributors_from_history_context(
            person_id=person_id,
            range_value=range_value,
            history_context=history_context,
        )
        attribution = self.portfolio_attribution(person_id, range_value=range_value)

        counters, coverage_warnings = self._coverage_summary(holdings, snapshot_warnings)
        coverage = PortfolioDataCoverageReadModel(
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

        warnings = self._collect_warnings(
            snapshot_warnings,
            history_context.snapshot_warnings,
            history_context.history_warnings,
            coverage.warnings,
        )
        errors = [
            model.meta.error
            for model in [summary, performance, exposures, holdings_model, risk, coverage, contributors, attribution]
            if model.meta.error
        ]
        return PortfolioDashboardReadModel(
            person_id=person_id,
            as_of=datetime.now(UTC).date(),
            range=range_value,
            benchmark_symbol=performance.benchmark_symbol,
            summary=summary,
            performance=performance,
            exposures=exposures,
            holdings=holdings_model,
            risk=risk,
            coverage=coverage,
            contributors=contributors,
            attribution=attribution,
            meta={
                "loading": False,
                "error": "; ".join(list(dict.fromkeys(errors))) or None,
                "warnings": warnings,
            },
        )
