from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient

from shared_config import get_settings

logger = logging.getLogger(__name__)


class MongoMarketDataRepository:
    """MongoDB-basierter Cache für StockModel-Dokumente des markedataservice."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=3000)
        self.collection = self.client[settings.mongo_db_name][settings.mongo_marketdata_collection]
        self.collection.create_index("isin", unique=True)

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

    def ping(self) -> None:
        self.client.admin.command("ping")
