import datetime
import logging
import math
from dataclasses import asdict, dataclass
from typing import Any, Optional

from src.repositories.providers.yfinance_provider import YFinanceProvider
from src.repositories.mongo_repository import MongoMarketDataRepository
from src.services.base_service import BaseService, handle_errors
from src.builders.stock_builder import StockBuilder
from src.models.stock_model import StockModel

logger = logging.getLogger(__name__)


class StockServiceError(Exception):
    """Basisklasse für fachliche Fehler im StockService."""


class InvalidRequestError(StockServiceError):
    """Ungültige Nutzereingaben."""


class InstrumentNotFoundError(StockServiceError):
    """Instrument konnte nicht aufgelöst werden."""


class PriceNotFoundError(StockServiceError):
    """Preis konnte nicht ermittelt werden."""


@dataclass
class InstrumentResponse:
    isin: str
    symbol: Optional[str]
    shortName: Optional[str]
    longName: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    country: Optional[str]
    exchange: Optional[str]


@dataclass
class MarketResponse:
    currentPrice: Optional[float]
    marketCap: Optional[float]
    averageVolume: Optional[float]
    currency: Optional[str]
    lastPriceDate: Optional[str]


@dataclass
class ValuationResponse:
    trailingPE: Optional[float]
    forwardPE: Optional[float]


@dataclass
class AnalysisMetaResponse:
    provider: str
    as_of: str
    coverage: str


