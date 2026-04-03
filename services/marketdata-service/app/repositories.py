from __future__ import annotations

from datetime import UTC, datetime

from pymongo import ASCENDING
from pymongo.collection import Collection

from app.models import CachedInstrumentProfile, InstrumentProfile, utcnow


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

        profile_payload = document.get("profile")
        if not isinstance(profile_payload, dict):
            return None

        return CachedInstrumentProfile(
            profile=InstrumentProfile.model_validate(profile_payload),
            fetched_at=fetched_at,
        )

    def upsert(self, symbol: str, profile: InstrumentProfile) -> datetime:
        fetched_at = utcnow()
        self._collection.update_one(
            {"symbol": symbol},
            {
                "$set": {
                    "symbol": symbol,
                    "profile": profile.model_dump(mode="json", exclude_none=True),
                    "fetched_at": fetched_at,
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

    def upsert(self, symbol: str, profile: InstrumentProfile) -> datetime:
        fetched_at = utcnow()
        self._data[symbol] = CachedInstrumentProfile(profile=profile, fetched_at=fetched_at)
        return fetched_at
