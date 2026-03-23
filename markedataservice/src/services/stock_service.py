import datetime
import logging
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
