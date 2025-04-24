import logging
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

from src.data.GetKeyFigures.yfinance_api import YFinanceService
from src.data.GetKeyFigures.finnhub_api import FinnhubService
from src.data.GetKeyFigures.fmp_api import FMPService
from src.data.GetKeyFigures.alphavantage_api import AlphaVantageService
from src.data.GetKeyFigures.eodhd_api import EODHDService
from src.data.GetKeyFigures.yahoo_quote_api import YahooQuoteService

load_dotenv()
logger = logging.getLogger(__name__)

class FileGetStockInfos:
    """
    Service-Klasse für aktienbezogene Daten:
      - Ticker-Auflösung via Yahoo Search
      - Historische Kurse via Yahoo Chart
      - Fundamentaldaten via verschiedene APIs
    """

    YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"
    YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

    def __init__(self):
        logger.debug("Initialisiere FileGetStockInfos")

        # interne Caches
        self._isin_to_ticker_cache = {}
        self._company_name_cache = {}
        self._price_cache = {}

        # API Services initialisieren (Key-Management in Modul)
        self.yfinance_service = YFinanceService()
        self.finnhub_service = FinnhubService()
        self.fmp_service = FMPService()
        self.alphavantage_service = AlphaVantageService()
        self.eod_service = EODHDService()
        self.yahoo_quote_service = YahooQuoteService()

    def get_ticker_by_isin(self, isin: str) -> str:
        logger.debug(f"get_ticker_by_isin: Suche nach ISIN {isin}")
        isin = isin.strip()
        if not isin:
            return None
        if isin in self._isin_to_ticker_cache:
            return self._isin_to_ticker_cache[isin]

        try:
            r = requests.get(
                self.YAHOO_SEARCH_URL,
                params={"q": isin},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=5
            )
            r.raise_for_status()
            for q in r.json().get("quotes", []):
                sym = q.get("symbol")
                if sym:
                    self._isin_to_ticker_cache[isin] = sym
                    name = q.get("longname") or q.get("shortname")
                    if name:
                        self._company_name_cache[isin] = name
                    logger.debug(f"Ticker gefunden: {sym} für ISIN {isin}")
                    return sym
        except Exception:
            logger.exception(f"get_ticker_by_isin: Fehler bei Suche für {isin}")

        self._isin_to_ticker_cache[isin] = None
        return None

    def get_company_name_by_isin(self, isin: str) -> str:
        return self._company_name_cache.get(isin.strip())

    def get_price_by_isin(self, isin: str, date: datetime) -> float:
        logger.debug(f"get_price_by_isin: ISIN {isin} am {date}")
        ticker = self.get_ticker_by_isin(isin)
        if not ticker:
            return 0.0
        day = date.strftime("%Y-%m-%d")
        key = (ticker, day)
        if key in self._price_cache:
            return self._price_cache[key]

        period1 = int(datetime.combine(date.date(), datetime.min.time()).timestamp())
        period2 = int(datetime.combine(date.date() + timedelta(days=1), datetime.min.time()).timestamp())
        try:
            r = requests.get(
                self.YAHOO_CHART_URL.format(ticker=ticker),
                params={"period1": period1, "period2": period2, "interval": "1d"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=5
            )
            r.raise_for_status()
            res = r.json().get("chart", {}).get("result")
            if res:
                meta = res[0].get("meta", {})
                price = meta.get("chartPreviousClose") or meta.get("regularMarketPrice")
                if price is None:
                    quotes = res[0].get("indicators", {}).get("quote", [])
                    if quotes and quotes[0].get("close"):
                        price = quotes[0]["close"][-1]
                price = float(price or 0.0)
                self._price_cache[key] = price
                logger.debug(f"Preis {price} für {ticker} am {day}")
                return price
        except Exception:
            logger.exception(f"get_price_by_isin: Fehler für {ticker} am {day}")

        self._price_cache[key] = 0.0
        return 0.0

    def get_stock_info(self, isin: str) -> dict:
        logger.debug(f"get_stock_info: Anfrage für ISIN {isin}")
        ticker = self.get_ticker_by_isin(isin)
        if not ticker:
            logger.debug(f"get_stock_info: Kein Ticker für {isin}")
            return {"error": "Kein Ticker gefunden"}

        # 1) Yahoo Finance
        info = self.yfinance_service.get_info(ticker)
        if info:
            return info
        return {"error": "Keine Kennzahlen verfügbar"}
"""
        # 2) Finnhub
        info = self.finnhub_service.get_metrics(ticker)
        if info:
            return info

        # 3) Financial Modeling Prep
        info = self.fmp_service.get_full_info(ticker)
        if info:
            return info

        # 4) AlphaVantage
        info = self.alphavantage_service.get_overview(ticker)
        if info.get("MarketCapitalization") is not None:
            return info
"""
