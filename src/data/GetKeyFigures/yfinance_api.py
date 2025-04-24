import logging
import yfinance as yf

logger = logging.getLogger(__name__)

class YFinanceService:
    """
    Wrapper für Yahoo Finance Library (yfinance):
      • Basis-Kennzahlen (MarketCap, PE, EPS, Dividendenrendite)
      • Earnings-Kalender
      • Analysten-Price Targets
      • Quartalsweise GuV
      • Historische Kurse (1M)
      • Option Chains (erste Laufzeit)
      • Jahres-Financials, Bilanz, Cashflow, Earnings
    """

    def __init__(self):
        logger.debug("Initialisiere YFinanceService")

    def get_info(self, symbol: str) -> dict:
        """
        Sammelt und merged alle verfügbaren Daten-Quellen aus yfinance:
          - ticker.info
          - ticker.calendar
          - ticker.analyst_price_targets
          - ticker.quarterly_income_stmt
          - ticker.history(period='1mo')
          - ticker.option_chain(first expiration)
          - ticker.financials, balance_sheet, cashflow, earnings
        """
        logger.debug(f"YFinanceService.get_info: Sammle alle Daten für {symbol}")
        result = {}

        try:
            ticker = yf.Ticker(symbol)

            # 1) Basis-Info
            info = ticker.info or {}
            result['info'] = {
                "marketCap": info.get("marketCap"),
                "trailingPE": info.get("trailingPE"),
                "epsTrailingTwelveMonths": info.get("epsTrailingTwelveMonths"),
                "dividendYield": info.get("dividendYield"),
                # du kannst hier gerne weitere info-Keys hinzufügen...
            }

            # 2) Earnings-Kalender
            try:
                cal = ticker.calendar
                result['calendar'] = cal.to_dict() if hasattr(cal, "to_dict") else {}
            except Exception:
                logger.exception(f"YFinanceService.get_info: Fehler calendar für {symbol}")
                result['calendar'] = {}

            # 3) Analysten-Price Targets
            try:
                pt = ticker.analyst_price_targets
                result['price_targets'] = pt.to_dict() if hasattr(pt, "to_dict") else {}
            except Exception:
                logger.exception(f"YFinanceService.get_info: Fehler price_targets für {symbol}")
                result['price_targets'] = {}

            # 4) Quartals-GuV
            try:
                qis = ticker.quarterly_income_stmt
                result['quarterly_income_stmt'] = (
                    qis.reset_index().to_dict("records") if qis is not None else []
                )
            except Exception:
                logger.exception(f"YFinanceService.get_info: Fehler quarterly_income_stmt für {symbol}")
                result['quarterly_income_stmt'] = []

            # 5) Historische Kurse (1 Monat)
            try:
                hist = ticker.history(period="1mo")
                result['history_1mo'] = (
                    hist.reset_index().to_dict("records") if hist is not None else []
                )
            except Exception:
                logger.exception(f"YFinanceService.get_info: Fehler history für {symbol}")
                result['history_1mo'] = []

            # 6) Option Chain (erste Ablaufzeit)
            try:
                exps = ticker.options or []
                expiry = exps[0] if exps else None
                if expiry:
                    oc = ticker.option_chain(expiry)
                    calls = oc.calls.reset_index().to_dict("records")
                    puts  = oc.puts.reset_index().to_dict("records")
                else:
                    calls = puts = []
                result['option_chain'] = {
                    "expiration": expiry,
                    "calls": calls,
                    "puts": puts
                }
            except Exception:
                logger.exception(f"YFinanceService.get_info: Fehler option_chain für {symbol}")
                result['option_chain'] = {"expiration": None, "calls": [], "puts": []}

            # 7) Jahres-Finanzzahlen
            try:
                # Income Statement, Balance Sheet, Cashflow, Earnings
                fin  = ticker.financials
                bs   = ticker.balance_sheet
                cf   = ticker.cashflow
                er   = ticker.earnings

                result['annual_financials'] = (
                    fin.to_dict() if fin is not None else {}
                )
                result['balance_sheet'] = (
                    bs.to_dict() if bs is not None else {}
                )
                result['cashflow'] = (
                    cf.to_dict() if cf is not None else {}
                )
                result['earnings'] = (
                    er.reset_index().to_dict("records") if er is not None else []
                )
            except Exception:
                logger.exception(f"YFinanceService.get_info: Fehler annual financials für {symbol}")
                result['annual_financials'] = {}
                result['balance_sheet']   = {}
                result['cashflow']        = {}
                result['earnings']        = []

            logger.debug(f"YFinanceService.get_info: Vollständiges Ergebnis für {symbol} gesammelt")
            return result

        except Exception as e:
            logger.exception(f"YFinanceService.get_info: Schwerer Fehler für {symbol}: {e}")
            return {}