class StockService(BaseService):
    """Orchestriert Basic-, History- und ETF-Modus mit MongoDB-Cache."""

    def __init__(self):
        super().__init__()
        self.mongo_repo = MongoMarketDataRepository()
        self.provider = YFinanceProvider()
        self.builder = StockBuilder(self.provider)

    @handle_errors
    def build(self, isin: str, etf_key: Optional[str] = None) -> Any:
        self.logger.debug("Starte Build für ISIN=%s, etf=%s", isin, etf_key)

        if etf_key:
            raw = self.mongo_repo.read(isin)
            if raw:
                model = StockModel(**raw)
                self.logger.debug("Cache-Hit: lade bestehendes Modell mit ETF-Daten")
            else:
                model = self.builder.load_basic(isin)
                self.logger.debug("Cache-Miss: lade Basisdaten für ETF-Modus")

            model = self.builder.load_history(model)
            model = self.builder.bewerte_etf(model, etf_key)
            self.mongo_repo.write(isin, model.to_dict())
            self.logger.debug("ETF-Daten für %s ergänzt und in Mongo gespeichert für ISIN=%s", etf_key, isin)
            return model

        raw = self.mongo_repo.read(isin)
        if raw:
            model = StockModel(**raw)
            self.logger.debug("Cache-Hit: lade bestehendes Modell ohne ETF")
        else:
            model = self.builder.load_basic(isin)
            self.logger.debug("Cache-Miss: lade Basisdaten ohne ETF")

        model = self.builder.load_history(model)
        self.mongo_repo.write(isin, model.to_dict())
        self.logger.debug("Cache aktualisiert mit History")
        return model

    @handle_errors
    def get_company(self, isin: str) -> str:
        model = self._get_or_build_model(isin)
        return self._extract_company_name(model)

    @handle_errors
    def get_price(self, isin: str, target_date: Optional[datetime.date]) -> float:
        model = self._get_or_build_model(isin, target_date=target_date)
        return self._price_from_history_for_date(model.price_history, target_date)

    @handle_errors
    def get_analysis_snapshot(self, isin: str) -> dict[str, Any]:
        model = self._get_or_build_model(isin)
        instrument = self._instrument_from_basic(model)
        market = self._market_from_model(model)
        valuation = self._valuation_from_model(model)
        snapshot = {
            "instrument": asdict(instrument),
            "market": asdict(market),
            "valuation": asdict(valuation),
            "meta": asdict(self._meta("snapshot")),
        }
        return snapshot

    @handle_errors
    def get_analysis_full(self, isin: str) -> dict[str, Any]:
        model = self._get_or_build_model(isin)
        payload = {
            "instrument": asdict(self._instrument_from_basic(model)),
            "market": asdict(self._market_from_model(model)),
            "valuation": asdict(self._valuation_from_model(model)),
            "metrics": self._sanitize_dict(model.metrics),
            "timeseries": {
                "price_history": self._normalize_price_history(model.price_history),
                "metrics_history": self._normalize_metrics_history(model.metrics_history),
            },
            "meta": asdict(self._meta("full")),
        }
        return payload

    @handle_errors
    def get_volatility(self, isin: str) -> dict[str, Any]:
        model = self._get_or_build_model(isin)
        closes = [entry["close"] for entry in self._normalize_price_history(model.price_history)]
        returns = self._daily_returns(closes)
        if not returns:
            raise PriceNotFoundError("Zu wenig Preisdaten zur Volatilitätsberechnung")

        annualized_vol = self._stddev(returns) * math.sqrt(252)
        return {
            "value": round(annualized_vol * 100.0, 2),
            "unit": "percent",
            "metric": "volatility_annualized",
            "meta": asdict(self._meta("volatility")),
        }

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
        return {
            "value": round(score, 2),
            "ratio": round(sharpe, 4),
            "metric": "sharpe_ratio_annualized",
            "meta": asdict(self._meta("sharpe")),
        }

    def _get_or_build_model(self, isin: str, target_date: Optional[datetime.date] = None) -> StockModel:
        normalized_isin = (isin or "").strip().upper()
        if not normalized_isin:
            raise InvalidRequestError("ISIN darf nicht leer sein")

        raw = self.mongo_repo.read(normalized_isin)
        model = StockModel(**raw) if raw else StockModel(isin=normalized_isin)
        needs_write = raw is None

        symbol = model.basic.get("symbol") if isinstance(model.basic, dict) else None
        if not symbol:
            symbol = self._resolve_symbol_or_raise(normalized_isin)

        if not model.basic:
            model.basic = self.provider.fetch_basic(normalized_isin, symbol=symbol)
            needs_write = True

        if not model.basic.get("symbol"):
            model.basic["symbol"] = symbol
            needs_write = True

        if not model.metrics:
            model.metrics = self.provider.fetch_metrics(normalized_isin, symbol=model.basic.get("symbol"))
            needs_write = True

        if not model.metrics_history:
            model.metrics_history = self.builder.load_history(model).metrics_history
            needs_write = True

        if not self._has_usable_price_history(model.price_history, target_date):
            model.price_history = self.provider.fetch_price_history(normalized_isin, symbol=model.basic.get("symbol"))
            needs_write = True

        if needs_write:
            self.mongo_repo.write(normalized_isin, model.to_dict())
            self.logger.debug("StockService: Cache aktualisiert für ISIN=%s", normalized_isin)

        return model

    def _resolve_symbol_or_raise(self, isin: str) -> str:
        try:
            return self.provider.resolve_symbol(isin)
        except Exception as exc:
            self.logger.warning("StockService: Symbolauflösung fehlgeschlagen für %s: %s", isin, exc)
            raise InstrumentNotFoundError(f"Kein Instrument für ISIN {isin} gefunden") from exc

    @staticmethod
    def _extract_company_name(model_or_basic_dict: StockModel | dict[str, Any]) -> str:
        basic = model_or_basic_dict.basic if isinstance(model_or_basic_dict, StockModel) else model_or_basic_dict
        if not isinstance(basic, dict):
            raise InstrumentNotFoundError("Instrument enthält keine Basisdaten")

        for key in ("longName", "shortName", "symbol"):
            value = basic.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        raise InstrumentNotFoundError("Kein Firmenname für dieses Instrument verfügbar")

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
                dt = datetime.date.fromisoformat(str(date_str))
                normalized.append((dt, float(close)))
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
            if not isinstance(entry, dict):
                continue
            date_str = entry.get("date")
            close = entry.get("close")
            if date_str is None or close is None:
                continue
            try:
                valid_dates.append(datetime.date.fromisoformat(str(date_str)))
            except ValueError:
                continue

        if not valid_dates:
            return False

        if target_date is None:
            return True
        return any(dt <= target_date for dt in valid_dates)

    def _instrument_from_basic(self, model: StockModel) -> InstrumentResponse:
        basic = self._sanitize_dict(model.basic)
        return InstrumentResponse(
            isin=str(basic.get("isin") or model.isin),
            symbol=basic.get("symbol"),
            shortName=basic.get("shortName"),
            longName=basic.get("longName"),
            sector=basic.get("sector"),
            industry=basic.get("industry"),
            country=basic.get("country"),
            exchange=basic.get("exchange"),
        )

    def _market_from_model(self, model: StockModel) -> MarketResponse:
        metrics = self._sanitize_dict(model.metrics)
        current_price = None
        last_price_date = None
        normalized_prices = self._normalize_price_history(model.price_history)
        if normalized_prices:
            latest = normalized_prices[-1]
            current_price = latest.get("close")
            last_price_date = latest.get("date")

        return MarketResponse(
            currentPrice=current_price,
            marketCap=self._to_float(metrics.get("marketCap")),
            averageVolume=self._to_float(metrics.get("averageVolume")),
            currency=metrics.get("currency") or model.basic.get("currency") if isinstance(model.basic, dict) else None,
            lastPriceDate=last_price_date,
        )

    def _valuation_from_model(self, model: StockModel) -> ValuationResponse:
        metrics = self._sanitize_dict(model.metrics)
        return ValuationResponse(
            trailingPE=self._to_float(metrics.get("trailingPE")),
            forwardPE=self._to_float(metrics.get("forwardPE")),
        )

    @staticmethod
    def _meta(coverage: str) -> AnalysisMetaResponse:
        return AnalysisMetaResponse(
            provider="yfinance",
            as_of=datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
            coverage=coverage,
        )

    @staticmethod
    def _sanitize_dict(raw: Any) -> dict[str, Any]:
        return raw if isinstance(raw, dict) else {}

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

    def _normalize_metrics_history(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for entry in history or []:
            if not isinstance(entry, dict):
                continue
            row = dict(entry)
            if "date" in row and row["date"] is not None:
                row["date"] = str(row["date"])
            normalized.append(row)
        normalized.sort(key=lambda item: item.get("date", ""))
        return normalized

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _daily_returns(closes: list[float]) -> list[float]:
        if len(closes) < 2:
            return []
        returns: list[float] = []
        for idx in range(1, len(closes)):
            previous = closes[idx - 1]
            current = closes[idx]
            if previous <= 0:
                continue
            returns.append((current / previous) - 1.0)
        return returns

    @staticmethod
    def _stddev(values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((val - mean) ** 2 for val in values) / (len(values) - 1)
        return math.sqrt(variance)
