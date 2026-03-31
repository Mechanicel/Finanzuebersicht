from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.models import InstrumentSelectionDetailsResponse


class InstrumentSelectionCacheRepository:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._initialize()

    def get(self, symbol: str) -> tuple[InstrumentSelectionDetailsResponse, datetime] | None:
        with sqlite3.connect(self._db_path) as connection:
            row = connection.execute(
                "SELECT payload_json, fetched_at FROM instrument_selection_cache WHERE symbol = ?",
                (symbol,),
            ).fetchone()

        if row is None:
            return None

        payload = InstrumentSelectionDetailsResponse.model_validate(json.loads(row[0]))
        fetched_at = datetime.fromisoformat(row[1])
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=UTC)
        return payload, fetched_at

    def upsert(self, symbol: str, payload: InstrumentSelectionDetailsResponse) -> datetime:
        fetched_at = datetime.now(UTC)
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                INSERT INTO instrument_selection_cache (symbol, payload_json, fetched_at)
                VALUES (?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    fetched_at = excluded.fetched_at
                """,
                (symbol, payload.model_dump_json(), fetched_at.isoformat()),
            )
            connection.commit()
        return fetched_at

    def _initialize(self) -> None:
        db = Path(self._db_path)
        db.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS instrument_selection_cache (
                    symbol TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    fetched_at TEXT NOT NULL
                )
                """
            )
            connection.commit()
