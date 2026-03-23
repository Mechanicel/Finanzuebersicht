import datetime
from typing import Any, Dict, List

import yfinance as yf

from src.repositories.providers.base_provider import BaseProvider, logger


class YFinanceProvider(BaseProvider):
    """Provider-Implementierung, die Daten über yfinance bezieht."""

    def __init__(self) -> None:
        self._symbol_cache: dict[str, str] = {}

    def resolve_symbol(self, isin: str) -> str:
        normalized_isin = (isin or "").strip().upper()
        if not normalized_isin:
            raise ValueError("ISIN darf nicht leer sein")

        cached_symbol = self._symbol_cache.get(normalized_isin)
        if cached_symbol:
            logger.debug("[YFinance] Symbol-Cache-Hit für %s -> %s", normalized_isin, cached_symbol)
            return cached_symbol

        symbols = self._search_symbols(normalized_isin)
        if not symbols:
            symbols = self._fallback_symbol_lookup(normalized_isin)

        if not symbols:
            raise LookupError(f"Kein Yahoo-Symbol für ISIN {normalized_isin} gefunden")

        best_symbol = self._pick_best_symbol(normalized_isin, symbols)
        self._symbol_cache[normalized_isin] = best_symbol
        logger.info("[YFinance] ISIN %s auf Symbol %s aufgelöst", normalized_isin, best_symbol)
        return best_symbol

    def _search_symbols(self, isin: str) -> List[Dict[str, Any]]:
        try:
            search = yf.Search(
                query=isin,
                max_results=12,
                news_count=0,
                lists_count=0,
                include_cb=False,
                enable_fuzzy_query=False,
                raise_errors=False,
            )
        except Exception as exc:
            logger.warning("[YFinance] Search fehlgeschlagen für %s: %s", isin, exc)
            return []

        quotes = [quote for quote in getattr(search, "quotes", []) if isinstance(quote, dict)]
        logger.debug("[YFinance] Search lieferte %d Quote-Kandidaten für %s", len(quotes), isin)
        candidates: List[Dict[str, Any]] = []
        for quote in quotes:
            symbol = quote.get("symbol")
            if not symbol:
                continue
            candidates.append({"symbol": symbol, "quote": quote})
        return candidates

    def _fallback_symbol_lookup(self, isin: str) -> List[Dict[str, Any]]:
        logger.debug("[YFinance] Starte Fallback-Symbolauflösung über yf.Ticker für %s", isin)
        try:
            info = yf.Ticker(isin).info or {}
        except Exception as exc:
            logger.warning("[YFinance] Fallback via yf.Ticker(%s) fehlgeschlagen: %s", isin, exc)
            return []
        symbol = info.get("symbol")
        if not symbol:
            return []
        return [{"symbol": symbol, "quote": {"symbol": symbol, "isin": info.get("isin")}}]

    def _pick_best_symbol(self, isin: str, candidates: List[Dict[str, Any]]) -> str:
        best_score = -1
        best_symbol: str | None = None

        for candidate in candidates:
            symbol = candidate.get("symbol")
            if not symbol:
                continue

            quote = candidate.get("quote", {}) if isinstance(candidate.get("quote"), dict) else {}
            quote_isin = str(quote.get("isin") or "").upper()
            score = 0
            if quote_isin == isin:
                score += 100

            verified_isin = ""
            try:
                info = yf.Ticker(symbol).info or {}
                verified_isin = str(info.get("isin") or "").upper()
                if verified_isin == isin:
                    score += 100
            except Exception as exc:
                logger.debug("[YFinance] Verifikation für Symbol %s fehlgeschlagen: %s", symbol, exc)

            quote_type = str(quote.get("quoteType") or "").upper()
            if quote_type in {"EQUITY", "ETF", "MUTUALFUND"}:
                score += 10
            if quote.get("exchange") or quote.get("exchDisp"):
                score += 1

            logger.debug(
                "[YFinance] Kandidat für %s: symbol=%s score=%s quote_isin=%s verified_isin=%s",
                isin,
                symbol,
                score,
                quote_isin,
                verified_isin,
            )
            if score > best_score:
                best_score = score
                best_symbol = symbol

        if not best_symbol:
            raise LookupError(f"Kein nutzbares Yahoo-Symbol für ISIN {isin} gefunden")

        logger.info("[YFinance] Gewählter Kandidat für %s: %s (score=%s)", isin, best_symbol, best_score)
        return best_symbol

    def _ticker_for_isin(self, isin: str, symbol: str | None = None) -> tuple[Any, str]:
        resolved_symbol = symbol or self.resolve_symbol(isin)
        return yf.Ticker(resolved_symbol), resolved_symbol

    def fetch_basic(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        logger.debug("[YFinance] Fetch basic for %s", isin)
        ticker, resolved_symbol = self._ticker_for_isin(isin, symbol)
        info = ticker.info or {}
        basic = {
            "symbol": info.get("symbol") or resolved_symbol,
            "shortName": info.get("shortName"),
            "longName": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "exchange": info.get("exchange"),
            "isin": info.get("isin") or isin,
        }
        logger.debug("[YFinance] Basic data: %s", basic)
        return basic

    def fetch_metrics(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        logger.debug("[YFinance] Fetch metrics for %s", isin)
        ticker, _ = self._ticker_for_isin(isin, symbol)
        info = ticker.info or {}

        free_float: Any = None
        try:
            fast = getattr(ticker, "fast_info", None)
            if fast and hasattr(fast, "free_float"):
                free_float = fast.free_float
                logger.debug("[YFinance] Using fast_info.free_float=%s", free_float)
        except Exception:
            logger.debug("[YFinance] fast_info.free_float nicht verfügbar", exc_info=True)

        if free_float is None:
            float_pct = info.get("floatPercent")
            if float_pct is not None:
                try:
                    free_float = float_pct / 100.0
                    logger.debug("[YFinance] Using info.floatPercent=%s", float_pct)
                except Exception:
                    free_float = None
        if free_float is None:
            float_shares = info.get("floatShares")
            shares_outstanding = info.get("sharesOutstanding")
            if float_shares and shares_outstanding:
                try:
                    free_float = float_shares / shares_outstanding
                    logger.debug("[YFinance] Calculated free_float from floatShares/sharesOutstanding: %s", free_float)
                except Exception:
                    free_float = None
        if free_float is None:
            float_mc = info.get("floatMarketCap")
            market_cap = info.get("marketCap")
            if float_mc and market_cap:
                try:
                    free_float = float_mc / market_cap
                    logger.debug("[YFinance] Calculated free_float from floatMarketCap/marketCap: %s", free_float)
                except Exception:
                    free_float = None

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
        logger.debug("[YFinance] Metrics data: %s", metrics)
        return metrics

    def fetch_metrics_history(self, isin: str, symbol: str | None = None) -> List[Dict[str, Any]]:
        logger.debug("[YFinance] Fetch metrics history for %s", isin)
        ticker, _ = self._ticker_for_isin(isin, symbol)
        hist = ticker.history(period="24mo", interval="1mo", actions=True)
        history: List[Dict[str, Any]] = []
        for dt, row in hist.iterrows():
            history.append(
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
        logger.debug("[YFinance] Loaded %d historical metric entries", len(history))
        return history

    def fetch_price_history(self, isin: str, symbol: str | None = None) -> List[Dict[str, Any]]:
        logger.debug("[YFinance] Fetch daily price history for %s", isin)
        ticker, _ = self._ticker_for_isin(isin, symbol)
        hist = ticker.history(period="10y", interval="1d", auto_adjust=False, actions=False)
        history: List[Dict[str, Any]] = []
        for dt, row in hist.iterrows():
            close = row.get("Close")
            if close is None:
                continue
            history.append({"date": dt.date().isoformat(), "close": float(close)})
        logger.debug("[YFinance] Loaded %d daily prices", len(history))
        return history

    def fetch_etf_data(self, isin: str, etf_key: str) -> List[Dict[str, Any]]:
        logger.debug("[YFinance:ETF] Fetch ETF data for %s, ETF=%s", isin, etf_key)
        return super().fetch_etf_data(isin, etf_key)

    def _build_etf_entries(self, isin: str, keys: List[str], etf_name: str) -> List[Dict[str, Any]]:
        logger.debug("[YFinance:ETF:%s] Lade Daten für ISIN=%s", etf_name, isin)
        raw_metrics = self.fetch_metrics(isin)
        raw_history = self.fetch_metrics_history(isin)

        entries: List[Dict[str, Any]] = []
        current = {"date": datetime.date.today().isoformat()}
        for key in keys:
            current[key] = raw_metrics.get(key)
        entries.append(current)
        logger.debug("[YFinance:ETF:%s] Aktuelle Kennzahlen: %s", etf_name, current)

        for rec in raw_history:
            entry = {"date": rec.get("date")}
            for key in keys:
                entry[key] = rec.get(key)
            entries.append(entry)
        logger.debug("[YFinance:ETF:%s] Insgesamt %d Einträge", etf_name, len(entries))
        return entries
