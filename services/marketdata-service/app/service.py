from __future__ import annotations

from datetime import date, timedelta
import logging
import threading
import time
from typing import Any, cast

from app.clients.fmp_client import FMPClient
from app.clients.yfinance_client import YFinanceClient
from app.models import (
    BadRequestError,
    BatchHistoryItem,
    BatchHistoryResponse,
    BatchPriceItem,
    BatchPricesResponse,
    BalanceSheetStatement,
    CacheStatus,
    FinancialStatements,
    FinancialsCacheDocument,
    FinancialsPeriod,
    FMPInstrumentProfile,
    HistoryRange,
    HoldingsSummaryItem,
    HoldingsSummaryResponse,
    InstrumentHistoryPoint,
    InstrumentHistoryResponse,
    InstrumentPriceRefreshResponse,
    InstrumentProfile,
    InstrumentSearchItem,
    InstrumentSearchResponse,
    MetaWarning,
    NotFoundError,
    PersistenceOnlyInstrumentProfile,
    PriceHistoryCacheDocument,
    PriceHistoryRow,
    UpstreamServiceError,
    utcnow,
)
from app.repositories import (
    CurrentPriceCacheRepository,
    FinancialsCacheRepository,
    InMemoryCurrentPriceCacheRepository,
    InMemoryFinancialsCacheRepository,
    InMemoryInstrumentProfileCacheRepository,
    InMemoryPriceHistoryCacheRepository,
    InstrumentProfileCacheRepository,
    PriceHistoryCacheRepository,
)
from app.ttl_lru_cache import TtlLruCache

LOGGER = logging.getLogger(__name__)


