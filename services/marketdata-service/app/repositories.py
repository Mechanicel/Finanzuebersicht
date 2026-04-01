from __future__ import annotations

from datetime import UTC, datetime

from pymongo import ASCENDING
from pymongo.collection import Collection

from app.models import InstrumentSelectionDetailsResponse


def _drop_none(value: object) -> object:
    if isinstance(value, dict):
        return {key: _drop_none(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [_drop_none(item) for item in value]
    return value


class InstrumentSelectionCacheRepository:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection
        self._initialize()

    def get(self, symbol: str, identity_source: str) -> tuple[InstrumentSelectionDetailsResponse, datetime] | None:
        document = self._collection.find_one({"symbol": symbol, "identity_source": identity_source})
        if document is None:
            return None

        payload = InstrumentSelectionDetailsResponse.model_validate(document["payload"])
        fetched_at = document["fetched_at"]
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=UTC)
        return payload, fetched_at

    def upsert(self, symbol: str, payload: InstrumentSelectionDetailsResponse, identity_source: str) -> datetime:
        fetched_at = datetime.now(UTC)
        self._collection.update_one(
            {"symbol": symbol, "identity_source": identity_source},
            {
                "$set": {
                    "symbol": symbol,
                    "identity_source": identity_source,
                    "payload": payload.model_dump(mode="json", exclude_none=True),
                    "fetched_at": fetched_at,
                }
            },
            upsert=True,
        )
        return fetched_at

    def _initialize(self) -> None:
        self._collection.create_index([("symbol", ASCENDING), ("identity_source", ASCENDING)], unique=True)


class InstrumentHydratedRepository:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection
        self._initialize()

    def upsert(self, symbol: str, payload: dict[str, object]) -> datetime:
        hydrated_at = datetime.now(UTC)
        payload_without_none = _drop_none(payload)
        if not isinstance(payload_without_none, dict):
            payload_without_none = {}
        self._collection.update_one(
            {"symbol": symbol},
            {
                "$set": {
                    "symbol": symbol,
                    **payload_without_none,
                    "hydrated_at": hydrated_at,
                }
            },
            upsert=True,
        )
        return hydrated_at

    def get_hydrated_at(self, symbol: str) -> datetime | None:
        document = self._collection.find_one({"symbol": symbol}, {"hydrated_at": 1})
        if document is None:
            return None

        hydrated_at = document.get("hydrated_at")
        if not isinstance(hydrated_at, datetime):
            return None
        if hydrated_at.tzinfo is None:
            hydrated_at = hydrated_at.replace(tzinfo=UTC)
        return hydrated_at

    def _initialize(self) -> None:
        self._collection.create_index([("symbol", ASCENDING)], unique=True)
