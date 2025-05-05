import yfinance as yf
import logging
import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class BaseProvider:
    """
    Abstrakte Provider-Klasse für Finanzdaten.
    """
    def fetch_basic(self, isin: str) -> Dict[str, Any]:
        """Basisinformationen zum Unternehmen abrufen"""
        raise NotImplementedError

    def fetch_metrics(self, isin: str) -> Dict[str, Any]:
        """Aktuelle Kennzahlen abrufen"""
        raise NotImplementedError

    def fetch_metrics_history(self, isin: str) -> List[Dict[str, Any]]:
        """Historische Kennzahlen abrufen"""
        raise NotImplementedError

    def fetch_etf_data(self, isin: str, etf_key: str) -> List[Dict[str, Any]]:
        """
        ETF-spezifische Daten abrufen (aktueller Stand + Historie).
        Leitet an eine interne Methode _fetch_<etf_key>_data weiter.
        """
        method_name = f"_fetch_{etf_key.lower()}_data"
        fetcher = getattr(self, method_name, None)
        if not fetcher:
            logger.error(f"Unbekannter ETF-Schlüssel: {etf_key}")
            raise NotImplementedError(f"Unbekannter ETF-Schlüssel: {etf_key}")
        logger.debug(f"[Provider:ETF] Dispatch zu {method_name} für ISIN={isin}")
        return fetcher(isin)