from __future__ import annotations

from datetime import UTC, datetime

from pymongo import ASCENDING
from pymongo.collection import Collection

from app.models import CachedInstrumentProfile, InstrumentProfile, PersistenceOnlyInstrumentProfile, utcnow


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

        visible_profile = document.get("visible_profile")
        persistence_only_profile = document.get("persistence_only_profile")
        source = document.get("source")
        if not isinstance(visible_profile, dict) or not isinstance(persistence_only_profile, dict) or not isinstance(source, str):
            return None

        return CachedInstrumentProfile(
            symbol=symbol,
            source=source,
            visible_profile=InstrumentProfile.model_validate(visible_profile),
            persistence_only_profile=PersistenceOnlyInstrumentProfile.model_validate(persistence_only_profile),
            fetched_at=fetched_at,
        )

    def upsert(
        self,
        symbol: str,
        *,
        visible_profile: dict,
        persistence_only_profile: dict,
        source: str = "fmp_profile_v2",
    ) -> datetime:
        fetched_at = utcnow()
        self._collection.update_one(
            {"symbol": symbol},
            {
                "$set": {
                    "symbol": symbol,
                    "visible_profile": visible_profile,
                    "persistence_only_profile": persistence_only_profile,
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

    def upsert(
        self,
        symbol: str,
        *,
        visible_profile: dict,
        persistence_only_profile: dict,
        source: str = "fmp_profile_v2",
    ) -> datetime:
        fetched_at = utcnow()
        self._data[symbol] = CachedInstrumentProfile(
            symbol=symbol,
            source=source,
            visible_profile=InstrumentProfile.model_validate(visible_profile),
            persistence_only_profile=PersistenceOnlyInstrumentProfile.model_validate(persistence_only_profile),
            fetched_at=fetched_at,
        )
        return fetched_at
