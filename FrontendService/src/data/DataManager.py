from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import requests
from pymongo.errors import PyMongoError

from shared_config import get_settings
from src.data.mongo_repository import MongoRepository

logger = logging.getLogger(__name__)


class DataManager:
    """Zentrale Datenlogik für Frontend; Persistenz erfolgt über MongoRepository."""

    def __init__(self):
        self.settings = get_settings()
        self.repository = MongoRepository()
        self._available = self._init_db()

    def _init_db(self) -> bool:
        try:
            self.repository.ping()
            self.repository.ensure_seeded()
            logger.info("DataManager: MongoDB verbunden und initialisiert")
            return True
        except PyMongoError:
            logger.exception("DataManager: MongoDB nicht erreichbar")
            return False

    def _with_db_or_default(self, fn, default):
        if not self._available:
            logger.warning("DataManager: MongoDB ist nicht verfügbar")
            return default
        try:
            return fn()
        except PyMongoError:
            logger.exception("DataManager: Datenbankoperation fehlgeschlagen")
            return default

    def load_personen(self):
        return self._with_db_or_default(self.repository.list_personen, [])

    def save_personen(self, personen):
        def save_all() -> None:
            for person in personen:
                person.setdefault("id", str(uuid4()))
                self.repository.upsert_person(person)

        self._with_db_or_default(save_all, None)

    def get_person(self, person_id: str):
        return self._with_db_or_default(lambda: self.repository.get_person_by_id(person_id), None)

    def get_person_data(self, selected_person):
        selected_id = selected_person.get("id")
        if selected_id:
            return self.get_person(selected_id)
        for p in self.load_personen():
            if p.get("Name") == selected_person.get("Name") and p.get("Nachname") == selected_person.get("Nachname"):
                return p
        return None

    def save_person_data(self, updated_person):
        person_id = updated_person.get("id")
        if person_id:
            self._with_db_or_default(lambda: self.repository.update_person(person_id, updated_person), False)
            return

        personen = self.load_personen()
        for person in personen:
            if person.get("Name") == updated_person.get("Name") and person.get("Nachname") == updated_person.get("Nachname"):
                updated_person["id"] = person.get("id", str(uuid4()))
                self._with_db_or_default(lambda: self.repository.update_person(updated_person["id"], updated_person), False)
                return
        updated_person["id"] = str(uuid4())
        self._with_db_or_default(lambda: self.repository.upsert_person(updated_person), False)

    def create_account(self, person_id: str, account_type: str, account_data: dict[str, Any]) -> bool:
        person = self.get_person(person_id)
        if not person:
            return False
        konto = {"id": str(uuid4()), "Kontotyp": account_type}
        konto.update(account_data)
        person.setdefault("Konten", []).append(konto)
        return self._with_db_or_default(lambda: self.repository.update_person(person_id, person), False)

    def update_account(self, selected_person, account_type, account_data):
        person_id = selected_person.get("id") if isinstance(selected_person, dict) else selected_person
        if not person_id:
            person = self.get_person_data(selected_person)
            person_id = person.get("id") if person else None
        if not person_id:
            return False
        return self.create_account(person_id, account_type, account_data)

    def duplicate_account(self, selected_person, account_type, account_data):
        person_id = selected_person.get("id") if isinstance(selected_person, dict) else selected_person
        person = self.get_person(person_id) if person_id else self.get_person_data(selected_person)
        if not person:
            return False
        target_number = account_data.get("Kontonummer", account_data.get("Deponummer"))
        for acct in person.get("Konten", []):
            if (
                acct.get("Kontotyp") == account_type
                and acct.get("Bank") == account_data.get("Bank")
                and acct.get("Kontonummer", acct.get("Deponummer")) == target_number
            ):
                return True
        return False

    def update_kontostaende(self, konto, datum_str, wert):
        existing = {}
        for entry in konto.get("Kontostaende", []):
            parts = entry.split(": ")
            if len(parts) == 2:
                existing[parts[0]] = parts[1]
        existing[datum_str] = f"{wert:.2f}"
        konto["Kontostaende"] = [f"{d}: {existing[d]}" for d in sorted(existing)]

    def update_account_balance(self, konto_id: str, datum_str: str, wert: float) -> bool:
        personen = self.load_personen()
        for person in personen:
            for konto in person.get("Konten", []):
                if konto.get("id") == konto_id:
                    self.update_kontostaende(konto, datum_str, wert)
                    return self._with_db_or_default(lambda: self.repository.update_person(person["id"], person), False)
        return False

    def save_account_balance(self, selected_person, account, balance, date_value):
        person = self.get_person_data(selected_person)
        if not person:
            return
        target_account_id = account.get("id")
        if not target_account_id:
            for acct in person.get("Konten", []):
                if acct.get("BIC", "") == account.get("BIC", "") and acct.get("Kontonummer", acct.get("Deponummer")) == account.get(
                    "Kontonummer", account.get("Deponummer")
                ):
                    target_account_id = acct.get("id")
                    break
        if target_account_id:
            self.update_account_balance(target_account_id, date_value.strftime("%Y-%m-%d"), balance)

    def update_depot_details(self, selected_person, account, depot_details):
        person_id = selected_person.get("id") if isinstance(selected_person, dict) else selected_person
        konto_id = account.get("id") if isinstance(account, dict) else account
        person = self.get_person(person_id) if person_id else self.get_person_data(selected_person)
        if not person:
            return
        for acct in person.get("Konten", []):
            if acct.get("id") == konto_id:
                acct["DepotDetails"] = depot_details
                self._with_db_or_default(lambda: self.repository.update_person(person["id"], person), False)
                return

    def load_bank_data(self):
        banken = self._with_db_or_default(self.repository.list_banken, [])
        return {"Banken": [{k: v for k, v in bank.items() if k != "id"} for bank in banken]}

    def save_bank_data(self, bank_data: dict[str, Any]):
        banken = bank_data.get("Banken", [])
        self._with_db_or_default(lambda: self.repository.save_banken(banken), False)

    def load_kontotypen(self):
        kontotypen = self._with_db_or_default(self.repository.list_kontotypen, [])
        return {"Kontotypen": kontotypen}

    def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = requests.get(url, params=params, timeout=8)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            logger.exception("HTTP-Fehler beim Aufruf von %s", url)
            return {}

    def get_price(self, isin: str, target_date):
        url = f"{self.settings.marketdata_base_url}/price/{isin}"
        payload = self._get(url, {"date": target_date.isoformat() if target_date else None})
        return float(payload.get("price", 0.0) or 0.0)

    def get_company_name(self, isin: str):
        url = f"{self.settings.marketdata_base_url}/company/{isin}"
        payload = self._get(url)
        return payload.get("company_name") or isin

    def calculate_festgeld_for_date(self, konto_or_id, date) -> float:
        konto = konto_or_id
        if isinstance(konto_or_id, str):
            konto = None
            for person in self.load_personen():
                for account in person.get("Konten", []):
                    if account.get("id") == konto_or_id:
                        konto = account
                        break
                if konto:
                    break
            if konto is None:
                return 0.0

        if isinstance(date, datetime):
            dt = date.date()
        else:
            dt = date
        anlagedatum_str = konto.get("Anlagedatum", "")
        try:
            anlagedatum = datetime.strptime(anlagedatum_str, "%Y-%m-%d").date()
        except ValueError:
            try:
                anlagedatum = datetime.strptime(anlagedatum_str, "%d.%m.%Y").date()
            except Exception:
                anlagedatum = dt
        try:
            anlagebetrag = float(konto.get("Anlagebetrag", 0))
        except Exception:
            anlagebetrag = 0.0
        try:
            zinssatz = float(konto.get("Zinssatz", 0))
        except Exception:
            zinssatz = 0.0
        try:
            laufzeit = int(konto.get("Laufzeit_in_Tagen", 0))
        except Exception:
            laufzeit = 0
        end_date = anlagedatum + timedelta(days=laufzeit)
        if dt < anlagedatum:
            return anlagebetrag
        tage = (min(dt, end_date) - anlagedatum).days
        zinsen = anlagebetrag * (zinssatz / 100.0) * (tage / 360.0)
        return anlagebetrag + zinsen
