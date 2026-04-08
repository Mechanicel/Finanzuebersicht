from __future__ import annotations

from datetime import date, timedelta
import logging
from typing import Any

from app.clients.fmp_client import FMPClient
from app.models import (
    BadRequestError,
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
    InMemoryCurrentPriceCacheRepository,
    InMemoryInstrumentProfileCacheRepository,
    InMemoryPriceHistoryCacheRepository,
    InstrumentProfileCacheRepository,
    PriceHistoryCacheRepository,
)

LOGGER = logging.getLogger(__name__)


class MarketDataService:
    MAX_SEARCH_LIMIT = 20
    VALID_HISTORY_RANGES: tuple[HistoryRange, ...] = ("1m", "3m", "6m", "ytd", "1y", "max")

    def __init__(
        self,
        *,
        fmp_client: FMPClient,
        profile_repository: InstrumentProfileCacheRepository | InMemoryInstrumentProfileCacheRepository,
        current_price_repository: CurrentPriceCacheRepository | InMemoryCurrentPriceCacheRepository,
        price_history_repository: PriceHistoryCacheRepository | InMemoryPriceHistoryCacheRepository,
        cache_enabled: bool,
        profile_cache_ttl_seconds: int,
    ) -> None:
        self._fmp_client = fmp_client
        self._profile_repository = profile_repository
        self._current_price_repository = current_price_repository
        self._price_history_repository = price_history_repository
        self._cache_enabled = cache_enabled
        self._profile_cache_ttl_seconds = profile_cache_ttl_seconds
        self._search_cache: dict[tuple[str, int], InstrumentSearchResponse] = {}
        self._snapshot_cache: dict[str, dict[str, Any]] = {}
        self._metrics_cache: dict[str, dict[str, Any]] = {}
        self._fundamentals_cache: dict[str, dict[str, Any]] = {}
        self._financials_cache: dict[tuple[str, str], dict[str, Any]] = {}
        self._benchmark_catalog_cache: dict[str, Any] | None = None

    def search_instruments(self, query: str, limit: int) -> InstrumentSearchResponse:
        cleaned_query = query.strip()
        if len(cleaned_query) < 1:
            raise BadRequestError("query must contain at least 1 character")
        bounded_limit = max(1, min(limit, self.MAX_SEARCH_LIMIT))

        cache_key = (cleaned_query.lower(), bounded_limit)
        if self._cache_enabled and cache_key in self._search_cache:
            return self._search_cache[cache_key]

        rows = self._fmp_client.search_name(query=cleaned_query, limit=bounded_limit)
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
            self._search_cache[cache_key] = response
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

        for symbol in symbols:
            try:
                snapshot = self.get_instrument_snapshot(symbol)
                items.append(
                    HoldingsSummaryItem(
                        symbol=symbol,
                        name=snapshot.get("name"),
                        sector=snapshot.get("sector"),
                        country=snapshot.get("country"),
                        currency=snapshot.get("currency"),
                        current_price=snapshot.get("current_price"),
                        provider=snapshot.get("provider"),
                        as_of=snapshot.get("as_of"),
                        coverage=snapshot.get("coverage", "basic"),
                    )
                )
            except Exception as exc:
                warnings.append(MetaWarning(symbol=symbol, code="symbol_unavailable", message=str(exc)))
                items.append(HoldingsSummaryItem(symbol=symbol, coverage="none"))

        return HoldingsSummaryResponse(
            items=items,
            requested_symbols=symbols,
            total=len(items),
            meta={"warnings": [warning.model_dump() for warning in warnings]},
        )

    def get_instrument_snapshot(self, symbol: str) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        if self._cache_enabled and normalized in self._snapshot_cache:
            return self._snapshot_cache[normalized]

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
            self._snapshot_cache[normalized] = payload
        return payload

    def get_instrument_fundamentals(self, symbol: str) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        if self._cache_enabled and normalized in self._fundamentals_cache:
            return self._fundamentals_cache[normalized]

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
            self._fundamentals_cache[normalized] = payload
        return payload

    def get_instrument_metrics(self, symbol: str) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        if self._cache_enabled and normalized in self._metrics_cache:
            return self._metrics_cache[normalized]

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
            self._metrics_cache[normalized] = payload
        return payload

    def get_instrument_financials(self, symbol: str, period: str) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        if period not in {"annual", "quarterly"}:
            raise BadRequestError("period must be annual or quarterly")
        cache_key = (normalized, period)
        if self._cache_enabled and cache_key in self._financials_cache:
            return self._financials_cache[cache_key]

        metrics = self.get_instrument_metrics(normalized)
        fundamentals = self.get_instrument_fundamentals(normalized)
        payload = {
            "symbol": normalized,
            "period": period,
            "currency": fundamentals.get("currency"),
            "statements": {
                "income_statement": [],
                "balance_sheet": [],
                "cash_flow": [],
            },
            "derived": {
                "market_cap": metrics.get("market_cap"),
                "beta": metrics.get("beta"),
            },
            "meta": {
                "warnings": [{"code": "financials_provider_not_connected", "message": "No direct financial statement provider configured."}],
            },
        }
        if self._cache_enabled:
            self._financials_cache[cache_key] = payload
        return payload

    def get_instrument_risk(self, symbol: str, benchmark: str | None) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        benchmark_symbol = (benchmark or "SPY").strip().upper()
        series = self.get_instrument_timeseries(normalized, "close", benchmark_symbol)
        instrument_points = series.get("instrument", {}).get("points", [])
        benchmark_points = series.get("benchmark", {}).get("points", [])
        aligned = min(len(instrument_points), len(benchmark_points))
        payload = {
            "symbol": normalized,
            "benchmark": benchmark_symbol,
            "aligned_points": aligned,
            "volatility_proxy": self._volatility_proxy([point["value"] for point in instrument_points]),
            "benchmark_volatility_proxy": self._volatility_proxy([point["value"] for point in benchmark_points]),
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
        selected_series = (series or "close").strip().lower()
        instrument_history = self.get_instrument_history(normalized, "1y")

        warnings: list[dict[str, Any]] = []
        benchmark_history: InstrumentHistoryResponse | None = None
        try:
            benchmark_history = self.get_instrument_history(benchmark_symbol, "1y")
        except Exception as exc:
            warnings.append({"symbol": benchmark_symbol, "code": "benchmark_unavailable", "message": str(exc)})

        return {
            "symbol": normalized,
            "series": selected_series,
            "benchmark_symbol": benchmark_symbol,
            "instrument": {
                "points": [{"date": point.date, "value": point.close} for point in instrument_history.points],
            },
            "benchmark_data": {"available": benchmark_history is not None},
            "benchmark": {
                "symbol": benchmark_symbol,
                "points": [] if benchmark_history is None else [{"date": point.date, "value": point.close} for point in benchmark_history.points],
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
        if self._cache_enabled and self._benchmark_catalog_cache is not None:
            return self._benchmark_catalog_cache
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
            self._benchmark_catalog_cache = catalog
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
            current_price = self._fetch_current_price(normalized)
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
        try:
            yf = self._get_yf_module()
            ticker = yf.Ticker(normalized)
            data = ticker.history(period="max", interval="1d")
        except Exception as exc:
            raise UpstreamServiceError("Market data provider temporarily unavailable") from exc
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
        try:
            yf = self._get_yf_module()
            ticker = yf.Ticker(normalized)
            data = ticker.history(period="5d", interval="1d")
        except Exception as exc:
            raise UpstreamServiceError("Market data provider temporarily unavailable") from exc
        rows = self._to_history_rows(data)
        if not rows:
            return
        self._price_history_repository.enrich_history_rows(normalized, rows)

    def get_instrument_history(self, symbol: str, range_value: str = "3m") -> InstrumentHistoryResponse:
        normalized = symbol.strip().upper()
        if not normalized:
            raise BadRequestError("symbol must not be empty")
        if range_value not in self.VALID_HISTORY_RANGES:
            raise BadRequestError("range must be one of: 1m, 3m, 6m, ytd, 1y, max")

        cache_document = self._price_history_repository.get(normalized)
        cache_present = cache_document is not None
        if cache_document is None:
            self.seed_history_max(normalized)
            cache_document = self._price_history_repository.get(normalized)

        if cache_document is None or not cache_document.history_rows:
            raise NotFoundError(f"No price history available for instrument '{normalized}'")

        cutoff = self._history_cutoff(date.today(), range_value)
        filtered_rows = cache_document.history_rows if cutoff is None else [row for row in cache_document.history_rows if row.date >= cutoff]
        filtered_rows.sort(key=lambda row: row.date)

        points = [InstrumentHistoryPoint(date=row.date, close=row.close) for row in filtered_rows]
        return InstrumentHistoryResponse(
            symbol=normalized,
            range=range_value,
            points=points,
            cache_present=cache_present,
            updated_at=cache_document.updated_at,
        )

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

    def _is_fresh(self, fetched_at) -> bool:
        return utcnow() - fetched_at <= timedelta(seconds=self._profile_cache_ttl_seconds)

    @staticmethod
    def _get_yf_module():
        try:
            import yfinance as yf
        except ImportError as exc:
            raise UpstreamServiceError("yfinance dependency is unavailable") from exc
        return yf

    def _fetch_current_price(self, symbol: str) -> float:
        try:
            yf = self._get_yf_module()
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval="1m")
            if getattr(hist, "empty", True):
                raise UpstreamServiceError("Market data provider returned no intraday data")
            close_series = hist["Close"].dropna()
            if getattr(close_series, "empty", True):
                raise UpstreamServiceError("Market data provider returned no close prices")
            last_price = close_series.iloc[-1]
            return float(last_price)
        except UpstreamServiceError:
            raise
        except Exception as exc:
            raise UpstreamServiceError("Market data provider temporarily unavailable") from exc

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
