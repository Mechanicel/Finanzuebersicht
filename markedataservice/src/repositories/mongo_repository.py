from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient

from finanzuebersicht_shared import get_settings

logger = logging.getLogger(__name__)


class MongoMarketDataRepository:
    """MongoDB-basierter Cache für StockModel-Dokumente des markedataservice."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=3000)
        self.collection = self.client[settings.mongo_db_name][settings.mongo_marketdata_collection]
        self.collection.create_index("isin", unique=True)
        self.collection.create_index("aliases.symbols")

    @staticmethod
    def _clean(doc: dict[str, Any] | None) -> dict[str, Any] | None:
        if not doc:
            return None
        out = dict(doc)
        out.pop("_id", None)
        out.pop("updated_at", None)
        return out

    def read(self, isin: str) -> dict[str, Any] | None:
        doc = self.collection.find_one({"isin": isin})
        return self._clean(doc)

    def write(self, isin: str, data: dict[str, Any]) -> None:
        payload = dict(data)
        payload["isin"] = isin
        payload["updated_at"] = datetime.now(timezone.utc)
        self.collection.replace_one({"isin": isin}, payload, upsert=True)

    def read_by_symbol(self, symbol: str) -> dict[str, Any] | None:
        normalized_symbol = (symbol or "").strip().upper()
        if not normalized_symbol:
            return None
        doc = self.collection.find_one({"aliases.symbols": normalized_symbol})
        return self._clean(doc)

    def upsert_timeseries_for_isin(self, isin: str, payload: dict[str, Any], *, instrument: dict[str, Any] | None = None) -> None:
        now = datetime.now(timezone.utc)
        normalized_symbol = str(payload.get("symbol") or "").strip().upper()
        update_set: dict[str, Any] = {
            "isin": isin,
            "timeseries.price_history": list(payload.get("price_history") or []),
            "price_history": list(payload.get("price_history") or []),
            "timeseries.metrics_history": list(payload.get("metrics_history") or []),
            "metrics_history": list(payload.get("metrics_history") or []),
            "meta.timeseries": {
                "as_of": payload.get("as_of"),
                "updated_at": payload.get("updated_at"),
                "source": payload.get("source"),
                "last_refresh_at": payload.get("last_refresh_at"),
                "record_count": payload.get("record_count"),
            },
            "meta.last_timeseries_refresh": payload.get("last_refresh_at"),
            "updated_at": now,
        }
        if instrument:
            update_set["instrument"] = {
                "isin": instrument.get("isin") or isin,
                "symbol": instrument.get("symbol") or normalized_symbol,
                "short_name": instrument.get("short_name") or instrument.get("name"),
                "long_name": instrument.get("long_name") or instrument.get("name"),
                "quote_type": instrument.get("quote_type"),
                "exchange": instrument.get("exchange"),
                "currency": instrument.get("currency"),
            }
        update_op: dict[str, Any] = {"$set": update_set}
        if normalized_symbol:
            update_op["$addToSet"] = {"aliases.symbols": normalized_symbol}
            update_set["aliases.primary_symbol"] = normalized_symbol
        self.collection.update_one({"isin": isin}, update_op, upsert=True)

    def ping(self) -> None:
        self.client.admin.command("ping")

    @staticmethod
    def _symbol_cache_key(symbol: str) -> str:
        return f"__SYMBOL_TIMESERIES__{(symbol or '').strip().upper()}"

    def read_symbol_timeseries(self, symbol: str) -> dict[str, Any] | None:
        symbol_doc = self.read_by_symbol(symbol)
        if symbol_doc:
            timeseries = symbol_doc.get("timeseries") or {}
            meta_timeseries = (symbol_doc.get("meta") or {}).get("timeseries") or {}
            payload = {
                "isin": symbol_doc.get("isin"),
                "symbol": (symbol_doc.get("instrument") or {}).get("symbol") or (symbol_doc.get("aliases") or {}).get("primary_symbol") or (symbol or "").strip().upper(),
                "price_history": list(timeseries.get("price_history") or symbol_doc.get("price_history") or []),
                "metrics_history": list(timeseries.get("metrics_history") or symbol_doc.get("metrics_history") or []),
                "as_of": meta_timeseries.get("as_of"),
                "updated_at": meta_timeseries.get("updated_at"),
                "source": meta_timeseries.get("source"),
                "last_refresh_at": meta_timeseries.get("last_refresh_at"),
                "record_count": meta_timeseries.get("record_count"),
            }
            if payload["price_history"]:
                return payload

        cache_key = self._symbol_cache_key(symbol)
        doc = self.collection.find_one({"isin": cache_key})
        cleaned = self._clean(doc)
        if not cleaned:
            return None
        payload = cleaned.get("timeseries_cache")
        return payload if isinstance(payload, dict) else None

    def write_symbol_timeseries(self, symbol: str, payload: dict[str, Any], *, isin: str | None = None, instrument: dict[str, Any] | None = None) -> None:
        normalized_isin = (isin or payload.get("isin") or "").strip().upper()
        if normalized_isin:
            self.upsert_timeseries_for_isin(normalized_isin, payload, instrument=instrument)
            return

        cache_key = self._symbol_cache_key(symbol)
        now = datetime.now(timezone.utc)
        document = {
            "isin": cache_key,
            "timeseries_cache": {
                **payload,
                "symbol": (symbol or "").strip().upper(),
                "updated_at": now.replace(microsecond=0).isoformat(),
            },
            "updated_at": now,
        }
        self.collection.replace_one({"isin": cache_key}, document, upsert=True)
