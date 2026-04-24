from __future__ import annotations

from datetime import UTC, datetime

from pymongo import ASCENDING
from pymongo.collection import Collection

from app.models import (
    CachedInstrumentProfile,
    CurrentPriceCacheDocument,
    EtfData,
    EtfDataCacheDocument,
    FinancialStatements,
    FinancialsCacheDocument,
    FinancialsPeriod,
    InstrumentProfile,
    InstrumentType,
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

    def is_delisted(self, symbol: str) -> bool:
        doc = self._collection.find_one({"symbol": symbol}, {"delisted": 1})
        return bool(doc and doc.get("delisted", False))

    def increment_failure_count(self, symbol: str, threshold: int = 3) -> tuple[int, bool]:
        self._collection.update_one({"symbol": symbol}, {"$inc": {"consecutive_failures": 1}}, upsert=True)
        doc = self._collection.find_one({"symbol": symbol}, {"consecutive_failures": 1, "delisted": 1})
        new_count = int(doc.get("consecutive_failures", 1)) if doc else 1
        already_delisted = bool(doc and doc.get("delisted", False))
        if not already_delisted and new_count >= threshold:
            self._collection.update_one({"symbol": symbol}, {"$set": {"delisted": True}})
            return new_count, True
        return new_count, already_delisted

    def reset_failure_count(self, symbol: str) -> None:
        self._collection.update_one({"symbol": symbol}, {"$set": {"consecutive_failures": 0, "delisted": False}})


class InMemoryInstrumentProfileCacheRepository:
    def __init__(self) -> None:
        self._data: dict[str, CachedInstrumentProfile] = {}
        self._failure_counts: dict[str, int] = {}
        self._delisted: set[str] = set()

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

    def is_delisted(self, symbol: str) -> bool:
        return symbol in self._delisted

    def increment_failure_count(self, symbol: str, threshold: int = 3) -> tuple[int, bool]:
        self._failure_counts[symbol] = self._failure_counts.get(symbol, 0) + 1
        new_count = self._failure_counts[symbol]
        if new_count >= threshold:
            self._delisted.add(symbol)
        return new_count, symbol in self._delisted

    def reset_failure_count(self, symbol: str) -> None:
        self._failure_counts.pop(symbol, None)
        self._delisted.discard(symbol)


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

    def get_latest(self, symbol: str) -> CurrentPriceCacheDocument | None:
        document = self._collection.find_one({"symbol": symbol}, sort=[("trade_date", -1)])
        if document is None:
            return None
        return self._to_document(document)

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

    def get_latest(self, symbol: str) -> CurrentPriceCacheDocument | None:
        matching = [doc for (stored_symbol, _), doc in self._data.items() if stored_symbol == symbol]
        if not matching:
            return None
        return max(matching, key=lambda item: item.trade_date)


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


class FinancialsCacheRepository:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection
        self._collection.create_index([("symbol", ASCENDING), ("period", ASCENDING)], unique=True)

    def get(self, symbol: str, period: FinancialsPeriod) -> FinancialsCacheDocument | None:
        document = self._collection.find_one({"symbol": symbol, "period": period})
        if document is None:
            return None
        return self._to_document(document)

    def upsert_document(self, document: FinancialsCacheDocument) -> FinancialsCacheDocument:
        self._collection.update_one(
            {"symbol": document.symbol, "period": document.period},
            {"$set": document.model_dump()},
            upsert=True,
        )
        return document

    @staticmethod
    def _to_document(document: dict) -> FinancialsCacheDocument | None:
        fetched_at = document.get("fetched_at")
        if not isinstance(fetched_at, datetime):
            return None
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=UTC)
        try:
            return FinancialsCacheDocument(
                symbol=str(document["symbol"]),
                period=document["period"],
                source=str(document["source"]),
                currency=document.get("currency"),
                statements=FinancialStatements.model_validate(document.get("statements", {})),
                fetched_at=fetched_at,
            )
        except (KeyError, TypeError, ValueError):
            return None


class InMemoryFinancialsCacheRepository:
    def __init__(self) -> None:
        self._data: dict[tuple[str, FinancialsPeriod], FinancialsCacheDocument] = {}

    def get(self, symbol: str, period: FinancialsPeriod) -> FinancialsCacheDocument | None:
        return self._data.get((symbol, period))

    def upsert_document(self, document: FinancialsCacheDocument) -> FinancialsCacheDocument:
        self._data[(document.symbol, document.period)] = document
        return document


class EtfDataCacheRepository:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection
        self._collection.create_index([("symbol", ASCENDING)], unique=True)

    def get(self, symbol: str) -> EtfDataCacheDocument | None:
        document = self._collection.find_one({"symbol": symbol})
        if document is None:
            return None
        return self._to_document(document)

    def upsert_document(self, document: EtfDataCacheDocument) -> None:
        self._collection.update_one(
            {"symbol": document.symbol},
            {"$set": document.model_dump()},
            upsert=True,
        )

    @staticmethod
    def _to_document(document: dict) -> EtfDataCacheDocument | None:
        fetched_at = document.get("fetched_at")
        if not isinstance(fetched_at, datetime):
            return None
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=UTC)
        try:
            return EtfDataCacheDocument(
                symbol=str(document["symbol"]),
                instrument_type=document.get("instrument_type", "ETF"),
                etf_data=EtfData.model_validate(document.get("etf_data", {})),
                fetched_at=fetched_at,
            )
        except (KeyError, TypeError, ValueError):
            return None


class InMemoryEtfDataCacheRepository:
    def __init__(self) -> None:
        self._data: dict[str, EtfDataCacheDocument] = {}

    def get(self, symbol: str) -> EtfDataCacheDocument | None:
        return self._data.get(symbol)

    def upsert_document(self, document: EtfDataCacheDocument) -> None:
        self._data[document.symbol] = document
