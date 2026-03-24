from __future__ import annotations

import datetime
import logging
import math
from dataclasses import asdict, dataclass
from typing import Any, Optional

from src.models.stock_model import StockModel
from src.repositories.mongo_repository import MongoMarketDataRepository
from src.repositories.providers.yfinance_provider import YFinanceProvider
from src.services.base_service import BaseService, handle_errors

logger = logging.getLogger(__name__)

PRICE_TTL_SECONDS = 15 * 60
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
        self.mongo_repo = MongoMarketDataRepository()
        self.provider = YFinanceProvider()

    @handle_errors
    def build(self, isin: str, etf_key: Optional[str] = None) -> Any:
        model = self._get_or_build_model(isin)
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
        model = self._get_or_build_model(isin, target_date=target_date)
        return self._price_from_history_for_date(model.price_history, target_date)

    @handle_errors
    def get_analysis_snapshot(self, isin: str) -> dict[str, Any]:
        model = self._get_or_build_model(isin)
        return {
            "instrument": model.instrument,
            "market": model.market,
            "valuation": model.valuation,
            "meta": asdict(self._meta("snapshot")),
        }

    @handle_errors
    def get_analysis_financials(self, isin: str, period: str = "annual") -> dict[str, Any]:
        model = self._get_or_build_model(isin)
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
        model = self._get_or_build_model(isin)
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
        model = self._get_or_build_model(isin)
        return {"analysts": model.analysts, "meta": asdict(self._meta("analysts"))}

    @handle_errors
    def get_analysis_fund(self, isin: str) -> dict[str, Any]:
        model = self._get_or_build_model(isin)
        return {"fund": model.fund, "meta": asdict(self._meta("fund"))}

    @handle_errors
    def get_analysis_full(self, isin: str) -> dict[str, Any]:
        model = self._get_or_build_model(isin)
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
    def get_volatility(self, isin: str) -> dict[str, Any]:
        model = self._get_or_build_model(isin)
        closes = [entry["close"] for entry in self._normalize_price_history(model.price_history)]
        returns = self._daily_returns(closes)
        if not returns:
            raise PriceNotFoundError("Zu wenig Preisdaten zur Volatilitätsberechnung")
        annualized_vol = self._stddev(returns) * math.sqrt(252)
        return {"value": round(annualized_vol * 100.0, 2), "unit": "percent", "metric": "volatility_annualized", "meta": asdict(self._meta("volatility"))}

    @handle_errors
    def get_sharpe_ratio(self, isin: str, risk_free_rate: float = 0.02) -> dict[str, Any]:
        model = self._get_or_build_model(isin)
        closes = [entry["close"] for entry in self._normalize_price_history(model.price_history)]
        returns = self._daily_returns(closes)
        if not returns:
            raise PriceNotFoundError("Zu wenig Preisdaten zur Sharpe-Berechnung")
        mean_return = sum(returns) / len(returns)
        volatility = self._stddev(returns)
        if volatility == 0:
            raise PriceNotFoundError("Keine Schwankung in den Preisdaten – Sharpe nicht berechenbar")
        daily_rf = risk_free_rate / 252
        sharpe = ((mean_return - daily_rf) / volatility) * math.sqrt(252)
        score = max(min(((sharpe + 1.0) / 2.0) * 100.0, 100.0), 0.0)
        return {"value": round(score, 2), "ratio": round(sharpe, 4), "metric": "sharpe_ratio_annualized", "meta": asdict(self._meta("sharpe"))}

    def _get_or_build_model(self, isin: str, target_date: Optional[datetime.date] = None) -> StockModel:
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

        if not model.instrument:
            model.instrument = self._provider_call("fetch_instrument", normalized_isin, symbol)

        if not model.profile:
            model.profile = self._provider_call("fetch_profile", normalized_isin, symbol)

        needs_fundamentals = bool(updated_at) and ((now - updated_at).total_seconds() > FUNDAMENTALS_TTL_SECONDS)
        if not model.market or needs_fundamentals:
            model.market = self._provider_call("fetch_market", normalized_isin, symbol)

        if not model.valuation or needs_fundamentals:
            fundamentals = self._provider_call("fetch_fundamentals", normalized_isin, symbol) or {}
            model.valuation = fundamentals.get("valuation") or {}
            model.quality = fundamentals.get("quality") or {}
            model.growth = fundamentals.get("growth") or {}
            model.balance_sheet.setdefault("snapshot", fundamentals.get("balance_sheet") or {})
            model.cash_flow.setdefault("snapshot", fundamentals.get("cash_flow") or {})

        if not model.balance_sheet.get("annual") or needs_fundamentals:
            financials = self._provider_call("fetch_financial_statements", normalized_isin, symbol=symbol) or {}
            model.meta["financials"] = financials
            model.balance_sheet = financials.get("balance_sheet") or {"annual": [], "quarterly": []}
            model.cash_flow = financials.get("cash_flow") or {"annual": [], "quarterly": []}

        if not model.analysts or needs_fundamentals:
            model.analysts = self._provider_call("fetch_analysts", normalized_isin, symbol)

        if not model.fund or needs_fundamentals:
            model.fund = self._provider_call("fetch_fund", normalized_isin, symbol)

        needs_prices = bool(updated_at) and ((now - updated_at).total_seconds() > PRICE_TTL_SECONDS)
        if not self._has_usable_price_history(model.price_history, target_date) or needs_prices:
            model.timeseries = self._provider_call("fetch_timeseries", normalized_isin, symbol)
            model.price_history = list((model.timeseries or {}).get("price_history") or [])
            model.metrics_history = list((model.timeseries or {}).get("metrics_history") or [])

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
        return model

    def _provider_call(self, method: str, isin: str, symbol: str | None = None, **kwargs: Any) -> Any:
        provider_fn = getattr(self.provider, method, None)
        if callable(provider_fn):
            return provider_fn(isin, symbol=symbol, **kwargs)

        # Fallback für Tests mit vereinfachtem FakeProvider
        if method == "fetch_instrument":
            basic = self.provider.fetch_basic(isin, symbol=symbol)
            return {
                "isin": basic.get("isin") or isin,
                "symbol": basic.get("symbol"),
                "short_name": basic.get("shortName"),
                "long_name": basic.get("longName"),
                "exchange": basic.get("exchange"),
                "currency": basic.get("currency"),
            }
        if method == "fetch_profile":
            basic = self.provider.fetch_basic(isin, symbol=symbol)
            return {"sector": basic.get("sector"), "industry": basic.get("industry"), "country": basic.get("country")}
        if method == "fetch_market":
            metrics_fn = getattr(self.provider, "fetch_metrics", None)
            return metrics_fn(isin, symbol=symbol) if callable(metrics_fn) else {}
        if method == "fetch_timeseries":
            return {
                "price_history": self.provider.fetch_price_history(isin, symbol=symbol),
                "metrics_history": self.provider.fetch_metrics_history(isin, symbol=symbol) if hasattr(self.provider, "fetch_metrics_history") else [],
            }
        if method in {"fetch_fundamentals", "fetch_analysts", "fetch_fund", "fetch_financial_statements"}:
            return {}
        raise InstrumentNotFoundError(f"Provider-Methode {method} fehlt")

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

    def _normalize_price_history(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for entry in history or []:
            if not isinstance(entry, dict):
                continue
            date_str = entry.get("date")
            close = self._to_float(entry.get("close"))
            if not date_str or close is None:
                continue
            normalized.append({"date": str(date_str), "close": close})
        normalized.sort(key=lambda item: item["date"])
        return normalized
