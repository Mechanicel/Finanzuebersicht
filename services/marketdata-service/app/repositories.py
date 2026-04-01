from __future__ import annotations

from datetime import UTC, datetime

from pymongo import ASCENDING
from pymongo.collection import Collection

from app.models import InstrumentIdentity, InstrumentSelectionDetailsResponse


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
                    "payload": payload.model_dump(mode="json", exclude_none=True),
                    "fetched_at": fetched_at,
                }
            },
            upsert=True,
        )
        return fetched_at

    def _initialize(self) -> None:
        self._collection.create_index([("symbol", ASCENDING)], unique=True)


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

    def _initialize(self) -> None:
        self._collection.create_index([("symbol", ASCENDING)], unique=True)


class SecurityIdentityRepository:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection
        self._initialize()

    def get(self, symbol: str, exchange: str | None) -> InstrumentIdentity | None:
        normalized_symbol = self._normalize_symbol(symbol)
        normalized_exchange = self._normalize_exchange(exchange)
        document = self._collection.find_one(self._lookup_filter(normalized_symbol, normalized_exchange))
        if document is None:
            return None

        return InstrumentIdentity.model_validate(document)

    def find_by_symbol(self, symbol: str) -> list[InstrumentIdentity]:
        normalized_symbol = self._normalize_symbol(symbol)
        documents = self._collection.find({"symbol": normalized_symbol})
        return [InstrumentIdentity.model_validate(document) for document in documents]

    def upsert(self, identity: InstrumentIdentity) -> datetime:
        normalized_identity = self._normalize_identity(identity)
        resolved_at = datetime.now(UTC)
        payload = normalized_identity.model_dump(mode="json", exclude_none=True)
        payload = _drop_none(payload)
        if not isinstance(payload, dict):
            payload = {}
        payload["resolved_at"] = resolved_at
        self._collection.update_one(
            self._lookup_filter(normalized_identity.symbol, normalized_identity.exchange),
            {"$set": payload},
            upsert=True,
        )
        return resolved_at

    def _initialize(self) -> None:
        self._collection.create_index([("symbol", ASCENDING), ("exchange", ASCENDING)], unique=True)
        self._collection.create_index([("isin", ASCENDING)], sparse=True)

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        return symbol.strip().upper()

    @staticmethod
    def _normalize_exchange(exchange: str | None) -> str | None:
        if exchange is None:
            return None
        normalized = exchange.strip().upper()
        return normalized or None

    @staticmethod
    def _normalize_identifier(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        return normalized or None

    @classmethod
    def _normalize_identity(cls, identity: InstrumentIdentity) -> InstrumentIdentity:
        return identity.model_copy(
            update={
                "symbol": cls._normalize_symbol(identity.symbol),
                "exchange": cls._normalize_exchange(identity.exchange),
                "isin": cls._normalize_identifier(identity.isin),
                "figi": cls._normalize_identifier(identity.figi),
                "wkn": cls._normalize_identifier(identity.wkn),
            }
        )

    @staticmethod
    def _lookup_filter(symbol: str, exchange: str | None) -> dict[str, object]:
        if exchange is None:
            return {
                "symbol": symbol,
                "$or": [{"exchange": None}, {"exchange": {"$exists": False}}],
            }
        return {"symbol": symbol, "exchange": exchange}
