import os
import logging
from requests_oauthlib import OAuth1
import requests

logger = logging.getLogger(__name__)

class YahooQuoteService:
    """
    Wrapper für offizielle Yahoo Quote-API via OAuth1:
      - Aktuelle Kursdaten und Kennzahlen
    """
    URL = "https://query1.finance.yahoo.com/v7/finance/quote"

    def __init__(self):
        self.app_id = os.getenv("YAHOO_APP_ID")
        self.client_id = os.getenv("YAHOO_CLIENT_ID")
        self.client_secret = os.getenv("YAHOO_CLIENT_SECRET")
        if not (self.app_id and self.client_id and self.client_secret):
            logger.warning("YAHOO OAuth Credentials fehlen! Offizielle Quote-API ist eingeschränkt.")

    def get_quote(self, ticker: str) -> dict:
        logger.debug(f"YahooQuoteService.get_quote: Abruf Quote für {ticker}")
        if not (self.app_id and self.client_id and self.client_secret):
            logger.error("Yahoo OAuth/Credentials fehlen. Abruf abgebrochen.")
            return {}

        try:
            auth = OAuth1(self.client_id, client_secret=self.client_secret)
            r = requests.get(
                self.URL,
                params={"symbols": ticker},
                auth=auth,
                headers={"User-Agent": "Mozilla/5.0", "X-Yahoo-App-Id": self.app_id},
                timeout=5
            )
            r.raise_for_status()
            res = r.json().get("quoteResponse", {}).get("result", [])
            if res:
                quote = res[0]
                logger.debug(f"YahooQuoteService.get_quote: Quote erhalten für {ticker}")
                return quote
            else:
                logger.debug(f"YahooQuoteService.get_quote: Keine Quote für {ticker}")
                return {}
        except Exception:
            logger.exception(f"YahooQuoteService.get_quote: Fehler beim Abruf Quote für {ticker}")
            return {}
