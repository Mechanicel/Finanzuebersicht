# stock_builder.py
import logging
import datetime
from typing import List, Dict, Any

from markedataservice.src.builders.Etfs.MsciWorld import bewerte_msciworld
from markedataservice.src.models.stock_model import StockModel, ModelNotFoundError

logger = logging.getLogger(__name__)

class StockBuilder:
    """
    Erzeugt und ergänzt das StockModel mit Basic-Daten, History und ETF-spezifischen Kennzahlen.
    """

    def __init__(self, provider):
        self.provider = provider

    def load_basic(self, isin: str) -> StockModel:
        data = self.provider.fetch_basic(isin)
        return StockModel(isin=isin, basic=data)

    def load_history(self, model: StockModel) -> StockModel:
        """
        Befüllt model.metrics_history mit Quartalsdaten (3,6,9,12) der letzten 2 Jahre.
        """
        raw = self.provider.fetch_metrics_history(model.isin)
        current_metrics = self.provider.fetch_metrics(model.isin)
        model.metrics = current_metrics

        cutoff = datetime.date.today() - datetime.timedelta(days=730)
        history: List[Dict[str, Any]] = []
        shares = current_metrics.get('sharesOutstanding') or 0

        for rec in raw:
            date_str = rec.get('date')
            try:
                dt = datetime.datetime.fromisoformat(date_str).date()
            except Exception:
                continue
            if dt.month not in (3, 6, 9, 12):
                continue
            if dt < cutoff:
                continue

            entry: Dict[str, Any] = {'date': date_str}
            close = rec.get('close')
            if close is not None and shares:
                entry['marketCap'] = close * shares
            entry['averageVolume'] = rec.get('volume')
            history.append(entry)

        model.metrics_history = history
        logger.debug(f"[History] Loaded {len(history)} quarterly entries for ISIN={model.isin}")
        return model

    def bewerte_etf(self, model: StockModel, etf_key: str) -> StockModel:
        """
        Leitet je nach etf_key per If-/Elif-Kaskade an die spezifische Bewertungsmethode weiter.
        """
        key = etf_key.lower()
        if key == 'msciworld':
            return bewerte_msciworld(self, model)
        # elif key == 'emergingmarkets':
        #     return self.bewerte_emergingmarkets(model)
        else:
            logger.error(f"Unbekannter ETF-Key: {etf_key}")
            raise ModelNotFoundError(f"Kein Bewertungskonfig für ETF '{etf_key}'")


