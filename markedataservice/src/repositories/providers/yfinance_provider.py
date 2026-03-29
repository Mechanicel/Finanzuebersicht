from __future__ import annotations

import datetime
from typing import Any, Dict, List

import pandas as pd
import yfinance as yf

from src.repositories.providers.base_provider import BaseProvider, logger


class YahooInstrumentClient:
    def get_info(self, ticker: Any) -> Dict[str, Any]:
        return ticker.info or {}

    def fetch_instrument(self, isin: str, symbol: str, info: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "isin": info.get("isin") or isin,
            "symbol": info.get("symbol") or symbol,
            "short_name": info.get("shortName"),
            "long_name": info.get("longName"),
            "exchange": info.get("exchange"),
            "quote_type": info.get("quoteType"),
            "currency": info.get("currency"),
        }

    def fetch_profile(self, info: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "website": info.get("website"),
            "employees": info.get("fullTimeEmployees"),
            "business_summary": info.get("longBusinessSummary"),
        }


class YahooMarketClient:
    @staticmethod
    def _safe_div(a: Any, b: Any) -> float | None:
        try:
            if a is None or b in (None, 0):
                return None
            return float(a) / float(b)
        except (TypeError, ValueError, ZeroDivisionError):
            return None

    @staticmethod
    def _sanitize_free_float(value: Any) -> float | None:
        try:
            if value is None:
                return None
            normalized = float(value)
            if 0.0 <= normalized <= 1.0:
                return normalized
        except (TypeError, ValueError):
            return None
        return None

    def fetch_market(self, info: Dict[str, Any], ticker: Any) -> Dict[str, Any]:
        free_float = None
        try:
            fast = getattr(ticker, "fast_info", None)
            if fast and hasattr(fast, "free_float"):
                free_float = fast.free_float
        except Exception:
            logger.debug("[YFinance] fast_info.free_float nicht verfügbar", exc_info=True)

        if free_float is None:
            float_percent = info.get("floatPercent")
            free_float = self._safe_div(float_percent, 100)
        if free_float is None:
            free_float = self._safe_div(info.get("floatShares"), info.get("sharesOutstanding"))
        if free_float is None:
            free_float = self._safe_div(info.get("floatMarketCap"), info.get("marketCap"))
        free_float = self._sanitize_free_float(free_float)

        return {
            "currentPrice": info.get("currentPrice"),
            "previousClose": info.get("previousClose"),
            "open": info.get("open"),
            "dayHigh": info.get("dayHigh"),
            "dayLow": info.get("dayLow"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "marketCap": info.get("marketCap"),
            "averageVolume": info.get("averageVolume"),
            "averageVolume10days": info.get("averageVolume10days"),
            "sharesOutstanding": info.get("sharesOutstanding"),
            "floatShares": info.get("floatShares"),
            "freeFloat": free_float,
            "currency": info.get("currency"),
        }

    def fetch_timeseries(self, ticker: Any, start_date: str | None = None) -> Dict[str, Any]:
        monthly = ticker.history(period="24mo", interval="1mo", actions=True)
        if start_date:
            daily = ticker.history(start=start_date, interval="1d", auto_adjust=False, actions=False)
        else:
            daily = ticker.history(period="10y", interval="1d", auto_adjust=False, actions=False)

        metrics_history: List[Dict[str, Any]] = []
        for dt, row in monthly.iterrows():
            metrics_history.append(
                {
                    "date": dt.date().isoformat(),
                    "open": row.get("Open"),
                    "high": row.get("High"),
                    "low": row.get("Low"),
                    "close": row.get("Close"),
                    "volume": row.get("Volume"),
                    "dividends": row.get("Dividends"),
                    "stockSplits": row.get("Stock Splits"),
                }
            )

        price_history: List[Dict[str, Any]] = []
        for dt, row in daily.iterrows():
            close = row.get("Close")
            if close is None:
                continue
            price_history.append({"date": dt.date().isoformat(), "close": float(close)})

        return {"metrics_history": metrics_history, "price_history": price_history}

    def fetch_benchmark_price_history(self, symbol: str, start_date: str | None = None) -> List[Dict[str, Any]]:
        ticker = yf.Ticker(symbol)
        if start_date:
            daily = ticker.history(start=start_date, interval="1d", auto_adjust=False, actions=False)
        else:
            daily = ticker.history(period="10y", interval="1d", auto_adjust=False, actions=False)
        price_history: List[Dict[str, Any]] = []
        for dt, row in daily.iterrows():
            close = row.get("Close")
            if close is None:
                continue
            price_history.append({"date": dt.date().isoformat(), "close": float(close)})
        return price_history


class YahooFinancialsClient:
    @staticmethod
    def _frame_to_records(frame: pd.DataFrame | None) -> List[Dict[str, Any]]:
        if frame is None or frame.empty:
            return []
        records: List[Dict[str, Any]] = []
        for col in frame.columns:
            rec = {"date": str(col.date()) if hasattr(col, "date") else str(col)}
            series = frame[col]
            for key, value in series.items():
                rec[str(key)] = None if pd.isna(value) else value
            records.append(rec)
        records.sort(key=lambda x: x.get("date") or "")
        return records

    def fetch_financials(self, ticker: Any) -> Dict[str, Any]:
        return {
            "income_statement": {
                "annual": self._frame_to_records(getattr(ticker, "financials", None)),
                "quarterly": self._frame_to_records(getattr(ticker, "quarterly_financials", None)),
            },
            "balance_sheet": {
                "annual": self._frame_to_records(getattr(ticker, "balance_sheet", None)),
                "quarterly": self._frame_to_records(getattr(ticker, "quarterly_balance_sheet", None)),
            },
            "cash_flow": {
                "annual": self._frame_to_records(getattr(ticker, "cash_flow", None)),
                "quarterly": self._frame_to_records(getattr(ticker, "quarterly_cash_flow", None)),
            },
        }

    def fetch_fundamentals(self, info: Dict[str, Any]) -> Dict[str, Any]:
        valuation = {
            "enterpriseValue": info.get("enterpriseValue"),
            "trailingPE": info.get("trailingPE"),
            "forwardPE": info.get("forwardPE"),
            "priceToBook": info.get("priceToBook"),
            "priceToSalesTrailing12Months": info.get("priceToSalesTrailing12Months"),
            "enterpriseToRevenue": info.get("enterpriseToRevenue"),
            "enterpriseToEbitda": info.get("enterpriseToEbitda"),
        }
        quality = {
            "returnOnEquity": info.get("returnOnEquity"),
            "returnOnAssets": info.get("returnOnAssets"),
            "grossMargins": info.get("grossMargins"),
            "operatingMargins": info.get("operatingMargins"),
            "profitMargins": info.get("profitMargins"),
            "currentRatio": info.get("currentRatio"),
            "quickRatio": info.get("quickRatio"),
            "debtToEquity": info.get("debtToEquity"),
            "payoutRatio": info.get("payoutRatio"),
        }
        growth = {
            "revenueGrowth": info.get("revenueGrowth"),
            "earningsGrowth": info.get("earningsGrowth"),
            "earningsQuarterlyGrowth": info.get("earningsQuarterlyGrowth"),
            "trailingEps": info.get("trailingEps"),
            "forwardEps": info.get("forwardEps"),
        }
        balance_sheet = {
            "totalCash": info.get("totalCash"),
            "totalDebt": info.get("totalDebt"),
            "totalRevenue": info.get("totalRevenue"),
            "bookValue": info.get("bookValue"),
        }
        cash_flow = {
            "operatingCashflow": info.get("operatingCashflow"),
            "freeCashflow": info.get("freeCashflow"),
        }
        return {
            "valuation": valuation,
            "quality": quality,
            "growth": growth,
            "balance_sheet": balance_sheet,
            "cash_flow": cash_flow,
        }


class YahooAnalystClient:
    @staticmethod
    def _safe_records(frame: pd.DataFrame | None) -> List[Dict[str, Any]]:
        if frame is None or frame.empty:
            return []
        df = frame.reset_index(drop=False)
        return df.where(pd.notna(df), None).to_dict(orient="records")

    def _safe_attr_records(self, ticker: Any, attr: str) -> List[Dict[str, Any]]:
        try:
            return self._safe_records(getattr(ticker, attr, None))
        except Exception:
            logger.debug("[YFinance] optionale Analystendaten %s nicht verfügbar", attr, exc_info=True)
            return []

    def fetch_analysts(self, ticker: Any, info: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "recommendationMean": info.get("recommendationMean"),
            "recommendationKey": info.get("recommendationKey"),
            "numberOfAnalystOpinions": info.get("numberOfAnalystOpinions"),
            "targetMeanPrice": info.get("targetMeanPrice"),
            "targetHighPrice": info.get("targetHighPrice"),
            "targetLowPrice": info.get("targetLowPrice"),
            "earnings_estimate": self._safe_attr_records(ticker, "earnings_estimate"),
            "revenue_estimate": self._safe_attr_records(ticker, "revenue_estimate"),
            "eps_trend": self._safe_attr_records(ticker, "eps_trend"),
            "upgrades_downgrades": self._safe_attr_records(ticker, "upgrades_downgrades"),
        }


class YahooFundClient:
    @staticmethod
    def _holders(frame: pd.DataFrame | None) -> List[Dict[str, Any]]:
        if frame is None or frame.empty:
            return []
        return frame.where(pd.notna(frame), None).to_dict(orient="records")

    @staticmethod
    def is_fund_like_quote_type(quote_type: str | None) -> bool:
        normalized = str(quote_type or "").upper()
        return normalized in {"ETF", "MUTUALFUND", "MONEYMARKET", "CLOSEDEND"}

    def fetch_fund(self, ticker: Any, info: Dict[str, Any]) -> Dict[str, Any]:
        quote_type = str(info.get("quoteType") or "").upper()
        if not self.is_fund_like_quote_type(quote_type):
            return {}

        holdings: List[Dict[str, Any]] = []
        try:
            funds_data = getattr(ticker, "funds_data", None)
            top_holdings = getattr(funds_data, "top_holdings", None) if funds_data else None
            holdings = self._holders(top_holdings)
        except Exception:
            logger.debug("[YFinance] optionale Fund-Holdings nicht verfügbar", exc_info=True)

        return {
            "quoteType": quote_type,
            "category": info.get("category"),
            "fundFamily": info.get("fundFamily"),
            "legalType": info.get("legalType"),
            "yield": info.get("yield"),
            "beta3Year": info.get("beta3Year"),
            "totalAssets": info.get("totalAssets"),
            "annualHoldingsTurnover": info.get("annualHoldingsTurnover"),
            "bondRatings": info.get("bondRatings"),
            "sectorWeightings": info.get("sectorWeightings"),
            "holdings": holdings,
        }


class YFinanceProvider(BaseProvider):
    provider_name = "yfinance"

    def __init__(self) -> None:
        self._symbol_cache: dict[str, str] = {}
        self._ticker_bundle_cache: dict[str, tuple[Any, Dict[str, Any]]] = {}
        self.instrument_client = YahooInstrumentClient()
        self.market_client = YahooMarketClient()
        self.financials_client = YahooFinancialsClient()
        self.analyst_client = YahooAnalystClient()
        self.fund_client = YahooFundClient()

    def resolve_symbol(self, isin: str) -> str:
        normalized_isin = (isin or "").strip().upper()
        if not normalized_isin:
            raise ValueError("ISIN darf nicht leer sein")

        if normalized_isin in self._symbol_cache:
            return self._symbol_cache[normalized_isin]

        symbols = self._search_symbols(normalized_isin) or self._fallback_symbol_lookup(normalized_isin)
        if not symbols:
            raise LookupError(f"Kein Yahoo-Symbol für ISIN {normalized_isin} gefunden")

        best_symbol = self._pick_best_symbol(normalized_isin, symbols)
        self._symbol_cache[normalized_isin] = best_symbol
        return best_symbol

    def resolve_instrument_for_symbol(self, symbol: str) -> Dict[str, Any]:
        normalized_symbol = (symbol or "").strip().upper()
        if not normalized_symbol:
            return {}
        candidates = self.search_quotes(normalized_symbol, max_results=8)
        exact = next((item for item in candidates if str(item.get("symbol") or "").upper() == normalized_symbol), None)
        if exact:
            return {
                "symbol": exact.get("symbol") or normalized_symbol,
                "isin": exact.get("isin"),
                "name": exact.get("name"),
                "exchange": exact.get("exchange"),
                "quote_type": exact.get("quote_type"),
                "currency": exact.get("currency"),
            }
        try:
            info = yf.Ticker(normalized_symbol).info or {}
        except Exception:
            info = {}
        return {
            "symbol": info.get("symbol") or normalized_symbol,
            "isin": info.get("isin"),
            "name": info.get("shortName") or info.get("longName"),
            "exchange": info.get("exchange"),
            "quote_type": info.get("quoteType"),
            "currency": info.get("currency"),
        }

    def _search_symbols(self, isin: str) -> List[Dict[str, Any]]:
        quotes = self.search_quotes(isin, max_results=12)
        return [{"symbol": q.get("symbol"), "quote": q} for q in quotes if q.get("symbol")]

    def search_quotes(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        normalized_query = (query or "").strip()
        if not normalized_query:
            return []
        try:
            search = yf.Search(
                query=normalized_query,
                max_results=max_results,
                news_count=0,
                lists_count=0,
                include_cb=False,
                enable_fuzzy_query=False,
                raise_errors=False,
            )
        except Exception:
            return []
        out: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for quote in getattr(search, "quotes", []) or []:
            if not isinstance(quote, dict):
                continue
            symbol = str(quote.get("symbol") or "").strip()
            if not symbol:
                continue
            upper_symbol = symbol.upper()
            if upper_symbol in seen:
                continue
            seen.add(upper_symbol)

            entry: Dict[str, Any] = {
                "symbol": symbol,
                "name": quote.get("shortname") or quote.get("longname") or quote.get("name"),
                "isin": quote.get("isin"),
                "exchange": quote.get("exchange") or quote.get("exchDisp"),
                "quote_type": quote.get("quoteType"),
                "currency": quote.get("currency"),
                "region": quote.get("region") or quote.get("market"),
            }

            if not entry.get("isin"):
                try:
                    info = yf.Ticker(symbol).info or {}
                except Exception:
                    info = {}
                entry["isin"] = info.get("isin") or entry.get("isin")
                entry["exchange"] = entry.get("exchange") or info.get("exchange")
                entry["quote_type"] = entry.get("quote_type") or info.get("quoteType")
                entry["currency"] = entry.get("currency") or info.get("currency")
                entry["region"] = entry.get("region") or info.get("region") or info.get("country")
                entry["name"] = entry.get("name") or info.get("shortName") or info.get("longName")

            out.append(entry)
            if len(out) >= max_results:
                break
        return out

    def _fallback_symbol_lookup(self, isin: str) -> List[Dict[str, Any]]:
        try:
            info = yf.Ticker(isin).info or {}
        except Exception:
            return []
        symbol = info.get("symbol")
        return [{"symbol": symbol, "quote": {"symbol": symbol, "isin": info.get("isin")}}] if symbol else []

    def _pick_best_symbol(self, isin: str, candidates: List[Dict[str, Any]]) -> str:
        best_score = -1
        best_symbol: str | None = None
        for candidate in candidates:
            symbol = candidate.get("symbol")
            if not symbol:
                continue
            quote = candidate.get("quote", {}) if isinstance(candidate.get("quote"), dict) else {}
            score = 100 if str(quote.get("isin") or "").upper() == isin else 0
            quote_type = str(quote.get("quoteType") or "").upper()
            if quote_type in {"EQUITY", "ETF", "MUTUALFUND"}:
                score += 10
            if quote.get("exchange") or quote.get("exchDisp"):
                score += 1
            if score > best_score:
                best_score = score
                best_symbol = symbol
        if not best_symbol:
            raise LookupError(f"Kein nutzbares Yahoo-Symbol für ISIN {isin} gefunden")
        return best_symbol

    def _ticker_for_isin(self, isin: str, symbol: str | None = None) -> tuple[Any, str, Dict[str, Any]]:
        resolved_symbol = symbol or self.resolve_symbol(isin)
        if resolved_symbol in self._ticker_bundle_cache:
            ticker, info = self._ticker_bundle_cache[resolved_symbol]
            return ticker, resolved_symbol, info

        ticker = yf.Ticker(resolved_symbol)
        info = self.instrument_client.get_info(ticker)
        self._ticker_bundle_cache[resolved_symbol] = (ticker, info)
        return ticker, resolved_symbol, info

    def fetch_instrument(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        ticker, resolved_symbol, info = self._ticker_for_isin(isin, symbol)
        return self.instrument_client.fetch_instrument(isin, resolved_symbol, info)

    def fetch_market(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        ticker, _, info = self._ticker_for_isin(isin, symbol)
        return self.market_client.fetch_market(info, ticker)

    def fetch_profile(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        _, _, info = self._ticker_for_isin(isin, symbol)
        return self.instrument_client.fetch_profile(info)

    def fetch_financial_statements(self, isin: str, period: str = "annual", symbol: str | None = None) -> Dict[str, Any]:
        ticker, _, _ = self._ticker_for_isin(isin, symbol)
        all_statements = self.financials_client.fetch_financials(ticker)
        period_key = "quarterly" if period == "quarterly" else "annual"
        return {
            "income_statement": {"annual": all_statements["income_statement"]["annual"], "quarterly": all_statements["income_statement"]["quarterly"]},
            "balance_sheet": {"annual": all_statements["balance_sheet"]["annual"], "quarterly": all_statements["balance_sheet"]["quarterly"]},
            "cash_flow": {"annual": all_statements["cash_flow"]["annual"], "quarterly": all_statements["cash_flow"]["quarterly"]},
            "period": period_key,
        }

    def fetch_fundamentals(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        _, _, info = self._ticker_for_isin(isin, symbol)
        return self.financials_client.fetch_fundamentals(info)

    def fetch_analysts(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        ticker, _, info = self._ticker_for_isin(isin, symbol)
        try:
            return self.analyst_client.fetch_analysts(ticker, info)
        except Exception:
            logger.warning("[YFinance] optionale Analystendaten für %s (%s) nicht verfügbar", isin, symbol, exc_info=True)
            return {}

    def fetch_fund(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        ticker, _, info = self._ticker_for_isin(isin, symbol)
        quote_type = str(info.get("quoteType") or "").upper()
        if not self.fund_client.is_fund_like_quote_type(quote_type):
            return {}
        try:
            return self.fund_client.fetch_fund(ticker, info)
        except Exception:
            logger.info("[YFinance] optionale Funddaten für %s (%s) nicht verfügbar", isin, symbol, exc_info=True)
            return {}

    def fetch_timeseries(self, isin: str, symbol: str | None = None, start_date: str | None = None) -> Dict[str, Any]:
        ticker, _, _ = self._ticker_for_isin(isin, symbol)
        return self.market_client.fetch_timeseries(ticker, start_date=start_date)

    def fetch_benchmark_timeseries(self, symbol: str, start_date: str | None = None) -> List[Dict[str, Any]]:
        return self.market_client.fetch_benchmark_price_history(symbol, start_date=start_date)

    def fetch_etf_data(self, isin: str, etf_key: str) -> List[Dict[str, Any]]:
        market = self.fetch_market(isin)
        ts = self.fetch_timeseries(isin)
        keys = ["marketCap", "averageVolume", "freeFloat", "currentPrice"]
        current = {"date": datetime.date.today().isoformat()}
        for key in keys:
            current[key] = market.get(key)
        return [current] + [{"date": r.get("date"), **{k: r.get(k) for k in keys}} for r in ts.get("metrics_history", [])]
