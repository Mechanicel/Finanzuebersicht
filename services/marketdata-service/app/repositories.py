from __future__ import annotations

from datetime import UTC, datetime

from pymongo import ASCENDING
from pymongo.collection import Collection

from app.models import (
    CachedInstrumentProfile,
    CurrentPriceCacheDocument,
    InstrumentProfile,
    PersistenceOnlyInstrumentProfile,
    PriceHistoryCacheDocument,
    PriceHistoryRow,
    utcnow,
)


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


class CurrentPriceCacheRepository:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection
        self._collection.create_index([("symbol", ASCENDING), ("trade_date", ASCENDING)], unique=True)

    def get(self, symbol: str, trade_date: str) -> CurrentPriceCacheDocument | None:
        document = self._collection.find_one({"symbol": symbol, "trade_date": trade_date})
        if document is None:
            return None
        return self._to_document(document)

    def upsert(
        self,
        symbol: str,
        trade_date: str,
        current_price: float,
        *,
        source: str = "yfinance_1d_1m",
    ) -> CurrentPriceCacheDocument:
        fetched_at = utcnow()
        self._collection.update_one(
            {"symbol": symbol, "trade_date": trade_date},
            {
                "$set": {
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "current_price": current_price,
                    "source": source,
                    "fetched_at": fetched_at,
                }
            },
            upsert=True,
        )
        return CurrentPriceCacheDocument(
            symbol=symbol,
            trade_date=trade_date,
            current_price=current_price,
            source="yfinance_1d_1m",
            fetched_at=fetched_at,
        )

    @staticmethod
    def _to_document(document: dict) -> CurrentPriceCacheDocument | None:
        fetched_at = document.get("fetched_at")
        if not isinstance(fetched_at, datetime):
            return None
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=UTC)
        try:
            return CurrentPriceCacheDocument(
                symbol=str(document["symbol"]),
                trade_date=str(document["trade_date"]),
                current_price=float(document["current_price"]),
                source="yfinance_1d_1m",
                fetched_at=fetched_at,
            )
        except (KeyError, TypeError, ValueError):
            return None


class InMemoryCurrentPriceCacheRepository:
    def __init__(self) -> None:
        self._data: dict[tuple[str, str], CurrentPriceCacheDocument] = {}

    def get(self, symbol: str, trade_date: str) -> CurrentPriceCacheDocument | None:
        return self._data.get((symbol, trade_date))

    def upsert(
        self,
        symbol: str,
        trade_date: str,
        current_price: float,
        *,
        source: str = "yfinance_1d_1m",
    ) -> CurrentPriceCacheDocument:
        document = CurrentPriceCacheDocument(
            symbol=symbol,
            trade_date=trade_date,
            current_price=current_price,
            source="yfinance_1d_1m",
            fetched_at=utcnow(),
        )
        self._data[(symbol, trade_date)] = document
        return document


class PriceHistoryCacheRepository:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection
        self._collection.create_index([("symbol", ASCENDING)], unique=True)

    def get(self, symbol: str) -> PriceHistoryCacheDocument | None:
        document = self._collection.find_one({"symbol": symbol})
        if document is None:
            return None
        return self._to_document(document)

    def upsert_document(self, document: PriceHistoryCacheDocument) -> None:
        self._collection.update_one(
            {"symbol": document.symbol},
            {"$set": document.model_dump()},
            upsert=True,
        )

    def enrich_history_rows(self, symbol: str, rows: list[PriceHistoryRow]) -> PriceHistoryCacheDocument | None:
        existing = self.get(symbol)
        if existing is None:
            return None

        existing_by_date = {row.date: row for row in existing.history_rows}
        for row in rows:
            if row.date not in existing_by_date:
                existing.history_rows.append(row)

        existing.history_rows.sort(key=lambda row: row.date)
        if existing.history_rows:
            existing.first_date = existing.history_rows[0].date
            existing.last_date = existing.history_rows[-1].date
        existing.updated_at = utcnow()
        self.upsert_document(existing)
        return existing

    @staticmethod
    def _to_document(document: dict) -> PriceHistoryCacheDocument | None:
        updated_at = document.get("updated_at")
        if not isinstance(updated_at, datetime):
            return None
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=UTC)
        try:
            rows = [PriceHistoryRow.model_validate(row) for row in document.get("history_rows", [])]
            return PriceHistoryCacheDocument(
                symbol=str(document["symbol"]),
                interval="1d",
                period_seeded="max",
                history_rows=rows,
                first_date=str(document["first_date"]),
                last_date=str(document["last_date"]),
                updated_at=updated_at,
            )
        except (KeyError, TypeError, ValueError):
            return None


class InMemoryPriceHistoryCacheRepository:
    def __init__(self) -> None:
        self._data: dict[str, PriceHistoryCacheDocument] = {}

    def get(self, symbol: str) -> PriceHistoryCacheDocument | None:
        return self._data.get(symbol)

    def upsert_document(self, document: PriceHistoryCacheDocument) -> None:
        self._data[document.symbol] = document

    def enrich_history_rows(self, symbol: str, rows: list[PriceHistoryRow]) -> PriceHistoryCacheDocument | None:
        existing = self.get(symbol)
        if existing is None:
            return None

        existing_dates = {row.date for row in existing.history_rows}
        for row in rows:
            if row.date not in existing_dates:
                existing.history_rows.append(row)
                existing_dates.add(row.date)

        existing.history_rows.sort(key=lambda row: row.date)
        if existing.history_rows:
            existing.first_date = existing.history_rows[0].date
            existing.last_date = existing.history_rows[-1].date
        existing.updated_at = utcnow()
        return existing
