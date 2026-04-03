from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pymongo import ASCENDING
from pymongo.collection import Collection

from app.models import CachedInstrumentProfile, utcnow


class InstrumentProfileCacheRepository:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection
        self._collection.create_index([("symbol", ASCENDING)], unique=True)

    def get(self, symbol: str) -> CachedInstrumentProfile | None:
        document = self._collection.find_one({"symbol": symbol})
        if document is None:
            return None

        fetched_at = document.get("fetched_at")
        if not isinstance(fetched_at, datetime):
            return None
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=UTC)

        payload = document.get("payload")
        if not isinstance(payload, dict):
            return None

        return CachedInstrumentProfile(
            payload=payload,
            fetched_at=fetched_at,
        )

    def upsert(self, symbol: str, payload: dict[str, Any], source: str = "fmp_profile_v1") -> datetime:
        fetched_at = utcnow()
        self._collection.update_one(
            {"symbol": symbol},
            {
                "$set": {
                    "symbol": symbol,
                    "payload": payload,
                    "fetched_at": fetched_at,
                    "source": source,
                }
            },
            upsert=True,
        )
        return fetched_at


class InMemoryInstrumentProfileCacheRepository:
    def __init__(self) -> None:
        self._data: dict[str, CachedInstrumentProfile] = {}

    def get(self, symbol: str) -> CachedInstrumentProfile | None:
        return self._data.get(symbol)

    def upsert(self, symbol: str, payload: dict[str, Any], source: str = "fmp_profile_v1") -> datetime:
        fetched_at = utcnow()
        self._data[symbol] = CachedInstrumentProfile(payload=payload, fetched_at=fetched_at)
        return fetched_at
