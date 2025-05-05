import logging
from datetime import date, datetime as dt
from typing import Any, Optional

from markedataservice.src.repositories.providers.yfinance_provider import YFinanceProvider
from markedataservice.src.services.base_service import BaseService, handle_errors
from markedataservice.src.repositories.file_repository import FileRepository

from markedataservice.src.builders.stock_builder import StockBuilder
from markedataservice.src.models.stock_model import StockModel

logger = logging.getLogger(__name__)

class StockService(BaseService):
    """
    Service zur Orchestrierung des Ladevorgangs für Aktien-Daten.
    Unterstützt zwei Modi:
      - historischer Modus: liefert Basic-Daten und History (ohne ETF)
      - ETF-Modus: liefert und speichert nur die ETF-spezifischen Kennzahlen und Historie
    """
    def __init__(self, data_dir: Optional[str] = None):
        super().__init__()
        self.file_repo = FileRepository(data_dir)
        self.provider = YFinanceProvider()
        self.builder = StockBuilder(self.provider)

    @handle_errors
    def build(self, isin: str, etf_key: Optional[str] = None) -> Any:
        self.logger.debug(f"Starte Build für ISIN={isin}, etf_key={etf_key}")

        if etf_key:
            # generische ETF-Bewertung
            model = self.builder.load_basic(isin)
            model = self.builder.load_history(model)
            model = self.builder.bewerte_etf(model, etf_key.lower())
            self.file_repo.write(isin, model.to_dict())
            self.logger.debug(f"ETF-Daten für {etf_key} gespeichert für ISIN={isin}")
            return model.etf.get(etf_key.lower())

        raw = self.file_repo.read(isin)
        if raw:
            model = StockModel(**raw)
            self.logger.debug("Cache-Hit: Model aus Datei geladen")
        else:
            model = self.builder.load_basic(isin)
            self.logger.debug("Cache-Miss: Basic-Daten geladen")

        model = self.builder.load_history(model)
        self.file_repo.write(isin, model.to_dict())
        self.logger.debug("Model im Cache aktualisiert und History angehängt")
        return model

    def get_price(self, isin: str, target_date: Optional[date] = None) -> float:
        if target_date is None:
            target_date = dt.utcnow().date()
        self.logger.debug(f"[Service] Lade Preis für ISIN={isin} am oder vor {target_date}")
        history = self.provider.fetch_metrics_history(isin)
        valid = []
        for rec in history:
            rec_date_str = rec.get("date")
            if not rec_date_str:
                continue
            try:
                rec_date = date.fromisoformat(rec_date_str)
            except ValueError:
                self.logger.debug(f"Ungültiges Datum übersprungen: {rec_date_str}")
                continue
            price = rec.get("close")
            if price is not None and rec_date <= target_date:
                valid.append((rec_date, price))
        if not valid:
            self.logger.error(f"Kein Preis gefunden für ISIN={isin} am oder vor {target_date}")
            raise ValueError(f"Price not found for ISIN={isin} on or before {target_date}")
        last_date, last_price = max(valid, key=lambda x: x[0])
        self.logger.debug(f"[Service] Gewählter Preis vom {last_date}: {last_price}")
        return last_price

    def get_company(self, isin: str) -> str:
        self.logger.debug(f"[Service] Lade Firmenname für ISIN={isin}")
        basic = self.provider.fetch_basic(isin)
        name = basic.get("longName") or basic.get("shortName") or basic.get("symbol")
        if not name:
            self.logger.error(f"Firmenname nicht gefunden für ISIN={isin}")
            raise ValueError(f"Company name not found for ISIN={isin}")
        self.logger.debug(f"[Service] Firmenname: {name}")
        return name