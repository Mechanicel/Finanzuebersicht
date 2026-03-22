import logging
from typing import Any, Optional

from src.repositories.providers.yfinance_provider import YFinanceProvider
from src.repositories.file_repository import FileRepository
from src.services.base_service import BaseService, handle_errors
from src.builders.stock_builder import StockBuilder
from src.models.stock_model import StockModel

logger = logging.getLogger(__name__)

class StockService(BaseService):
    """
    Orchestriert Basic-, History- und ETF-Modus (inkl. Mehrfach-ETFs).
    """
    def __init__(self, data_dir: Optional[str] = None):
        super().__init__()
        self.file_repo = FileRepository(data_dir)
        self.provider  = YFinanceProvider()
        self.builder   = StockBuilder(self.provider)

    @handle_errors
    def build(self, isin: str, etf_key: Optional[str] = None) -> Any:
        self.logger.debug(f"Starte Build für ISIN={isin}, etf={etf_key}")

        if etf_key:
            # 1) Existierenden Cache laden (wenn vorhanden), sonst Basisdaten
            raw = self.file_repo.read(isin)
            if raw:
                model = StockModel(**raw)
                self.logger.debug("Cache-Hit: lade bestehendes Modell mit ETF-Daten")
            else:
                model = self.builder.load_basic(isin)
                self.logger.debug("Cache-Miss: lade Basisdaten für ETF-Modus")

            # 2) History und spezifische ETF-Bewertung
            model = self.builder.load_history(model)
            model = self.builder.bewerte_etf(model, etf_key)

            # 3) Komplettes Modell speichern (inkl. aller ETF-Keys)
            self.file_repo.write(isin, model.to_dict())
            self.logger.debug(f"ETF-Daten für {etf_key} ergänzt und gespeichert für ISIN={isin}")

            # 4) Ganzes Modell zurückliefern, damit .to_dict() in der API funktioniert
            return model

        # --- historischer Modus (ohne ETF) ---
        raw = self.file_repo.read(isin)
        if raw:
            model = StockModel(**raw)
            self.logger.debug("Cache-Hit: lade bestehendes Modell ohne ETF")
        else:
            model = self.builder.load_basic(isin)
            self.logger.debug("Cache-Miss: lade Basisdaten ohne ETF")

        model = self.builder.load_history(model)
        self.file_repo.write(isin, model.to_dict())
        self.logger.debug("Cache aktualisiert mit History")
        return model