class MarketDataService:
    MAX_SEARCH_LIMIT = 20
    VALID_HISTORY_RANGES: tuple[HistoryRange, ...] = ("1m", "3m", "6m", "ytd", "1y", "max")
    PRICE_CACHE_STALE_AFTER = timedelta(hours=20)
    HISTORY_STALE_AFTER = timedelta(hours=24)
    SEARCH_CACHE_MAX_SIZE = 256
    SEARCH_CACHE_TTL_SECONDS = 86400
    SNAPSHOT_CACHE_MAX_SIZE = 512
    SNAPSHOT_CACHE_TTL_SECONDS = 300
    METRICS_CACHE_MAX_SIZE = 512
    METRICS_CACHE_TTL_SECONDS = 300
    FUNDAMENTALS_CACHE_MAX_SIZE = 512
    FUNDAMENTALS_CACHE_TTL_SECONDS = 3600
    BENCHMARK_CATALOG_CACHE_MAX_SIZE = 8
    BENCHMARK_CATALOG_CACHE_TTL_SECONDS = 86400
    NEGATIVE_REFRESH_CACHE_MAX_SIZE = 2048
    NEGATIVE_REFRESH_CACHE_TTL_SECONDS = 30

    def __init__(
        self,
        *,
        fmp_client: FMPClient,
        yfinance_client: YFinanceClient,
        profile_repository: InstrumentProfileCacheRepository | InMemoryInstrumentProfileCacheRepository,
        current_price_repository: CurrentPriceCacheRepository | InMemoryCurrentPriceCacheRepository,
        price_history_repository: PriceHistoryCacheRepository | InMemoryPriceHistoryCacheRepository,
        financials_repository: FinancialsCacheRepository | InMemoryFinancialsCacheRepository,
        cache_enabled: bool,
        profile_cache_ttl_seconds: int,
        financials_cache_ttl_seconds: int,
    ) -> None:
        self._fmp_client = fmp_client
        self._yfinance_client = yfinance_client
        self._profile_repository = profile_repository
        self._current_price_repository = current_price_repository
        self._price_history_repository = price_history_repository
        self._financials_repository = financials_repository
        self._cache_enabled = cache_enabled
        self._profile_cache_ttl_seconds = profile_cache_ttl_seconds
        self._financials_cache_ttl_seconds = financials_cache_ttl_seconds
        self._search_cache = TtlLruCache(max_size=self.SEARCH_CACHE_MAX_SIZE, ttl_seconds=self.SEARCH_CACHE_TTL_SECONDS)
        self._snapshot_cache = TtlLruCache(max_size=self.SNAPSHOT_CACHE_MAX_SIZE, ttl_seconds=self.SNAPSHOT_CACHE_TTL_SECONDS)
        self._metrics_cache = TtlLruCache(max_size=self.METRICS_CACHE_MAX_SIZE, ttl_seconds=self.METRICS_CACHE_TTL_SECONDS)
        self._fundamentals_cache = TtlLruCache(max_size=self.FUNDAMENTALS_CACHE_MAX_SIZE, ttl_seconds=self.FUNDAMENTALS_CACHE_TTL_SECONDS)
        self._benchmark_catalog_cache = TtlLruCache(
            max_size=self.BENCHMARK_CATALOG_CACHE_MAX_SIZE,
            ttl_seconds=self.BENCHMARK_CATALOG_CACHE_TTL_SECONDS,
        )
        self._negative_refresh_cache = TtlLruCache(
            max_size=self.NEGATIVE_REFRESH_CACHE_MAX_SIZE,
            ttl_seconds=self.NEGATIVE_REFRESH_CACHE_TTL_SECONDS,
        )
        self._inflight_locks: dict[tuple[str, str], threading.Lock] = {}
        self._inflight_guard = threading.Lock()

    def search_instruments(self, query: str, limit: int) -> InstrumentSearchResponse:
        method_started_at = time.perf_counter()
        LOGGER.info('search_trace marketdata_service_enter query="%s" limit=%s', query, limit)
        cleaned_query = query.strip()
        if len(cleaned_query) < 1:
            duration_ms = round((time.perf_counter() - method_started_at) * 1000, 2)
            LOGGER.info(
                "search_trace marketdata_service_exit success=false duration_ms=%s reason=invalid_query query=%r",
                duration_ms,
                query,
            )
            raise BadRequestError("query must contain at least 1 character")
        bounded_limit = max(1, min(limit, self.MAX_SEARCH_LIMIT))

        cache_key = (cleaned_query.lower(), bounded_limit)
        LOGGER.info(
            'search_trace marketdata_service_before_cache_check query="%s" bounded_limit=%s cache_enabled=%s',
            cleaned_query,
            bounded_limit,
            self._cache_enabled,
        )
        if self._cache_enabled:
            cached_response = self._search_cache.get(cache_key)
            if cached_response is not None:
                duration_ms = round((time.perf_counter() - method_started_at) * 1000, 2)
                LOGGER.info(
                    'search_trace marketdata_service_cache_hit query="%s" bounded_limit=%s total=%s duration_ms=%s',
                    cleaned_query,
                    bounded_limit,
                    cached_response.total,
                    duration_ms,
                )
                return cached_response
        LOGGER.info(
            'search_trace marketdata_service_cache_miss query="%s" bounded_limit=%s',
            cleaned_query,
            bounded_limit,
        )

        fmp_started_at = time.perf_counter()
        LOGGER.info('search_trace marketdata_service_before_fmp query="%s" limit=%s', cleaned_query, bounded_limit)
        try:
            rows = self._fmp_client.search_name(query=cleaned_query, limit=bounded_limit)
            fmp_duration_ms = round((time.perf_counter() - fmp_started_at) * 1000, 2)
            LOGGER.info(
                'search_trace marketdata_service_after_fmp success=true query="%s" limit=%s duration_ms=%s row_count=%s',
                cleaned_query,
                bounded_limit,
                fmp_duration_ms,
                len(rows),
            )
        except Exception:
            fmp_duration_ms = round((time.perf_counter() - fmp_started_at) * 1000, 2)
            LOGGER.exception(
                'search_trace marketdata_service_after_fmp success=false query="%s" limit=%s duration_ms=%s',
                cleaned_query,
                bounded_limit,
                fmp_duration_ms,
            )
            raise
        items = [
            InstrumentSearchItem.model_validate(
                {
                    "symbol": row.get("symbol", ""),
                    "company_name": row.get("name") or "",
                    "display_name": row.get("name") or "",
                    "currency": row.get("currency"),
                    "exchange": row.get("exchange"),
                    "exchange_full_name": row.get("exchangeFullName"),
                }
            )
            for row in rows
            if row.get("symbol") and row.get("name")
        ]
        response = InstrumentSearchResponse(query=cleaned_query, items=items, total=len(items))
        if self._cache_enabled:
            self._search_cache.set(cache_key, response)
        total_duration_ms = round((time.perf_counter() - method_started_at) * 1000, 2)
        LOGGER.info(
            'search_trace marketdata_service_exit success=true query="%s" bounded_limit=%s total=%s duration_ms=%s',
            cleaned_query,
            bounded_limit,
            response.total,
            total_duration_ms,
        )
        return response

    def get_instrument_profile(self, symbol: str) -> InstrumentProfile:
        normalized = symbol.strip().upper()
        if not normalized:
            raise BadRequestError("symbol must not be empty")

        try:
            cached = self._profile_repository.get(normalized)
        except Exception:
            LOGGER.warning("profile cache read failed for symbol '%s'", normalized, exc_info=True)
            cached = None

        if cached is not None and self._is_fresh(cached.fetched_at):
            return cached.visible_profile

        rows = self._fmp_client.profile(symbol=normalized)
        if not rows:
            raise NotFoundError(f"Instrument '{normalized}' not found")

        parsed = FMPInstrumentProfile.model_validate(rows[0] | {"symbol": normalized})
        visible_profile = self._build_visible_profile(parsed)
        persistence_only_profile = self._build_persistence_profile(parsed)

        try:
            self._profile_repository.upsert(
                normalized,
                visible_profile=visible_profile.model_dump(),
                persistence_only_profile=persistence_only_profile.model_dump(),
            )
        except Exception:
            LOGGER.warning("profile cache write failed for symbol '%s'", normalized, exc_info=True)
        return visible_profile

    def get_holdings_summary(self, symbols_csv: str) -> HoldingsSummaryResponse:
        symbols = self._parse_symbols_csv(symbols_csv)
        items: list[HoldingsSummaryItem] = []
        warnings: list[MetaWarning] = []
        errors: list[MetaWarning] = []

        for symbol in symbols:
            try:
                profile_payload = self._get_profile_with_swr(symbol)
                price_payload = self._get_price_with_swr(symbol)
                cache_status = self._combine_cache_status(profile_payload["cache_status"], price_payload["cache_status"])
                items.append(
                    HoldingsSummaryItem(
                        symbol=symbol,
                        name=profile_payload.get("name"),
                        sector=profile_payload.get("sector"),
                        country=profile_payload.get("country"),
                        currency=profile_payload.get("currency"),
                        current_price=price_payload.get("current_price"),
                        provider=price_payload.get("provider") or profile_payload.get("provider"),
                        as_of=price_payload.get("as_of"),
                        coverage="profile+price",
                        cache_status=cache_status,
                    )
                )
            except Exception as exc:
                errors.append(MetaWarning(symbol=symbol, code="symbol_unavailable", message=str(exc)))
                items.append(HoldingsSummaryItem(symbol=symbol, coverage="none", cache_status="cache_miss_pending"))

        return HoldingsSummaryResponse(
            items=items,
            requested_symbols=symbols,
            total=len(items),
            meta={"warnings": [warning.model_dump() for warning in warnings], "errors": [error.model_dump() for error in errors]},
        )

    def get_batch_prices(self, symbols_csv: str) -> BatchPricesResponse:
        symbols = self._parse_symbols_csv(symbols_csv)
        items: list[BatchPriceItem] = []
        warnings: list[MetaWarning] = []
        errors: list[MetaWarning] = []
        for symbol in symbols:
            try:
                payload = self._get_price_with_swr(symbol)
                items.append(
                    BatchPriceItem(
                        symbol=symbol,
                        current_price=payload.get("current_price"),
                        trade_date=payload.get("as_of"),
                        price_source=payload.get("price_source"),
                        fetched_at=payload.get("fetched_at"),
                        cache_status=payload["cache_status"],
                    )
                )
            except Exception as exc:
                errors.append(MetaWarning(symbol=symbol, code="symbol_unavailable", message=str(exc)))
                items.append(BatchPriceItem(symbol=symbol, cache_status="cache_miss_pending"))
        return BatchPricesResponse(
            items=items,
            requested_symbols=symbols,
            total=len(items),
            meta={"warnings": [warning.model_dump() for warning in warnings], "errors": [error.model_dump() for error in errors]},
        )

    def get_batch_history(self, symbols_csv: str, range_value: str = "3m") -> BatchHistoryResponse:
        symbols = self._parse_symbols_csv(symbols_csv)
        if range_value not in self.VALID_HISTORY_RANGES:
            raise BadRequestError("range must be one of: 1m, 3m, 6m, ytd, 1y, max")

        items: list[BatchHistoryItem] = []
        errors: list[MetaWarning] = []
        for symbol in symbols:
            try:
                payload = self._get_history_with_swr(symbol, range_value)
                items.append(
                    BatchHistoryItem(
                        symbol=symbol,
                        range=range_value,  # type: ignore[arg-type]
                        points=payload["points"],
                        cache_present=payload["cache_present"],
                        updated_at=payload["updated_at"],
                        cache_status=payload["cache_status"],
                    )
                )
            except Exception as exc:
                errors.append(MetaWarning(symbol=symbol, code="symbol_unavailable", message=str(exc)))
                items.append(BatchHistoryItem(symbol=symbol, range=range_value, points=[], cache_present=False, cache_status="cache_miss_pending"))  # type: ignore[arg-type]

        return BatchHistoryResponse(
            items=items,
            requested_symbols=symbols,
            total=len(items),
            meta={"warnings": [], "errors": [error.model_dump() for error in errors]},
        )

    def get_instrument_snapshot(self, symbol: str) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        if self._cache_enabled:
            cached = self._snapshot_cache.get(normalized)
            if cached is not None:
                return cached

        profile = self.get_instrument_profile(normalized)
        price_refresh = self.refresh_instrument_price(normalized)
        payload = {
            "symbol": normalized,
            "name": profile.company_name,
            "sector": profile.sector,
            "country": profile.country,
            "currency": profile.currency,
            "current_price": price_refresh.current_price,
            "provider": "fmp+yfinance",
            "as_of": price_refresh.trade_date,
            "coverage": "profile+price",
        }
        if self._cache_enabled:
            self._snapshot_cache.set(normalized, payload)
        return payload

    def get_instrument_fundamentals(self, symbol: str) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        if self._cache_enabled:
            cached = self._fundamentals_cache.get(normalized)
            if cached is not None:
                return cached

        profile = self.get_instrument_profile(normalized)
        payload = {
            "symbol": normalized,
            "company_name": profile.company_name,
            "sector": profile.sector,
            "industry": profile.industry,
            "country": profile.country,
            "website": profile.website,
            "description": profile.description,
            "currency": profile.currency,
            "source": "profile_cache",
        }
        if self._cache_enabled:
            self._fundamentals_cache.set(normalized, payload)
        return payload

    def get_instrument_metrics(self, symbol: str) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        if self._cache_enabled:
            cached = self._metrics_cache.get(normalized)
            if cached is not None:
                return cached

        profile = self.get_instrument_profile(normalized)
        history = self.get_instrument_history(normalized, "1y")
        closes = [point.close for point in history.points]
        returns = []
        for idx in range(1, len(closes)):
            prev = closes[idx - 1]
            curr = closes[idx]
            if prev != 0:
                returns.append((curr - prev) / prev)
        avg_return = (sum(returns) / len(returns)) if returns else None
        payload = {
            "symbol": normalized,
            "market_cap": self._extract_market_cap(normalized),
            "beta": self._extract_beta(normalized),
            "last_price": closes[-1] if closes else None,
            "avg_daily_return_1y": avg_return,
            "series_points_1y": len(closes),
            "currency": profile.currency,
            "source": "profile+history_cache",
        }
        if self._cache_enabled:
            self._metrics_cache.set(normalized, payload)
        return payload

    def get_instrument_financials(self, symbol: str, period: str) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        if period not in {"annual", "quarterly"}:
            raise BadRequestError("period must be annual or quarterly")
        financials_period = cast(FinancialsPeriod, period)
        warnings: list[dict[str, str]] = []
        cached = self._financials_repository.get(normalized, financials_period)
        if cached is not None and self._is_financials_fresh(cached.fetched_at):
            return self._financials_document_to_payload(cached, warnings=warnings)

        income_statement_rows: list[dict[str, Any]] = []
        cash_flow_rows: list[dict[str, Any]] = []
        income_coverage = "empty"
        cash_flow_coverage = "empty"

        try:
            income_statement_rows = self._map_income_statement_rows(
                normalized,
                self._yfinance_client.income_statement(normalized, financials_period),
            )
            income_coverage = "integrated" if income_statement_rows else "empty"
        except UpstreamServiceError:
            income_coverage = "provider_error_fallback"
            warnings.append({"code": "income_statement_provider_error", "message": "Income statement provider unavailable."})

        try:
            cash_flow_rows = self._map_cash_flow_rows(
                normalized,
                self._yfinance_client.cash_flow_statement(normalized, financials_period),
            )
            cash_flow_coverage = "integrated" if cash_flow_rows else "empty"
        except UpstreamServiceError:
            cash_flow_coverage = "provider_error_fallback"
            warnings.append({"code": "cash_flow_provider_error", "message": "Cash flow provider unavailable."})

        yfinance_rows: list[BalanceSheetStatement] = []
        yfinance_error: UpstreamServiceError | None = None
        balance_sheet_coverage = "empty"
        try:
            yfinance_payload = self._yfinance_client.balance_sheet_statement(symbol=normalized, period=financials_period)
            yfinance_rows = self._map_balance_sheet_rows(normalized, yfinance_payload)
            balance_sheet_coverage = "integrated" if yfinance_rows else "empty"
        except UpstreamServiceError as exc:
            yfinance_error = exc
            balance_sheet_coverage = "provider_error_fallback"
            LOGGER.warning("yfinance balance sheet failed for %s; using FMP fallback", normalized, exc_info=True)
            warnings.append({"code": "yfinance_balance_sheet_failed", "message": "yfinance failed; trying FMP fallback."})

        if yfinance_rows:
            currency = yfinance_rows[0].reported_currency if yfinance_rows else None
            document = FinancialsCacheDocument(
                symbol=normalized,
                period=financials_period,
                source="yfinance_financials_v2",
                currency=currency or self._detect_statement_currency(income_statement_rows, cash_flow_rows),
                statements=FinancialStatements(
                    income_statement=income_statement_rows,
                    balance_sheet=yfinance_rows,
                    cash_flow=cash_flow_rows,
                ),
                fetched_at=utcnow(),
            )
            self._financials_repository.upsert_document(document)
            return self._financials_document_to_payload(
                document,
                warnings=warnings,
                coverage={
                    "income_statement": income_coverage,
                    "balance_sheet": balance_sheet_coverage,
                    "cash_flow": cash_flow_coverage,
                },
            )

        if yfinance_error is None:
            LOGGER.info("yfinance balance sheet empty for %s; using FMP fallback", normalized)
            warnings.append({"code": "yfinance_balance_sheet_empty", "message": "yfinance returned no usable balance sheet; trying FMP fallback."})

        try:
            rows = self._fmp_client.balance_sheet_statement(symbol=normalized, period=financials_period)
            balance_sheet_rows = self._map_balance_sheet_rows(normalized, rows)
            currency = balance_sheet_rows[0].reported_currency if balance_sheet_rows else None
            if not balance_sheet_rows:
                warnings.append({"code": "balance_sheet_empty", "message": "No balance sheet statements available from provider."})
            document = FinancialsCacheDocument(
                symbol=normalized,
                period=financials_period,
                source="fmp_balance_sheet_v2",
                currency=currency or self._detect_statement_currency(income_statement_rows, cash_flow_rows),
                statements=FinancialStatements(
                    income_statement=income_statement_rows,
                    balance_sheet=balance_sheet_rows,
                    cash_flow=cash_flow_rows,
                ),
                fetched_at=utcnow(),
            )
            self._financials_repository.upsert_document(document)
            return self._financials_document_to_payload(
                document,
                warnings=warnings,
                coverage={
                    "income_statement": income_coverage,
                    "balance_sheet": "integrated" if balance_sheet_rows else "empty",
                    "cash_flow": cash_flow_coverage,
                },
            )
        except UpstreamServiceError:
            if cached is not None:
                warnings.append({"code": "provider_error_fallback", "message": "Using stale cached financials due to provider error."})
                return self._financials_document_to_payload(
                    cached,
                    warnings=warnings,
                    coverage={
                        "income_statement": "provider_error_fallback" if income_coverage == "provider_error_fallback" else ("integrated" if cached.statements.income_statement else "empty"),
                        "balance_sheet": "provider_error_fallback",
                        "cash_flow": "provider_error_fallback" if cash_flow_coverage == "provider_error_fallback" else ("integrated" if cached.statements.cash_flow else "empty"),
                    },
                )
            raise

    def get_instrument_risk(self, symbol: str, benchmark: str | None) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        benchmark_symbol = (benchmark or "SPY").strip().upper()
        series = self.get_instrument_timeseries(normalized, "returns", benchmark_symbol)
        instrument_points = series.get("instrument", {}).get("points", [])
        benchmark_points = series.get("benchmark", {}).get("points", [])
        instrument_returns = [point["value"] for point in instrument_points]
        benchmark_returns = [point["value"] for point in benchmark_points]
        aligned = min(len(instrument_returns), len(benchmark_returns))
        aligned_instrument_returns = instrument_returns[-aligned:] if aligned else []
        aligned_benchmark_returns = benchmark_returns[-aligned:] if aligned else []

        covariance: float | None = None
        correlation: float | None = None
        beta_proxy: float | None = None
        if aligned >= 2:
            benchmark_mean = sum(aligned_benchmark_returns) / aligned
            instrument_mean = sum(aligned_instrument_returns) / aligned
            covariance = sum(
                (aligned_instrument_returns[idx] - instrument_mean)
                * (aligned_benchmark_returns[idx] - benchmark_mean)
                for idx in range(aligned)
            ) / aligned
            instrument_variance = sum((value - instrument_mean) ** 2 for value in aligned_instrument_returns) / aligned
            benchmark_variance = sum((value - benchmark_mean) ** 2 for value in aligned_benchmark_returns) / aligned
            if benchmark_variance != 0:
                beta_proxy = covariance / benchmark_variance
            if instrument_variance > 0 and benchmark_variance > 0:
                correlation = covariance / ((instrument_variance ** 0.5) * (benchmark_variance ** 0.5))

        tracking_error: float | None = None
        if aligned >= 2:
            active_returns = [
                aligned_instrument_returns[idx] - aligned_benchmark_returns[idx]
                for idx in range(aligned)
            ]
            tracking_error = self._volatility_proxy(active_returns)

        drawdown_series = self.get_instrument_timeseries(normalized, "drawdown", benchmark_symbol)
        drawdown_points = drawdown_series.get("instrument", {}).get("points", [])
        max_drawdown = min((point["value"] for point in drawdown_points), default=None)

        payload = {
            "symbol": normalized,
            "benchmark": benchmark_symbol,
            "aligned_points": aligned,
            "series": "returns",
            "volatility_proxy": self._volatility_proxy(aligned_instrument_returns),
            "benchmark_volatility_proxy": self._volatility_proxy(aligned_benchmark_returns),
            "correlation": correlation,
            "beta": beta_proxy,
            "beta_proxy": beta_proxy,
            "tracking_error": tracking_error,
            "max_drawdown": max_drawdown,
            "meta": series.get("meta", {}),
        }
        return payload

    def get_instrument_benchmark(self, symbol: str, benchmark: str | None) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        benchmark_symbol = (benchmark or "SPY").strip().upper()
        return {
            "symbol": normalized,
            "benchmark": benchmark_symbol,
            "comparison": self.get_instrument_timeseries(normalized, "close", benchmark_symbol),
        }

    def get_instrument_timeseries(self, symbol: str, series: str | None, benchmark: str | None) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        benchmark_symbol = (benchmark or "SPY").strip().upper()
        raw_series = (series or "price").strip().lower()
        series_aliases = {
            "close": "price",
            "normalized_close": "normalized_price",
        }
        selected_series = series_aliases.get(raw_series, raw_series)
        supported_series = {
            "price",
            "benchmark_price",
            "returns",
            "drawdown",
            "benchmark_relative",
            "normalized_price",
        }
        if selected_series not in supported_series:
            raise BadRequestError(
                "series must be one of: price, benchmark_price, returns, drawdown, benchmark_relative"
            )

        instrument_history = self.get_instrument_history(normalized, "1y")

        warnings: list[dict[str, Any]] = []
        benchmark_history: InstrumentHistoryResponse | None = None
        try:
            benchmark_history = self.get_instrument_history(benchmark_symbol, "1y")
        except Exception as exc:
            warnings.append({"symbol": benchmark_symbol, "code": "benchmark_unavailable", "message": str(exc)})

        instrument_prices = self._series_points(instrument_history.points, "price")
        benchmark_prices = [] if benchmark_history is None else self._series_points(benchmark_history.points, "price")
        aligned_price_series = self._align_series_by_date(instrument_prices, benchmark_prices)
        aligned_instrument_prices = aligned_price_series["left"]
        aligned_benchmark_prices = aligned_price_series["right"]

        instrument_points: list[dict[str, float | str]] = []
        benchmark_points: list[dict[str, float | str]] = []

        if selected_series == "price":
            instrument_points = instrument_prices
            benchmark_points = benchmark_prices
        elif selected_series == "benchmark_price":
            benchmark_points = benchmark_prices
            instrument_points = []
            if not benchmark_points:
                warnings.append(
                    {
                        "symbol": benchmark_symbol,
                        "code": "benchmark_price_unavailable",
                        "message": "Benchmark price series is unavailable.",
                    }
                )
        elif selected_series == "returns":
            instrument_points = self._series_points(instrument_history.points, "returns")
            benchmark_points = [] if benchmark_history is None else self._series_points(benchmark_history.points, "returns")
        elif selected_series == "drawdown":
            instrument_points = self._series_points(instrument_history.points, "drawdown")
            benchmark_points = [] if benchmark_history is None else self._series_points(benchmark_history.points, "drawdown")
        elif selected_series == "normalized_price":
            instrument_points = self._series_points(instrument_history.points, "normalized_price")
            benchmark_points = [] if benchmark_history is None else self._series_points(benchmark_history.points, "normalized_price")
        elif selected_series == "benchmark_relative":
            if not aligned_instrument_prices or not aligned_benchmark_prices:
                warnings.append(
                    {
                        "symbol": normalized,
                        "code": "benchmark_relative_unavailable",
                        "message": "Benchmark relative series requires aligned instrument and benchmark price data.",
                    }
                )
            else:
                instrument_points, benchmark_points = self._benchmark_relative_points(
                    aligned_instrument_prices,
                    aligned_benchmark_prices,
                )

        return {
            "symbol": normalized,
            "series": raw_series,
            "benchmark_symbol": benchmark_symbol,
            "instrument": {
                "points": instrument_points,
            },
            "benchmark_data": {"available": benchmark_history is not None},
            "benchmark": {
                "symbol": benchmark_symbol,
                "points": benchmark_points,
            },
            "meta": {"warnings": warnings},
        }

    def get_instrument_comparison_timeseries(self, symbol: str, symbols_csv: str) -> dict[str, Any]:
        base_symbol = self._normalize_symbol(symbol)
        comparison_symbols = self._parse_symbols_csv(symbols_csv)
        output = {"base_symbol": base_symbol, "series": []}
        warnings: list[dict[str, Any]] = []

        for comparison_symbol in comparison_symbols:
            try:
                history = self.get_instrument_history(comparison_symbol, "1y")
                output["series"].append(
                    {
                        "symbol": comparison_symbol,
                        "points": [{"date": point.date, "value": point.close} for point in history.points],
                    }
                )
            except Exception as exc:
                warnings.append({"symbol": comparison_symbol, "code": "comparison_symbol_unavailable", "message": str(exc)})

        output["meta"] = {"warnings": warnings}
        return output

    def get_benchmark_catalog(self) -> dict[str, Any]:
        if self._cache_enabled:
            cached_catalog = self._benchmark_catalog_cache.get("catalog")
            if cached_catalog is not None:
                return cached_catalog
        catalog = {
            "items": [
                {"symbol": "SPY", "name": "SPDR S&P 500 ETF"},
                {"symbol": "QQQ", "name": "Invesco QQQ Trust"},
                {"symbol": "VT", "name": "Vanguard Total World Stock ETF"},
                {"symbol": "IWM", "name": "iShares Russell 2000 ETF"},
            ],
            "source": "marketdata_service_catalog",
        }
        if self._cache_enabled:
            self._benchmark_catalog_cache.set("catalog", catalog)
        return catalog

    def search_benchmark_catalog(self, query: str) -> dict[str, Any]:
        cleaned_query = query.strip().lower()
        if not cleaned_query:
            raise BadRequestError("q must not be empty")
        catalog = self.get_benchmark_catalog()
        matched = [
            item
            for item in catalog["items"]
            if cleaned_query in item["symbol"].lower() or cleaned_query in item["name"].lower()
        ]
        return {"query": query, "items": matched, "total": len(matched)}

    def get_instrument_full(self, symbol: str) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        return {
            "symbol": normalized,
            "snapshot": self.get_instrument_snapshot(normalized),
            "fundamentals": self.get_instrument_fundamentals(normalized),
            "metrics": self.get_instrument_metrics(normalized),
            "financials": self.get_instrument_financials(normalized, "annual"),
            "risk": self.get_instrument_risk(normalized, "SPY"),
        }

    def refresh_instrument_price(self, symbol: str) -> InstrumentPriceRefreshResponse:
        normalized = symbol.strip().upper()
        if not normalized:
            raise BadRequestError("symbol must not be empty")

        trade_date = date.today().isoformat()

        cached = self._current_price_repository.get(normalized, trade_date)
        if cached is not None:
            current_price = cached.current_price
            price_source = "cache_today"
            price_cache_hit = True
            fetched_at = cached.fetched_at
        else:
            current_price = self._yfinance_client.fetch_current_price(normalized)
            stored = self._current_price_repository.upsert(normalized, trade_date, current_price, source="yfinance_1d_1m")
            price_source = "yfinance_1d_1m"
            price_cache_hit = False
            fetched_at = stored.fetched_at

        history_cache_present = self._price_history_repository.get(normalized) is not None
        history_action = "enrich_in_background" if history_cache_present else "seed_max_in_background"

        return InstrumentPriceRefreshResponse(
            symbol=normalized,
            trade_date=trade_date,
            current_price=current_price,
            price_source=price_source,
            price_cache_hit=price_cache_hit,
            history_cache_present=history_cache_present,
            history_action=history_action,
            fetched_at=fetched_at,
        )

    def seed_history_max(self, symbol: str) -> None:
        normalized = symbol.strip().upper()
        data = self._yfinance_client.fetch_history(normalized, period="max", interval="1d")
        rows = self._to_history_rows(data)
        if not rows:
            raise UpstreamServiceError("Market data provider returned no daily history for seed")

        document = PriceHistoryCacheDocument(
            symbol=normalized,
            interval="1d",
            period_seeded="max",
            history_rows=rows,
            first_date=rows[0].date,
            last_date=rows[-1].date,
            updated_at=utcnow(),
        )
        self._price_history_repository.upsert_document(document)

    def enrich_history_recent(self, symbol: str) -> None:
        normalized = symbol.strip().upper()
        data = self._yfinance_client.fetch_history(normalized, period="5d", interval="1d")
        rows = self._to_history_rows(data)
        if not rows:
            return
        self._price_history_repository.enrich_history_rows(normalized, rows)

    def get_instrument_history(self, symbol: str, range_value: str = "3m") -> InstrumentHistoryResponse:
        normalized = self._normalize_symbol(symbol)
        payload = self._get_history_with_swr(normalized, range_value)
        return InstrumentHistoryResponse(
            symbol=normalized,
            range=range_value,
            points=payload["points"],
            cache_present=payload["cache_present"],
            updated_at=payload["updated_at"],
        )

    def _get_profile_with_swr(self, symbol: str) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        cached = self._profile_repository.get(normalized)
        if cached is not None and self._is_fresh(cached.fetched_at):
            return {"name": cached.visible_profile.company_name, "sector": cached.visible_profile.sector, "country": cached.visible_profile.country, "currency": cached.visible_profile.currency, "provider": cached.source, "cache_status": "fresh_cache"}
        if cached is not None:
            self._trigger_background_refresh("profile", normalized, self._refresh_profile_now)
            return {"name": cached.visible_profile.company_name, "sector": cached.visible_profile.sector, "country": cached.visible_profile.country, "currency": cached.visible_profile.currency, "provider": cached.source, "cache_status": "stale_cache"}
        refreshed = self._refresh_profile_now(normalized)
        if refreshed is None:
            return {"name": None, "sector": None, "country": None, "currency": None, "provider": None, "cache_status": "cache_miss_pending"}
        return refreshed | {"cache_status": "cache_miss_seeded"}

    def _get_price_with_swr(self, symbol: str) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        trade_date = date.today().isoformat()
        cached_today = self._current_price_repository.get(normalized, trade_date)
        if cached_today is not None:
            return {"current_price": cached_today.current_price, "as_of": cached_today.trade_date, "provider": "yfinance", "price_source": "cache_today", "fetched_at": cached_today.fetched_at, "cache_status": "fresh_cache"}

        latest = self._current_price_repository.get_latest(normalized)
        if latest is not None:
            if utcnow() - latest.fetched_at > self.PRICE_CACHE_STALE_AFTER:
                self._trigger_background_refresh("price", normalized, self._refresh_price_now)
                return {"current_price": latest.current_price, "as_of": latest.trade_date, "provider": "yfinance", "price_source": latest.source, "fetched_at": latest.fetched_at, "cache_status": "stale_cache"}

        refreshed = self._refresh_price_now(normalized)
        if refreshed is None and latest is not None:
            return {"current_price": latest.current_price, "as_of": latest.trade_date, "provider": "yfinance", "price_source": latest.source, "fetched_at": latest.fetched_at, "cache_status": "provider_error_fallback"}
        if refreshed is None:
            return {"current_price": None, "as_of": trade_date, "provider": "yfinance", "price_source": "yfinance_1d_1m", "fetched_at": None, "cache_status": "cache_miss_pending"}
        return refreshed | {"cache_status": "cache_miss_seeded"}

    def _get_history_with_swr(self, symbol: str, range_value: str) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        if range_value not in self.VALID_HISTORY_RANGES:
            raise BadRequestError("range must be one of: 1m, 3m, 6m, ytd, 1y, max")
        cache_document = self._price_history_repository.get(normalized)
        if cache_document is None:
            seeded = self._refresh_history_seed_now(normalized)
            if not seeded:
                return {"points": [], "cache_present": False, "updated_at": None, "cache_status": "cache_miss_pending"}
            cache_document = self._price_history_repository.get(normalized)
            cache_status: CacheStatus = "cache_miss_seeded"
        else:
            cache_status = "fresh_cache"
            if utcnow() - cache_document.updated_at > self.HISTORY_STALE_AFTER:
                cache_status = "stale_cache"
                self._trigger_background_refresh("history", normalized, self._refresh_history_enrich_now)
        if cache_document is None or not cache_document.history_rows:
            raise NotFoundError(f"No price history available for instrument '{normalized}'")
        cutoff = self._history_cutoff(date.today(), range_value)  # type: ignore[arg-type]
        filtered_rows = cache_document.history_rows if cutoff is None else [row for row in cache_document.history_rows if row.date >= cutoff]
        filtered_rows.sort(key=lambda row: row.date)
        return {"points": [InstrumentHistoryPoint(date=row.date, close=row.close) for row in filtered_rows], "cache_present": True, "updated_at": cache_document.updated_at, "cache_status": cache_status}

    def _extract_market_cap(self, symbol: str) -> float | None:
        cached = self._profile_repository.get(symbol)
        if cached is None:
            return None
        return cached.persistence_only_profile.market_cap

    def _extract_beta(self, symbol: str) -> float | None:
        cached = self._profile_repository.get(symbol)
        if cached is None:
            return None
        return cached.persistence_only_profile.beta

    @staticmethod
    def _series_points(points: list[InstrumentHistoryPoint], selected_series: str) -> list[dict[str, float | str]]:
        if selected_series == "price":
            return [{"date": point.date, "value": point.close} for point in points]

        if selected_series == "normalized_price":
            if not points:
                return []
            base = points[0].close
            if base == 0:
                return [{"date": point.date, "value": 0.0} for point in points]
            return [{"date": point.date, "value": (point.close / base) * 100.0} for point in points]

        if selected_series == "drawdown":
            drawdown_points: list[dict[str, float | str]] = []
            running_peak: float | None = None
            for point in points:
                running_peak = point.close if running_peak is None else max(running_peak, point.close)
                if running_peak == 0:
                    drawdown_points.append({"date": point.date, "value": 0.0})
                else:
                    drawdown_points.append({"date": point.date, "value": (point.close / running_peak) - 1.0})
            return drawdown_points

        returns_points: list[dict[str, float | str]] = []
        for idx in range(1, len(points)):
            previous = points[idx - 1].close
            current = points[idx].close
            if previous == 0:
                continue
            returns_points.append({"date": points[idx].date, "value": (current - previous) / previous})
        return returns_points

    @staticmethod
    def _align_series_by_date(
        left_points: list[dict[str, float | str]],
        right_points: list[dict[str, float | str]],
    ) -> dict[str, list[dict[str, float | str]]]:
        right_by_date = {point["date"]: point["value"] for point in right_points}
        aligned_left: list[dict[str, float | str]] = []
        aligned_right: list[dict[str, float | str]] = []
        for left in left_points:
            date_key = left["date"]
            if date_key not in right_by_date:
                continue
            aligned_left.append({"date": date_key, "value": left["value"]})
            aligned_right.append({"date": date_key, "value": right_by_date[date_key]})
        return {"left": aligned_left, "right": aligned_right}

    @staticmethod
    def _benchmark_relative_points(
        aligned_instrument_prices: list[dict[str, float | str]],
        aligned_benchmark_prices: list[dict[str, float | str]],
    ) -> tuple[list[dict[str, float | str]], list[dict[str, float | str]]]:
        if not aligned_instrument_prices or not aligned_benchmark_prices:
            return [], []
        instrument_base = float(aligned_instrument_prices[0]["value"])
        benchmark_base = float(aligned_benchmark_prices[0]["value"])
        if instrument_base == 0 or benchmark_base == 0:
            return [], []

        instrument_points: list[dict[str, float | str]] = []
        benchmark_points: list[dict[str, float | str]] = []
        for idx in range(len(aligned_instrument_prices)):
            date_key = aligned_instrument_prices[idx]["date"]
            instrument_norm = float(aligned_instrument_prices[idx]["value"]) / instrument_base
            benchmark_norm = float(aligned_benchmark_prices[idx]["value"]) / benchmark_base
            benchmark_relative = (instrument_norm / benchmark_norm) - 1.0 if benchmark_norm != 0 else 0.0
            instrument_points.append({"date": date_key, "value": benchmark_relative})
            benchmark_points.append({"date": date_key, "value": 0.0})
        return instrument_points, benchmark_points

    @staticmethod
    def _volatility_proxy(values: list[float]) -> float | None:
        if len(values) < 2:
            return None
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        return variance ** 0.5

    @staticmethod
    def _parse_symbols_csv(symbols_csv: str) -> list[str]:
        symbols = [part.strip().upper() for part in symbols_csv.split(",") if part.strip()]
        if not symbols:
            raise BadRequestError("symbols must contain at least one symbol")
        return list(dict.fromkeys(symbols))

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not normalized:
            raise BadRequestError("symbol must not be empty")
        return normalized

    def _build_visible_profile(self, parsed: FMPInstrumentProfile) -> InstrumentProfile:
        visible_profile = InstrumentProfile.model_validate(parsed.model_dump())
        visible_profile.address_line = self._build_address_line(
            visible_profile.address,
            visible_profile.zip,
            visible_profile.city,
        )
        return visible_profile

    @staticmethod
    def _build_persistence_profile(parsed: FMPInstrumentProfile) -> PersistenceOnlyInstrumentProfile:
        return PersistenceOnlyInstrumentProfile.model_validate(parsed.model_dump())

    @staticmethod
    def _build_address_line(address: str | None, zip_code: str | None, city: str | None) -> str | None:
        prefix_parts = [part.strip() for part in [address] if isinstance(part, str) and part.strip()]
        location_parts = [part.strip() for part in [zip_code, city] if isinstance(part, str) and part.strip()]

        if location_parts:
            prefix_parts.append(" ".join(location_parts))

        if not prefix_parts:
            return None
        return ", ".join(prefix_parts)

    def _lock_for(self, datatype: str, symbol: str) -> threading.Lock:
        key = (datatype, symbol)
        with self._inflight_guard:
            if key not in self._inflight_locks:
                self._inflight_locks[key] = threading.Lock()
            return self._inflight_locks[key]

    def _trigger_background_refresh(self, datatype: str, symbol: str, func) -> None:
        lock = self._lock_for(datatype, symbol)
        if not lock.acquire(blocking=False):
            return

        def _run() -> None:
            try:
                func(symbol)
            except Exception:
                LOGGER.warning("background refresh failed for %s/%s", datatype, symbol, exc_info=True)
            finally:
                lock.release()

        threading.Thread(target=_run, daemon=True).start()

    def _refresh_profile_now(self, symbol: str) -> dict[str, Any] | None:
        lock = self._lock_for("profile", symbol)
        with lock:
            rows = self._fmp_client.profile(symbol=symbol)
            if not rows:
                return None
            parsed = FMPInstrumentProfile.model_validate(rows[0] | {"symbol": symbol})
            visible_profile = self._build_visible_profile(parsed)
            persistence_only_profile = self._build_persistence_profile(parsed)
            self._profile_repository.upsert(
                symbol,
                visible_profile=visible_profile.model_dump(),
                persistence_only_profile=persistence_only_profile.model_dump(),
            )
            return {"name": visible_profile.company_name, "sector": visible_profile.sector, "country": visible_profile.country, "currency": visible_profile.currency, "provider": "fmp_profile_v2"}

    def _refresh_price_now(self, symbol: str) -> dict[str, Any] | None:
        if self._is_negative_cached("price", symbol):
            return None
        lock = self._lock_for("price", symbol)
        with lock:
            if self._is_negative_cached("price", symbol):
                return None
            try:
                current_price = self._yfinance_client.fetch_current_price(symbol)
                trade_date = date.today().isoformat()
                stored = self._current_price_repository.upsert(symbol, trade_date, current_price, source="yfinance_1d_1m")
                return {"current_price": current_price, "as_of": trade_date, "provider": "yfinance", "price_source": "yfinance_1d_1m", "fetched_at": stored.fetched_at}
            except Exception:
                self._set_negative_cache("price", symbol)
                LOGGER.warning("price refresh failed for %s", symbol, exc_info=True)
                return None

    def _refresh_history_seed_now(self, symbol: str) -> bool:
        if self._is_negative_cached("history_seed", symbol):
            return False
        lock = self._lock_for("history", symbol)
        with lock:
            if self._is_negative_cached("history_seed", symbol):
                return False
            try:
                if self._price_history_repository.get(symbol) is None:
                    self.seed_history_max(symbol)
                return self._price_history_repository.get(symbol) is not None
            except Exception:
                self._set_negative_cache("history_seed", symbol)
                LOGGER.warning("history seed failed for %s", symbol, exc_info=True)
                return False

    def _set_negative_cache(self, datatype: str, symbol: str) -> None:
        self._negative_refresh_cache.set((datatype, symbol), True)

    def _is_negative_cached(self, datatype: str, symbol: str) -> bool:
        return bool(self._negative_refresh_cache.get((datatype, symbol)))

    def _refresh_history_enrich_now(self, symbol: str) -> None:
        lock = self._lock_for("history", symbol)
        with lock:
            self.enrich_history_recent(symbol)

    @staticmethod
    def _combine_cache_status(left: CacheStatus, right: CacheStatus) -> CacheStatus:
        severity = {
            "provider_error_fallback": 5,
            "cache_miss_pending": 4,
            "cache_miss_seeded": 3,
            "stale_cache": 2,
            "fresh_cache": 1,
        }
        return left if severity[left] >= severity[right] else right

    def _is_fresh(self, fetched_at) -> bool:
        return utcnow() - fetched_at <= timedelta(seconds=self._profile_cache_ttl_seconds)

    def _is_financials_fresh(self, fetched_at) -> bool:
        return utcnow() - fetched_at <= timedelta(seconds=self._financials_cache_ttl_seconds)

    def _financials_document_to_payload(
        self,
        document: FinancialsCacheDocument,
        *,
        warnings: list[dict[str, str]] | None = None,
        coverage: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        income_statement = sorted(document.statements.income_statement, key=lambda row: row.get("date") or "", reverse=True)
        cash_flow = sorted(document.statements.cash_flow, key=lambda row: row.get("date") or "", reverse=True)
        normalized_balance_sheet = [
            self._normalize_balance_sheet_item(item.model_dump(by_alias=True))
            for item in sorted(document.statements.balance_sheet, key=lambda row: row.date or "", reverse=True)
        ]
        effective_coverage = coverage or {
            "income_statement": "integrated" if income_statement else "empty",
            "balance_sheet": "integrated" if normalized_balance_sheet else "empty",
            "cash_flow": "integrated" if cash_flow else "empty",
        }
        computed_warnings = list(warnings or [])
        if effective_coverage["income_statement"] == "empty":
            computed_warnings.append({"code": "income_statement_empty", "message": "Income statement data is empty."})
        if effective_coverage["cash_flow"] == "empty":
            computed_warnings.append({"code": "cash_flow_empty", "message": "Cash flow data is empty."})
        if effective_coverage["balance_sheet"] == "empty":
            computed_warnings.append({"code": "balance_sheet_empty", "message": "Balance sheet data is empty."})
        deduped_warnings: list[dict[str, str]] = []
        seen_warning_keys: set[tuple[str, str]] = set()
        for item in computed_warnings:
            key = (item.get("code", ""), item.get("message", ""))
            if key in seen_warning_keys:
                continue
            seen_warning_keys.add(key)
            deduped_warnings.append(item)
        derived = self._derive_financials(
            symbol=document.symbol,
            balance_sheet=normalized_balance_sheet,
            income_statement=income_statement,
            cash_flow=cash_flow,
        )
        return {
            "symbol": document.symbol,
            "period": document.period,
            "currency": document.currency,
            "statements": {
                "income_statement": income_statement,
                "balance_sheet": normalized_balance_sheet,
                "cash_flow": cash_flow,
            },
            "derived": derived,
            "meta": {
                "warnings": deduped_warnings,
                "source": document.source,
                "fetched_at": document.fetched_at.isoformat(),
                "coverage": effective_coverage,
            },
        }

    def _derive_financials(
        self,
        *,
        symbol: str,
        balance_sheet: list[dict[str, Any]],
        income_statement: list[dict[str, Any]],
        cash_flow: list[dict[str, Any]],
    ) -> dict[str, Any]:
        latest_balance = balance_sheet[0] if balance_sheet else {}
        latest_income = income_statement[0] if income_statement else {}
        latest_cash_flow = cash_flow[0] if cash_flow else {}
        latest_date = latest_balance.get("date") or latest_income.get("date") or latest_cash_flow.get("date")

        total_debt = self._coerce_float(latest_balance.get("totalDebt"))
        if total_debt is None:
            short_term = self._coerce_float(latest_balance.get("shortTermDebt"))
            long_term = self._coerce_float(latest_balance.get("longTermDebt"))
            if short_term is not None and long_term is not None:
                total_debt = short_term + long_term

        cash_and_equivalents = self._coerce_float(latest_balance.get("cashAndCashEquivalents"))
        net_debt = (total_debt - cash_and_equivalents) if total_debt is not None and cash_and_equivalents is not None else None

        operating_cash_flow = self._coerce_float(latest_cash_flow.get("operatingCashFlow"))
        capital_expenditure = self._coerce_float(latest_cash_flow.get("capitalExpenditure"))
        free_cash_flow = (
            operating_cash_flow - capital_expenditure
            if operating_cash_flow is not None and capital_expenditure is not None
            else None
        )

        net_income = self._coerce_float(latest_income.get("netIncome"))
        total_equity = self._coerce_float(latest_balance.get("totalEquity"))
        total_assets = self._coerce_float(latest_balance.get("totalAssets"))
        roe = (net_income / total_equity) if net_income is not None and total_equity not in (None, 0.0) else None
        roa = (net_income / total_assets) if net_income is not None and total_assets not in (None, 0.0) else None
        debt_to_equity = (total_debt / total_equity) if total_debt is not None and total_equity not in (None, 0.0) else None

        return {
            "market_cap": self._extract_market_cap(symbol),
            "beta": self._extract_beta(symbol),
            "latest_period_date": latest_date,
            "total_debt": total_debt,
            "net_debt": net_debt,
            "free_cash_flow": free_cash_flow,
            "roe": roe,
            "roa": roa,
            "debt_to_equity": debt_to_equity,
        }

    @staticmethod
    def _coerce_float(value: Any) -> float | None:
        if isinstance(value, int | float):
            return float(value)
        return None

    @staticmethod
    def _detect_statement_currency(income_statement: list[dict[str, Any]], cash_flow: list[dict[str, Any]]) -> str | None:
        for row in income_statement + cash_flow:
            currency = row.get("reportedCurrency") or row.get("currency")
            if isinstance(currency, str) and currency.strip():
                return currency.strip()
        return None

    @staticmethod
    def _map_income_statement_rows(symbol: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        mapped: list[dict[str, Any]] = []
        for row in rows:
            mapped.append(
                {
                    "symbol": symbol,
                    "date": row.get("date"),
                    "calendarYear": row.get("calendarYear") or row.get("calendar_year"),
                    "period": row.get("period"),
                    "revenue": row.get("revenue"),
                    "operatingIncome": row.get("operatingIncome"),
                    "netIncome": row.get("netIncome"),
                }
            )
        return mapped

    @staticmethod
    def _map_cash_flow_rows(symbol: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        mapped: list[dict[str, Any]] = []
        for row in rows:
            operating_cash_flow = row.get("operatingCashFlow")
            capital_expenditure = row.get("capitalExpenditure")
            free_cash_flow = row.get("freeCashFlow")
            if free_cash_flow is None and isinstance(operating_cash_flow, int | float) and isinstance(capital_expenditure, int | float):
                free_cash_flow = float(operating_cash_flow) - float(capital_expenditure)
            mapped.append(
                {
                    "symbol": symbol,
                    "date": row.get("date"),
                    "calendarYear": row.get("calendarYear") or row.get("calendar_year"),
                    "period": row.get("period"),
                    "operatingCashFlow": operating_cash_flow,
                    "capitalExpenditure": capital_expenditure,
                    "freeCashFlow": free_cash_flow,
                }
            )
        return mapped

    @staticmethod
    def _normalize_balance_sheet_item(row: dict[str, Any]) -> dict[str, Any]:
        result = dict(row)
        result["fiscalYear"] = row.get("calendarYear") or row.get("calendar_year")
        result["reportedCurrency"] = row.get("reportedCurrency") or row.get("reported_currency")
        result["totalEquity"] = row.get("totalStockholdersEquity")
        short_term_debt = row.get("shortTermDebt")
        long_term_debt = row.get("longTermDebt")
        if isinstance(short_term_debt, (int, float)) or isinstance(long_term_debt, (int, float)):
            result["totalDebt"] = (float(short_term_debt or 0.0) + float(long_term_debt or 0.0))
        else:
            result["totalDebt"] = None
        cash_and_equivalents = row.get("cashAndCashEquivalents")
        if isinstance(result["totalDebt"], (int, float)) and isinstance(cash_and_equivalents, (int, float)):
            result["netDebt"] = float(result["totalDebt"]) - float(cash_and_equivalents)
        else:
            result["netDebt"] = None
        return result

    @staticmethod
    def _map_balance_sheet_rows(symbol: str, rows: list[dict[str, Any]]) -> list[BalanceSheetStatement]:
        mapped_rows: list[BalanceSheetStatement] = []
        for row in rows:
            try:
                mapped_rows.append(BalanceSheetStatement.model_validate(row | {"symbol": symbol}))
            except Exception:
                continue
        return mapped_rows

    @staticmethod
    def _to_history_rows(data) -> list[PriceHistoryRow]:
        if getattr(data, "empty", True):
            return []

        rows: list[PriceHistoryRow] = []
        for index, row in data.iterrows():
            close = row.get("Close")
            open_price = row.get("Open")
            high = row.get("High")
            low = row.get("Low")
            volume = row.get("Volume")
            if any(value is None for value in [close, open_price, high, low, volume]):
                continue
            try:
                rows.append(
                    PriceHistoryRow(
                        date=index.date().isoformat(),
                        open=float(open_price),
                        high=float(high),
                        low=float(low),
                        close=float(close),
                        volume=int(volume),
                    )
                )
            except Exception:
                continue

        rows.sort(key=lambda entry: entry.date)
        return rows

    @staticmethod
    def _history_cutoff(today: date, range_value: HistoryRange) -> str | None:
        if range_value == "max":
            return None
        if range_value == "1m":
            return (today - timedelta(days=30)).isoformat()
        if range_value == "3m":
            return (today - timedelta(days=90)).isoformat()
        if range_value == "6m":
            return (today - timedelta(days=180)).isoformat()
        if range_value == "1y":
            return (today - timedelta(days=365)).isoformat()
        return date(today.year, 1, 1).isoformat()
