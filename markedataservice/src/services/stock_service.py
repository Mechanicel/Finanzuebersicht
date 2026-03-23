import logging
from typing import Any, Optional

from src.repositories.providers.yfinance_provider import YFinanceProvider
from src.repositories.mongo_repository import MongoMarketDataRepository
from src.services.base_service import BaseService, handle_errors
from src.builders.stock_builder import StockBuilder
from src.models.stock_model import StockModel

logger = logging.getLogger(__name__)


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
