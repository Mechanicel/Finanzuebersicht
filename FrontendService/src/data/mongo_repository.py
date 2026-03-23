from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from finanzuebersicht_shared import get_settings

logger = logging.getLogger(__name__)


class MongoRepository:
    """Persistenzschicht für Frontend-Domänendaten in MongoDB."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = MongoClient(self.settings.mongo_uri, serverSelectionTimeoutMS=3000)
        self.db = self.client[self.settings.mongo_db_name]
        self.person_collection = self.db[self.settings.mongo_person_collection]
        self.bank_collection = self.db[self.settings.mongo_bank_collection]
        self.account_type_collection = self.db[self.settings.mongo_account_type_collection]

    def ping(self) -> None:
        self.client.admin.command("ping")

    def ensure_seeded(self) -> None:
        if self.person_collection.estimated_document_count() == 0:
            self._seed_personen()
        if self.bank_collection.estimated_document_count() == 0:
            self._seed_banken()
        if self.account_type_collection.estimated_document_count() == 0:
            self._seed_kontotypen()

    def _read_json_file(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            logger.info("Seed-Datei fehlt: %s", path)
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            logger.warning("Seed-Datei %s enthält kein JSON-Objekt und wird ignoriert", path)
            return {}
        return payload

    def _seed_personen(self) -> None:
        payload = self._read_json_file(self.settings.frontend_seed_personen_file)
        personen = payload.get("personen", [])
        docs = [self._normalize_person(person) for person in personen]
        if docs:
            self.person_collection.insert_many(docs)
            logger.info("Mongo Seed: %d Personen migriert", len(docs))

    def _seed_banken(self) -> None:
        payload = self._read_json_file(self.settings.frontend_seed_banken_file)
        banken = payload.get("Banken", [])
        docs = [self._normalize_bank(bank) for bank in banken]
        if docs:
            self.bank_collection.insert_many(docs)
            logger.info("Mongo Seed: %d Banken migriert", len(docs))

    def _seed_kontotypen(self) -> None:
        payload = self._read_json_file(self.settings.frontend_seed_kontotypen_file)
        kontotypen = payload.get("Kontotypen", [])
        docs = [self._normalize_account_type(item) for item in kontotypen]
        if docs:
            self.account_type_collection.insert_many(docs)
            logger.info("Mongo Seed: %d Kontotypen migriert", len(docs))

    def _normalize_person(self, person: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(person, dict):
            logger.warning("MongoRepository._normalize_person: Ungültiger Personentyp: %s", type(person).__name__)
            person = {}
        person_doc = dict(person)
        person_doc.setdefault("id", str(uuid4()))
        konten = []
        for konto in person_doc.get("Konten", []):
            if not isinstance(konto, dict):
                logger.warning("MongoRepository._normalize_person: Ungültiger Kontotyp übersprungen: %s", konto)
                continue
            konto_doc = dict(konto)
            konto_doc.setdefault("id", str(uuid4()))
            konten.append(konto_doc)
        person_doc["Konten"] = konten
        return person_doc

    def _normalize_bank(self, bank: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(bank, dict):
            logger.warning("MongoRepository._normalize_bank: Ungültiger Banktyp: %s", type(bank).__name__)
            bank = {}
        bank_doc = dict(bank)
        bank_doc.setdefault("id", str(uuid4()))
        bank_doc.setdefault("BIC", [])
        bank_doc.setdefault("BLZ", [])
        return bank_doc

    def _normalize_account_type(self, item: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(item, dict) or not item:
            logger.warning("MongoRepository._normalize_account_type: Ungültiger Kontotyp-Eintrag: %s", item)
            return {"id": str(uuid4()), "name": "Unbekannt", "fields": []}
        key = next(iter(item.keys()))
        fields = item.get(key, [])
        return {"id": str(uuid4()), "name": key, "fields": fields}

    @staticmethod
    def _clean_mongo_id(doc: dict[str, Any]) -> dict[str, Any]:
        out = dict(doc)
        out.pop("_id", None)
        return out

    def list_personen(self) -> list[dict[str, Any]]:
        return [self._clean_mongo_id(doc) for doc in self.person_collection.find({})]

    def upsert_person(self, person: dict[str, Any]) -> bool:
        person_doc = self._normalize_person(person)
        result = self.person_collection.replace_one({"id": person_doc["id"]}, person_doc, upsert=True)
        return bool(result.acknowledged)

    def get_person_by_id(self, person_id: str) -> dict[str, Any] | None:
        doc = self.person_collection.find_one({"id": person_id})
        return self._clean_mongo_id(doc) if doc else None

    def update_person(self, person_id: str, person_doc: dict[str, Any]) -> bool:
        normalized = self._normalize_person(person_doc)
        normalized["id"] = person_id
        result = self.person_collection.replace_one({"id": person_id}, normalized, upsert=False)
        return result.modified_count >= 0 and result.matched_count == 1

    def list_banken(self) -> list[dict[str, Any]]:
        return [self._clean_mongo_id(doc) for doc in self.bank_collection.find({})]

    def save_banken(self, banken: list[dict[str, Any]]) -> bool:
        self.bank_collection.delete_many({})
        docs = [self._normalize_bank(bank) for bank in banken]
        if docs:
            self.bank_collection.insert_many(docs)
        return True

    def list_kontotypen(self) -> list[dict[str, Any]]:
        docs = [self._clean_mongo_id(doc) for doc in self.account_type_collection.find({})]
        return [{doc["name"]: doc.get("fields", [])} for doc in docs]

    def close(self) -> None:
        self.client.close()
