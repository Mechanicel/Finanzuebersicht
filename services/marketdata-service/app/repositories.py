from __future__ import annotations

from datetime import UTC, datetime

from pymongo import ASCENDING
from pymongo.collection import Collection

from app.models import InstrumentSelectionDetailsResponse


class InstrumentSelectionCacheRepository:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection
        self._initialize()

    def get(self, symbol: str) -> tuple[InstrumentSelectionDetailsResponse, datetime] | None:
        document = self._collection.find_one({"symbol": symbol})
        if document is None:
            return None

        payload = InstrumentSelectionDetailsResponse.model_validate(document["payload"])
        fetched_at = document["fetched_at"]
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=UTC)
        return payload, fetched_at

    def upsert(self, symbol: str, payload: InstrumentSelectionDetailsResponse) -> datetime:
        fetched_at = datetime.now(UTC)
        self._collection.update_one(
            {"symbol": symbol},
            {
                "$set": {
                    "symbol": symbol,
                    "payload": payload.model_dump(mode="json"),
                    "fetched_at": fetched_at,
                }
            },
            upsert=True,
        )
        return fetched_at

    def _initialize(self) -> None:
        self._collection.create_index([("symbol", ASCENDING)], unique=True)
