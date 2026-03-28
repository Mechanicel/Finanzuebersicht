from __future__ import annotations

import datetime
import logging
import time
from dataclasses import asdict, dataclass
from typing import Any, Optional

from finanzuebersicht_shared import get_settings
from src.models.stock_model import StockModel
from src.repositories.mongo_repository import MongoMarketDataRepository
from src.repositories.providers.yfinance_provider import YFinanceProvider
from src.services.analysis_service import AnalysisMetricsService
from src.services.base_service import BaseService, handle_errors

logger = logging.getLogger(__name__)

FUNDAMENTALS_TTL_SECONDS = 24 * 60 * 60


class StockServiceError(Exception):
    pass


class InvalidRequestError(StockServiceError):
    pass


class InstrumentNotFoundError(StockServiceError):
    pass


class PriceNotFoundError(StockServiceError):
    pass


@dataclass
class AnalysisMetaResponse:
    provider: str
    as_of: str
    coverage: str
    provider_map: dict[str, str]


class StockService(BaseService):
    def __init__(self):
        super().__init__()
        settings = get_settings()
        self.performance_logging = settings.performance_logging
        self.mongo_repo = MongoMarketDataRepository()
        self.provider = YFinanceProvider()
        self.analysis = AnalysisMetricsService(self.provider, benchmark_loader=self._get_benchmark_timeseries_cached)

    def _analysis_service(self) -> AnalysisMetricsService:
        analysis = getattr(self, "analysis", None)
        if analysis is None or getattr(analysis, "provider", None) is not self.provider:
            self.analysis = AnalysisMetricsService(self.provider, benchmark_loader=self._get_benchmark_timeseries_cached)
        return self.analysis

    @handle_errors
    def build(self, isin: str, etf_key: Optional[str] = None) -> Any:
        model = self._get_or_build_model(
            isin,
            include_market=True,
            include_prices=True,
            include_financials=True,
            include_analysts=True,
            include_fund=True,
        )
        if etf_key:
            model.etf[etf_key.lower()] = {"entries": self.provider.fetch_etf_data(model.isin, etf_key)}
            self.mongo_repo.write(model.isin, model.to_dict())
        return model

    @handle_errors
    def get_company(self, isin: str) -> str:
        model = self._get_or_build_model(isin)
        for key in ("long_name", "short_name", "symbol"):
            value = model.instrument.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        raise InstrumentNotFoundError("Kein Firmenname für dieses Instrument verfügbar")

    @handle_errors
    def get_price(self, isin: str, target_date: Optional[datetime.date]) -> float:
        model = self._get_or_build_model(isin, target_date=target_date, include_prices=True)
        return self._price_from_history_for_date(model.price_history, target_date)

    @handle_errors
    def get_analysis_snapshot(self, isin: str) -> dict[str, Any]:
        model = self._get_or_build_model(isin, include_market=True, include_financials=True)
        return {
            "instrument": model.instrument,
            "market": model.market,
            "valuation": model.valuation,
            "meta": asdict(self._meta("snapshot")),
        }

    @handle_errors
    def get_depot_holdings_summary(self, isins: list[str]) -> dict[str, Any]:
        if not isinstance(isins, list):
            raise InvalidRequestError("isins muss eine Liste sein")

        deduplicated_isins: list[str] = []
        seen: set[str] = set()
        skipped: int = 0
        for raw_isin in isins:
            normalized = (raw_isin or "").strip().upper()
            if not normalized:
                skipped += 1
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            deduplicated_isins.append(normalized)

        holdings: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        for isin in deduplicated_isins:
            try:
                model = self._get_or_build_model(isin, include_market=True)
            except Exception as exc:
                logger.warning("Depot summary für ISIN=%s fehlgeschlagen: %s", isin, exc)
                errors.append({"isin": isin, "error": str(exc)})
                continue

            instrument = model.instrument if isinstance(model.instrument, dict) else {}
            market = model.market if isinstance(model.market, dict) else {}
            profile = model.profile if isinstance(model.profile, dict) else {}
            meta = model.meta if isinstance(model.meta, dict) else {}
            provider = (meta.get("provider_map") or {}).get("market") or getattr(self.provider, "provider_name", "yfinance")

            holdings.append(
                {
                    "isin": isin,
                    "name": instrument.get("long_name") or instrument.get("short_name"),
                    "symbol": instrument.get("symbol"),
                    "current_price": market.get("currentPrice"),
                    "currency": market.get("currency") or instrument.get("currency"),
                    "sector": profile.get("sector"),
                    "country": profile.get("country"),
                    "provider": provider,
                    "as_of": meta.get("updated_at"),
                    "coverage": "depot_summary",
                }
            )

        return {
            "holdings": holdings,
            "meta": {
                **asdict(self._meta("depot_summary")),
                "requested": len(isins),
                "processed": len(deduplicated_isins),
                "returned": len(holdings),
                "skipped_empty": skipped,
                "failed": len(errors),
                "errors": errors,
            },
        }

    @handle_errors
    def get_analysis_financials(self, isin: str, period: str = "annual") -> dict[str, Any]:
        model = self._get_or_build_model(isin, include_financials=True)
        period = "quarterly" if period == "quarterly" else "annual"
        response = {
            "financials": {
                "income_statement": {"annual": model.meta.get("financials", {}).get("income_statement", {}).get("annual", []), "quarterly": model.meta.get("financials", {}).get("income_statement", {}).get("quarterly", [])},
                "balance_sheet": {"annual": model.balance_sheet.get("annual", []), "quarterly": model.balance_sheet.get("quarterly", [])},
                "cash_flow": {"annual": model.cash_flow.get("annual", []), "quarterly": model.cash_flow.get("quarterly", [])},
            },
            "period": period,
            "meta": asdict(self._meta("financials")),
        }
        return response

    @handle_errors
    def get_analysis_fundamentals(self, isin: str) -> dict[str, Any]:
        model = self._get_or_build_model(isin, include_market=True, include_financials=True)
        return {
            "fundamentals": {
                "valuation": model.valuation,
                "quality": model.quality,
                "growth": model.growth,
            },
            "meta": asdict(self._meta("fundamentals")),
        }

    @handle_errors
    def get_analysis_analysts(self, isin: str) -> dict[str, Any]:
        model = self._get_or_build_model(isin, include_analysts=True)
        return {"analysts": model.analysts, "meta": asdict(self._meta("analysts"))}

    @handle_errors
    def get_analysis_fund(self, isin: str) -> dict[str, Any]:
        model = self._get_or_build_model(isin, include_fund=True)
        return {"fund": model.fund, "meta": asdict(self._meta("fund"))}

    @handle_errors
    def get_analysis_full(self, isin: str) -> dict[str, Any]:
        model = self._get_or_build_model(
            isin,
            include_market=True,
            include_prices=True,
            include_financials=True,
            include_analysts=True,
            include_fund=True,
        )
        return {
            "instrument": model.instrument,
            "market": model.market,
            "profile": model.profile,
            "valuation": model.valuation,
            "quality": model.quality,
            "growth": model.growth,
            "balance_sheet": model.balance_sheet,
            "cash_flow": model.cash_flow,
            "analysts": model.analysts,
            "fund": model.fund,
            "timeseries": model.timeseries,
            "meta": asdict(self._meta("full")),
        }

    @handle_errors
    def get_analysis_benchmark_catalog(self) -> dict[str, Any]:
        analysis = self._analysis_service()
        catalog = analysis.benchmark_catalog()
        return {
            "benchmarks": catalog,
            "benchmark_items": catalog.get("items", {}) if isinstance(catalog, dict) else {},
            "benchmark_groups": catalog.get("groups", {}) if isinstance(catalog, dict) else {},
            "default": analysis.default_benchmark_key(),
            "meta": asdict(self._meta("benchmarks")),
        }

    @handle_errors
    def search_benchmark_candidates(self, query: str) -> dict[str, Any]:
        normalized_query = (query or "").strip()
        if len(normalized_query) < 2:
            raise InvalidRequestError("Query muss mindestens 2 Zeichen enthalten")
        return {
            "results": self.provider.search_quotes(normalized_query, max_results=20),
            "meta": asdict(self._meta("benchmark_search")),
        }

    @handle_errors
    def get_volatility(self, isin: str) -> dict[str, Any]:
        model = self._get_or_build_model(isin, include_prices=True)
        metrics = self._analysis_service().build_metrics_payload(model)
        return {**metrics["performance"]["volatility"], "metric": "volatility_annualized", "meta": asdict(self._meta("volatility"))}

    @handle_errors
    def get_sharpe_ratio(self, isin: str, risk_free_rate: float = 0.02) -> dict[str, Any]:
        model = self._get_or_build_model(isin, include_prices=True)
        sharpe = self._analysis_service().build_metrics_payload(model)["performance"]["sharpe_ratio"]["value"]
        if sharpe is None:
            raise PriceNotFoundError("Zu wenig Preisdaten zur Sharpe-Berechnung")
        score = max(min(((sharpe + 1.0) / 2.0) * 100.0, 100.0), 0.0)
        return {"value": round(score, 2), "ratio": round(sharpe, 4), "metric": "sharpe_ratio_annualized", "meta": asdict(self._meta("sharpe"))}

    @handle_errors
    def get_analysis_metrics(self, isin: str) -> dict[str, Any]:
        model = self._get_or_build_model(isin, include_market=True, include_prices=True, include_financials=True)
        return {
            "metrics": self._analysis_service().build_metrics_payload(model),
            "meta": asdict(self._meta("metrics")),
        }

    @handle_errors
    def get_analysis_risk(self, isin: str, benchmark_key: str | None = None) -> dict[str, Any]:
        model = self._get_or_build_model(isin, include_prices=True)
        return {
            **self._analysis_service().build_risk_payload(model, benchmark_key=benchmark_key),
            "meta": asdict(self._meta("risk")),
        }

    @handle_errors
    def get_analysis_benchmark(self, isin: str, benchmark_key: str | None = None) -> dict[str, Any]:
        model = self._get_or_build_model(isin, include_prices=True)
        return {
            **self._analysis_service().build_benchmark_payload(model, benchmark_key=benchmark_key),
            "meta": asdict(self._meta("benchmark")),
        }

    @handle_errors
    def get_analysis_timeseries(self, isin: str, series: str, benchmark_key: str | None = None) -> dict[str, Any]:
        model = self._get_or_build_model(isin, include_prices=True)
        requested = [item.strip().lower() for item in (series or "").split(",") if item.strip()]
        allowed = {"price", "returns", "drawdown", "benchmark_relative", "benchmark_price"}
        if not requested:
            requested = ["price", "returns", "drawdown"]
        invalid = [item for item in requested if item not in allowed]
        if invalid:
            raise InvalidRequestError(f"Invalid series values: {', '.join(invalid)}")
        return {
            **self._analysis_service().build_timeseries(model, requested, benchmark_key=benchmark_key),
            "meta": asdict(self._meta("timeseries_analysis")),
        }

    @handle_errors
    def get_analysis_comparison_timeseries(self, isin: str, symbols: str) -> dict[str, Any]:
        model = self._get_or_build_model(isin, include_prices=True)
        requested_symbols = self._parse_symbols(symbols)
        if not requested_symbols:
            raise InvalidRequestError("Symbols dürfen nicht leer sein")

        search_index = {
            str(item.get("symbol")).upper(): item
            for item in self.provider.search_quotes(" ".join(requested_symbols), max_results=25)
            if isinstance(item, dict) and item.get("symbol")
        }

        comparisons: list[dict[str, Any]] = []
        warnings: list[str] = []
        for symbol in requested_symbols:
            try:
                cache_entry = self._get_symbol_timeseries_cached(symbol)
                series = list(cache_entry.get("price_history") or [])
            except Exception:
                logger.warning("Vergleichszeitreihe für %s fehlgeschlagen", symbol, exc_info=True)
                warnings.append(f"Zeitreihe für {symbol} konnte nicht geladen werden")
                continue
            info = search_index.get(symbol.upper(), {})
            comparisons.append(
                {
                    "symbol": symbol,
                    "name": info.get("name") if isinstance(info, dict) else None,
                    "series": series,
                }
            )

        return {
            "company": {"isin": model.isin, "series": list(model.price_history or [])},
            "comparisons": comparisons,
            "meta": {**asdict(self._meta("comparison_timeseries")), "warnings": warnings},
        }

    def _get_or_build_model(
        self,
        isin: str,
        target_date: Optional[datetime.date] = None,
        *,
        include_market: bool = False,
        include_prices: bool = False,
        include_financials: bool = False,
        include_analysts: bool = False,
        include_fund: bool = False,
    ) -> StockModel:
        started_at = time.perf_counter()
        normalized_isin = (isin or "").strip().upper()
        if not normalized_isin:
            raise InvalidRequestError("ISIN darf nicht leer sein")

        raw = self.mongo_repo.read(normalized_isin)
        model = StockModel(**raw) if raw else StockModel(isin=normalized_isin)
        now = datetime.datetime.now(datetime.timezone.utc)
        updated_at = self._parse_ts(model.meta.get("updated_at"))

        symbol = model.instrument.get("symbol") or model.basic.get("symbol")
        if not symbol:
            symbol = self._resolve_symbol_or_raise(normalized_isin)

        provider_cache: dict[tuple[str, str | None, tuple[tuple[str, Any], ...]], Any] = {}

        if not model.instrument:
            model.instrument = self._provider_call("fetch_instrument", normalized_isin, symbol, cache=provider_cache)

        if not model.profile:
            model.profile = self._provider_call("fetch_profile", normalized_isin, symbol, cache=provider_cache)

        needs_fundamentals = bool(updated_at) and ((now - updated_at).total_seconds() > FUNDAMENTALS_TTL_SECONDS)
        if include_market and (not model.market or needs_fundamentals):
            model.market = self._provider_call("fetch_market", normalized_isin, symbol, cache=provider_cache)

        if include_financials and (not model.valuation or needs_fundamentals):
            fundamentals = self._optional_provider_call("fetch_fundamentals", normalized_isin, symbol, default={}, cache=provider_cache) or {}
            model.valuation = fundamentals.get("valuation") or {}
            model.quality = fundamentals.get("quality") or {}
            model.growth = fundamentals.get("growth") or {}
            model.balance_sheet.setdefault("snapshot", fundamentals.get("balance_sheet") or {})
            model.cash_flow.setdefault("snapshot", fundamentals.get("cash_flow") or {})

        if include_financials and (not model.balance_sheet.get("annual") or needs_fundamentals):
            financials = self._optional_provider_call("fetch_financial_statements", normalized_isin, symbol=symbol, default={}, cache=provider_cache) or {}
            model.meta["financials"] = financials
            model.balance_sheet = financials.get("balance_sheet") or {"annual": [], "quarterly": []}
            model.cash_flow = financials.get("cash_flow") or {"annual": [], "quarterly": []}

        if include_analysts and (not model.analysts or needs_fundamentals):
            model.analysts = self._optional_provider_call("fetch_analysts", normalized_isin, symbol, default={}, cache=provider_cache)

        instrument_quote_type = str(model.instrument.get("quote_type") or "").upper()
        can_have_fund = self._is_fund_like_quote_type(instrument_quote_type)
        if include_fund and can_have_fund and (not model.fund or needs_fundamentals):
            model.fund = self._optional_provider_call("fetch_fund", normalized_isin, symbol, default={}, cache=provider_cache)
        elif include_fund and not can_have_fund:
            model.fund = {}

        if include_prices:
            self._ensure_company_timeseries(
                model=model,
                isin=normalized_isin,
                symbol=symbol,
                target_date=target_date,
                provider_cache=provider_cache,
            )

        provider_name = getattr(self.provider, "provider_name", "yfinance")
        model.meta.setdefault("provider_map", {
            "instrument": provider_name,
            "market": provider_name,
            "profile": provider_name,
            "valuation": provider_name,
            "quality": provider_name,
            "growth": provider_name,
            "balance_sheet": provider_name,
            "cash_flow": provider_name,
            "analysts": provider_name,
            "fund": provider_name,
            "timeseries": provider_name,
        })
        model.meta["updated_at"] = now.replace(microsecond=0).isoformat()
        model.sync_legacy_fields()
        self.mongo_repo.write(normalized_isin, model.to_dict())
        if self.performance_logging:
            duration_ms = (time.perf_counter() - started_at) * 1000
            logger.info(
                "StockService._get_or_build_model(%s) took %.0fms (market=%s, prices=%s, financials=%s, analysts=%s, fund=%s)",
                normalized_isin,
                duration_ms,
                include_market,
                include_prices,
                include_financials,
                include_analysts,
                include_fund,
            )
        return model

    def _ensure_company_timeseries(
        self,
        *,
        model: StockModel,
        isin: str,
        symbol: str,
        target_date: Optional[datetime.date],
        provider_cache: dict[tuple[str, str | None, tuple[tuple[str, Any], ...]], Any],
    ) -> None:
        model.timeseries = model.timeseries if isinstance(model.timeseries, dict) else {}
        model.meta = model.meta if isinstance(model.meta, dict) else {}
        existing_price_history = list(model.price_history or model.timeseries.get("price_history") or [])
        existing_metrics_history = list(model.metrics_history or model.timeseries.get("metrics_history") or [])
        ts_meta = dict((model.meta.get("timeseries") or {}))

        if self._is_timeseries_fresh(existing_price_history, ts_meta) and self._has_usable_price_history(existing_price_history, target_date):
            model.price_history = existing_price_history
            model.metrics_history = existing_metrics_history
            model.timeseries["price_history"] = existing_price_history
            model.timeseries["metrics_history"] = existing_metrics_history
            model.meta["last_timeseries_refresh"] = ts_meta.get("last_refresh_at") or model.meta.get("last_timeseries_refresh")
            return

        fetch_start_date = self._timeseries_refresh_start_date(existing_price_history, ts_meta)
        fetched = self._provider_call("fetch_timeseries", isin, symbol, cache=provider_cache, start_date=fetch_start_date) or {}
        fetched_price_history = list((fetched or {}).get("price_history") or [])
        fetched_metrics_history = list((fetched or {}).get("metrics_history") or [])

        merged_price_history = self._merge_series_by_date(existing_price_history, fetched_price_history)
        merged_metrics_history = self._merge_series_by_date(existing_metrics_history, fetched_metrics_history)
        now_iso = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
        as_of = self._latest_history_date(merged_price_history)
        provider_name = getattr(self.provider, "provider_name", "yfinance")

        model.price_history = merged_price_history
        model.metrics_history = merged_metrics_history
        model.timeseries["price_history"] = merged_price_history
        model.timeseries["metrics_history"] = merged_metrics_history
        model.meta["timeseries"] = {
            "as_of": as_of,
            "updated_at": now_iso,
            "source": provider_name,
            "last_refresh_at": now_iso,
            "record_count": len(merged_price_history),
        }
        model.meta["last_timeseries_refresh"] = now_iso

    def _get_benchmark_timeseries_cached(self, symbol: str) -> dict[str, Any]:
        return self._get_symbol_timeseries_cached(symbol)

    def _get_symbol_timeseries_cached(self, symbol: str) -> dict[str, Any]:
        normalized_symbol = (symbol or "").strip().upper()
        if not normalized_symbol:
            raise InvalidRequestError("Symbol darf nicht leer sein")

        repo_read = getattr(self.mongo_repo, "read_symbol_timeseries", None)
        cached = repo_read(normalized_symbol) if callable(repo_read) else None
        cached = cached if isinstance(cached, dict) else {}
        cached_history = list(cached.get("price_history") or [])
        if self._is_timeseries_fresh(cached_history, cached):
            return cached

        refresh_start = self._timeseries_refresh_start_date(cached_history, cached)
        fresh_history = self.provider.fetch_benchmark_timeseries(normalized_symbol, start_date=refresh_start)
        merged_history = self._merge_series_by_date(cached_history, list(fresh_history or []))
        now_iso = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
        payload = {
            "symbol": normalized_symbol,
            "price_history": merged_history,
            "as_of": self._latest_history_date(merged_history),
            "updated_at": now_iso,
            "source": getattr(self.provider, "provider_name", "yfinance"),
            "last_refresh_at": now_iso,
            "record_count": len(merged_history),
        }
        repo_write = getattr(self.mongo_repo, "write_symbol_timeseries", None)
        if callable(repo_write):
            repo_write(normalized_symbol, payload)
        return payload

    @staticmethod
    def _parse_symbols(symbols_raw: str) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for token in (symbols_raw or "").split(","):
            symbol = token.strip().upper()
            if not symbol or symbol in seen:
                continue
            seen.add(symbol)
            out.append(symbol)
        return out

    def _provider_call(self, method: str, isin: str, symbol: str | None = None, *, cache: dict[tuple[str, str | None, tuple[tuple[str, Any], ...]], Any] | None = None, **kwargs: Any) -> Any:
        key_kwargs = tuple(sorted(kwargs.items()))
        key = (method, symbol, key_kwargs)
        if cache is not None and key in cache:
            return cache[key]
        started_at = time.perf_counter()

        provider_fn = getattr(self.provider, method, None)
        if callable(provider_fn):
            result = provider_fn(isin, symbol=symbol, **kwargs)
            if cache is not None:
                cache[key] = result
            if self.performance_logging:
                duration_ms = (time.perf_counter() - started_at) * 1000
                logger.info("Provider call %s for %s took %.0fms", method, isin, duration_ms)
            return result

        # Fallback für Tests mit vereinfachtem FakeProvider
        if method == "fetch_instrument":
            basic = self.provider.fetch_basic(isin, symbol=symbol)
            result = {
                "isin": basic.get("isin") or isin,
                "symbol": basic.get("symbol"),
                "short_name": basic.get("shortName"),
                "long_name": basic.get("longName"),
                "exchange": basic.get("exchange"),
                "currency": basic.get("currency"),
            }
            if cache is not None:
                cache[key] = result
            if self.performance_logging:
                duration_ms = (time.perf_counter() - started_at) * 1000
                logger.info("Provider call %s for %s took %.0fms", method, isin, duration_ms)
            return result
        if method == "fetch_profile":
            basic = self.provider.fetch_basic(isin, symbol=symbol)
            result = {"sector": basic.get("sector"), "industry": basic.get("industry"), "country": basic.get("country")}
            if cache is not None:
                cache[key] = result
            if self.performance_logging:
                duration_ms = (time.perf_counter() - started_at) * 1000
                logger.info("Provider call %s for %s took %.0fms", method, isin, duration_ms)
            return result
        if method == "fetch_market":
            metrics_fn = getattr(self.provider, "fetch_metrics", None)
            result = metrics_fn(isin, symbol=symbol) if callable(metrics_fn) else {}
            if cache is not None:
                cache[key] = result
            if self.performance_logging:
                duration_ms = (time.perf_counter() - started_at) * 1000
                logger.info("Provider call %s for %s took %.0fms", method, isin, duration_ms)
            return result
        if method == "fetch_timeseries":
            price_history_fn = getattr(self.provider, "fetch_price_history")
            metrics_history_fn = getattr(self.provider, "fetch_metrics_history", None)
            try:
                price_history = price_history_fn(isin, symbol=symbol, **kwargs)
            except TypeError:
                price_history = price_history_fn(isin, symbol=symbol)
            try:
                metrics_history = metrics_history_fn(isin, symbol=symbol, **kwargs) if callable(metrics_history_fn) else []
            except TypeError:
                metrics_history = metrics_history_fn(isin, symbol=symbol) if callable(metrics_history_fn) else []
            result = {
                "price_history": price_history,
                "metrics_history": metrics_history,
            }
            if cache is not None:
                cache[key] = result
            if self.performance_logging:
                duration_ms = (time.perf_counter() - started_at) * 1000
                logger.info("Provider call %s for %s took %.0fms", method, isin, duration_ms)
            return result
        if method in {"fetch_fundamentals", "fetch_analysts", "fetch_fund", "fetch_financial_statements"}:
            return {}
        raise InstrumentNotFoundError(f"Provider-Methode {method} fehlt")

    def _optional_provider_call(self, method: str, isin: str, symbol: str | None = None, *, default: Any, cache: dict[tuple[str, str | None, tuple[tuple[str, Any], ...]], Any] | None = None, **kwargs: Any) -> Any:
        try:
            return self._provider_call(method, isin, symbol, cache=cache, **kwargs)
        except Exception as exc:
            if self._is_optional_data_unavailable(exc):
                logger.info("Optionaler Provider-Block %s für %s/%s nicht verfügbar: %s", method, isin, symbol, exc)
            else:
                logger.warning("Optionaler Provider-Block %s für %s/%s fehlgeschlagen", method, isin, symbol, exc_info=True)
            return default

    @staticmethod
    def _is_fund_like_quote_type(quote_type: str) -> bool:
        normalized = (quote_type or "").strip().upper()
        return normalized in {"ETF", "MUTUALFUND", "MONEYMARKET", "CLOSEDEND"}

    @staticmethod
    def _is_optional_data_unavailable(exc: Exception) -> bool:
        text = str(exc).lower()
        name = exc.__class__.__name__.lower()
        return (
            "no fund data found" in text
            or "404" in text
            or "not found" in text
            or "yfdataexception" in name
        )

    def _resolve_symbol_or_raise(self, isin: str) -> str:
        try:
            return self.provider.resolve_symbol(isin)
        except Exception as exc:
            raise InstrumentNotFoundError(f"Kein Instrument für ISIN {isin} gefunden") from exc

    @staticmethod
    def _parse_ts(raw: Any) -> datetime.datetime | None:
        if not raw:
            return None
        try:
            return datetime.datetime.fromisoformat(str(raw))
        except ValueError:
            return None

    def _price_from_history_for_date(self, history: list[dict[str, Any]], target_date: Optional[datetime.date]) -> float:
        if not history:
            raise PriceNotFoundError("Keine Preishistorie verfügbar")
        normalized: list[tuple[datetime.date, float]] = []
        for entry in history:
            date_str = entry.get("date") if isinstance(entry, dict) else None
            close = entry.get("close") if isinstance(entry, dict) else None
            if date_str is None or close is None:
                continue
            try:
                normalized.append((datetime.date.fromisoformat(str(date_str)), float(close)))
            except (ValueError, TypeError):
                continue
        if not normalized:
            raise PriceNotFoundError("Keine verwertbaren Preise in der Historie gefunden")
        normalized.sort(key=lambda item: item[0])
        if target_date is None:
            return normalized[-1][1]
        for dt, close in reversed(normalized):
            if dt <= target_date:
                return close
        raise PriceNotFoundError(f"Kein Preis für ISIN vor oder am Datum {target_date.isoformat()} gefunden")

    @staticmethod
    def _has_usable_price_history(history: list[dict[str, Any]], target_date: Optional[datetime.date]) -> bool:
        if not history:
            return False
        valid_dates: list[datetime.date] = []
        for entry in history:
            date_str = entry.get("date") if isinstance(entry, dict) else None
            close = entry.get("close") if isinstance(entry, dict) else None
            if date_str is None or close is None:
                continue
            try:
                valid_dates.append(datetime.date.fromisoformat(str(date_str)))
            except ValueError:
                continue
        if not valid_dates:
            return False
        return True if target_date is None else any(dt <= target_date for dt in valid_dates)

    @staticmethod
    def _merge_series_by_date(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for entry in existing + incoming:
            if not isinstance(entry, dict):
                continue
            date_str = entry.get("date")
            if not isinstance(date_str, str):
                continue
            merged[date_str] = dict(entry)
        return [merged[key] for key in sorted(merged.keys())]

    @staticmethod
    def _latest_history_date(history: list[dict[str, Any]]) -> str | None:
        latest: datetime.date | None = None
        for entry in history:
            if not isinstance(entry, dict):
                continue
            date_raw = entry.get("date")
            if not isinstance(date_raw, str):
                continue
            try:
                parsed = datetime.date.fromisoformat(date_raw)
            except ValueError:
                continue
            if latest is None or parsed > latest:
                latest = parsed
        return latest.isoformat() if latest else None

    @staticmethod
    def _timeseries_refresh_start_date(history: list[dict[str, Any]], metadata: dict[str, Any] | None = None) -> str | None:
        latest_raw = (metadata or {}).get("as_of")
        latest_date: datetime.date | None = None
        if isinstance(latest_raw, str):
            try:
                latest_date = datetime.date.fromisoformat(latest_raw)
            except ValueError:
                latest_date = None
        if latest_date is None:
            latest_str = StockService._latest_history_date(history)
            if latest_str:
                latest_date = datetime.date.fromisoformat(latest_str)
        if latest_date is None:
            return None
        # Überlappung von 7 Tagen, um Handelskalender-/Korrektur-Effekte robust zu mergen.
        return (latest_date - datetime.timedelta(days=7)).isoformat()

    @staticmethod
    def _current_reference_date(today: datetime.date | None = None) -> datetime.date:
        ref = today or datetime.datetime.now(datetime.timezone.utc).date()
        if ref.weekday() == 6:  # Sonntag
            ref = ref - datetime.timedelta(days=2)
        elif ref.weekday() == 5:  # Samstag
            ref = ref - datetime.timedelta(days=1)
        elif datetime.datetime.now(datetime.timezone.utc).hour < 20:
            # Vor US-Handelsschluss reicht in der Regel der letzte Handelstag.
            ref = ref - datetime.timedelta(days=1)
            while ref.weekday() >= 5:
                ref = ref - datetime.timedelta(days=1)
        return ref

    def _is_timeseries_fresh(self, history: list[dict[str, Any]], metadata: dict[str, Any] | None = None) -> bool:
        latest_raw = (metadata or {}).get("as_of")
        latest_date = None
        if isinstance(latest_raw, str):
            try:
                latest_date = datetime.date.fromisoformat(latest_raw)
            except ValueError:
                latest_date = None
        if latest_date is None:
            latest_str = self._latest_history_date(history)
            if latest_str:
                latest_date = datetime.date.fromisoformat(latest_str)
        if latest_date is None:
            return False
        return latest_date >= self._current_reference_date()

    @staticmethod
    def _meta(coverage: str) -> AnalysisMetaResponse:
        return AnalysisMetaResponse(
            provider="yfinance",
            as_of=datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
            coverage=coverage,
            provider_map={
                "instrument": "yfinance",
                "market": "yfinance",
                "profile": "yfinance",
                "valuation": "yfinance",
                "quality": "yfinance",
                "growth": "yfinance",
                "balance_sheet": "yfinance",
                "cash_flow": "yfinance",
                "analysts": "yfinance",
                "fund": "yfinance",
                "timeseries": "yfinance",
            },
        )
