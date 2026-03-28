from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class BaseProvider:
    """Abstrakte Provider-Schnittstelle für Analyseblöcke."""

    provider_name = "base"

    def resolve_symbol(self, isin: str) -> str:
        raise NotImplementedError

    def fetch_instrument(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    def fetch_market(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    def fetch_profile(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    def fetch_financial_statements(self, isin: str, period: str = "annual", symbol: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    def fetch_fundamentals(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    def fetch_analysts(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    def fetch_fund(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    def fetch_timeseries(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    def fetch_benchmark_timeseries(self, symbol: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def search_quotes(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        raise NotImplementedError

    # Legacy-Adapter
    def fetch_basic(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        instrument = self.fetch_instrument(isin, symbol=symbol)
        profile = self.fetch_profile(isin, symbol=symbol)
        return {
            "symbol": instrument.get("symbol"),
            "shortName": instrument.get("short_name"),
            "longName": instrument.get("long_name"),
            "sector": profile.get("sector"),
            "industry": profile.get("industry"),
            "country": profile.get("country"),
            "exchange": instrument.get("exchange"),
            "isin": instrument.get("isin") or isin,
            "currency": instrument.get("currency"),
        }

    def fetch_metrics(self, isin: str, symbol: str | None = None) -> Dict[str, Any]:
        market = self.fetch_market(isin, symbol=symbol)
        fundamentals = self.fetch_fundamentals(isin, symbol=symbol)
        merged = {}
        merged.update(market)
        merged.update((fundamentals or {}).get("valuation") or {})
        merged.update((fundamentals or {}).get("quality") or {})
        merged.update((fundamentals or {}).get("growth") or {})
        return merged

    def fetch_metrics_history(self, isin: str, symbol: str | None = None) -> List[Dict[str, Any]]:
        ts = self.fetch_timeseries(isin, symbol=symbol)
        return list(ts.get("metrics_history") or [])

    def fetch_price_history(self, isin: str, symbol: str | None = None) -> List[Dict[str, Any]]:
        ts = self.fetch_timeseries(isin, symbol=symbol)
        return list(ts.get("price_history") or [])

    def fetch_etf_data(self, isin: str, etf_key: str) -> List[Dict[str, Any]]:
        logger.error("Unbekannter ETF-Schlüssel: %s", etf_key)
        raise NotImplementedError(f"Unbekannter ETF-Schlüssel: {etf_key}")
