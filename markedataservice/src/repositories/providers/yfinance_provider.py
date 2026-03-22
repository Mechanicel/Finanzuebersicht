import yfinance as yf
import datetime
from typing import Dict, List, Any

from src.repositories.providers.base_provider import BaseProvider, logger

class YFinanceProvider(BaseProvider):
    """
    Provider-Implementierung, die Daten über yfinance bezieht.
    """
    def fetch_basic(self, isin: str) -> Dict[str, Any]:
        logger.debug(f"[YFinance] Fetch basic for {isin}")
        ticker = yf.Ticker(isin)
        info = ticker.info or {}
        basic = {
            "symbol": info.get("symbol"),
            "shortName": info.get("shortName"),
            "longName": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "exchange": info.get("exchange"),
        }
        logger.debug(f"[YFinance] Basic data: {basic}")
        return basic

    def fetch_metrics(self, isin: str) -> Dict[str, Any]:
        logger.debug(f"[YFinance] Fetch metrics for {isin}")
        ticker = yf.Ticker(isin)
        info = ticker.info or {}
        # Try fast_info free_float first
        free_float: Any = None
        try:
            fast = getattr(ticker, 'fast_info', None)
            if fast and hasattr(fast, 'free_float'):
                free_float = fast.free_float
                logger.debug(f"[YFinance] Using fast_info.free_float={free_float}")
        except Exception:
            pass

        # Fallbacks if fast_info not available or returned None
        if free_float is None:
            # (1) floatPercent field (in Prozent)
            float_pct = info.get("floatPercent")
            if float_pct is not None:
                try:
                    free_float = float_pct / 100.0
                    logger.debug(f"[YFinance] Using info.floatPercent={float_pct}" )
                except Exception:
                    free_float = None
        if free_float is None:
            # (2) floatShares / sharesOutstanding
            float_shares = info.get("floatShares")
            shares_outstanding = info.get("sharesOutstanding")
            if float_shares and shares_outstanding:
                try:
                    free_float = float_shares / shares_outstanding
                    logger.debug(f"[YFinance] Calculated free_float from floatShares/sharesOutstanding: {free_float}")
                except Exception:
                    free_float = None
        if free_float is None:
            # (3) floatMarketCap / marketCap
            float_mc = info.get("floatMarketCap")
            mc = info.get("marketCap")
            if float_mc and mc:
                try:
                    free_float = float_mc / mc
                    logger.debug(f"[YFinance] Calculated free_float from floatMarketCap/marketCap: {free_float}")
                except Exception:
                    free_float = None
        # Do not cap to 1, retain value or None

        metrics = {
            "marketCap": info.get("marketCap"),
            "floatShares": info.get("floatShares"),
            "floatMarketCap": info.get("floatMarketCap"),
            "sharesOutstanding": info.get("sharesOutstanding"),
            "averageVolume": info.get("averageVolume"),
            "freeFloat": free_float,
            "trailingPE": info.get("trailingPE"),
            "forwardPE": info.get("forwardPE"),
        }
        logger.debug(f"[YFinance] Metrics data: {metrics}")
        return metrics

    def fetch_metrics_history(self, isin: str) -> List[Dict[str, Any]]:
        logger.debug(f"[YFinance] Fetch metrics history for {isin}")
        ticker = yf.Ticker(isin)
        hist = ticker.history(period='24mo', interval='1mo', actions=True)
        history: List[Dict[str, Any]] = []
        for dt, row in hist.iterrows():
            entry = {
                "date": dt.date().isoformat(),
                "open": row.get("Open"),
                "high": row.get("High"),
                "low": row.get("Low"),
                "close": row.get("Close"),
                "volume": row.get("Volume"),
                "dividends": row.get("Dividends"),
                "stockSplits": row.get("Stock Splits"),
            }
            history.append(entry)
        logger.debug(f"[YFinance] Loaded {len(history)} historical entries")
        return history

    def fetch_etf_data(self, isin: str, etf_key: str) -> List[Dict[str, Any]]:
        logger.debug(f"[YFinance:ETF] Fetch ETF data for {isin}, ETF={etf_key}")
        return super().fetch_etf_data(isin, etf_key)

    def _build_etf_entries(self, isin: str, keys: List[str], etf_name: str) -> List[Dict[str, Any]]:
        logger.debug(f"[YFinance:ETF:{etf_name}] Lade Daten für ISIN={isin}")
        raw_metrics = self.fetch_metrics(isin)
        raw_history = self.fetch_metrics_history(isin)

        entries: List[Dict[str, Any]] = []
        current = {"date": datetime.date.today().isoformat()}
        for k in keys:
            current[k] = raw_metrics.get(k)
        entries.append(current)
        logger.debug(f"[YFinance:ETF:{etf_name}] Aktuelle Kennzahlen: {current}")

        for rec in raw_history:
            entry = {"date": rec.get("date")}
            for k in keys:
                entry[k] = rec.get(k)
            entries.append(entry)
        logger.debug(f"[YFinance:ETF:{etf_name}] Insgesamt {len(entries)} Einträge")
        return entries