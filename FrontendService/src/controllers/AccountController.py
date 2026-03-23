import logging
from datetime import date, datetime

from src.data.DataManager import DataManager

logger = logging.getLogger(__name__)


class AccountController:
    """
    Steuert Konten-Operationen und Berechnungen, kommuniziert über DataManager mit dem Backend.
    """

    def __init__(self):
        self.data_manager = DataManager()
        logger.debug("AccountController: Initialisiert")

    @staticmethod
    def _extract_person_id(selected_person) -> str | None:
        if isinstance(selected_person, dict):
            person_id = selected_person.get("id")
            if not person_id:
                logger.warning("AccountController: selected_person ohne id verworfen: %s", selected_person)
                return None
            return person_id
        logger.warning("AccountController: selected_person hat ungültigen Typ: %s", type(selected_person).__name__)
        return None

    @staticmethod
    def _as_date(value: date | datetime) -> date:
        if isinstance(value, datetime):
            return value.date()
        return value

    def add_account(self, selected_person: dict, account_type: str, account_data: dict) -> bool:
        """
        Legt ein neues Konto für eine Person an, wenn kein Duplikat existiert.
        """
        logger.debug(
            "AccountController.add_account: Person=%s, Typ=%s",
            selected_person,
            account_type,
        )
        person_id = self._extract_person_id(selected_person)
        if not person_id:
            return False
        if not account_type:
            logger.warning("AccountController.add_account: Leerer account_type verworfen")
            return False
        if not isinstance(account_data, dict):
            logger.warning("AccountController.add_account: account_data hat ungültigen Typ: %s", type(account_data).__name__)
            return False

        if self.data_manager.duplicate_account(person_id, account_type, account_data):
            logger.warning("AccountController.add_account: Duplikat erkannt, Abbruch")
            return False
        result = self.data_manager.create_account(person_id, account_type, account_data)
        if result:
            logger.debug("AccountController.add_account: Konto erfolgreich angelegt")
        else:
            logger.error("AccountController.add_account: Fehler beim Anlegen des Kontos")
        return result

    def calculate_depot(self, selected_person: dict, date_value: date | datetime):
        logger.debug("AccountController.calculate_depot: Person=%s, Datum=%s", selected_person, date_value)
        person_id = self._extract_person_id(selected_person)
        if not person_id:
            return
        normalized_date = self._as_date(date_value)
        person = self.data_manager.get_person(person_id)
        if not person:
            logger.warning("AccountController.calculate_depot: Person nicht gefunden")
            return
        konten = person.get("Konten", [])
        if not isinstance(konten, list):
            logger.warning("AccountController.calculate_depot: Konten ist kein list-Typ für Person %s", person_id)
            return
        for konto in konten:
            if not isinstance(konto, dict):
                logger.warning("AccountController.calculate_depot: Ungültiger Kontoeintrag übersprungen: %s", konto)
                continue
            if konto.get("Kontotyp") != "Depot":
                continue
            details = []
            for det in konto.get("DepotDetails", []):
                if not isinstance(det, dict):
                    logger.warning("AccountController.calculate_depot: Ungültiges Depot-Detail übersprungen: %s", det)
                    continue
                isin = det.get("ISIN", "").strip()
                menge = float(det.get("Menge", 0) or 0)
                price = self.data_manager.get_price(isin, normalized_date)
                company = self.data_manager.get_company_name(isin)
                value = price * menge
                details.append({
                    "ISIN": isin,
                    "company": company,
                    "price": price,
                    "Menge": menge,
                    "value": value,
                })
            konto_id = konto.get("id")
            if not konto_id:
                logger.warning("AccountController.calculate_depot: Depotkonto ohne id übersprungen: %s", konto)
                continue
            self.data_manager.update_depot_details(person_id, konto_id, details)
        logger.info("AccountController.calculate_depot: Depot-Berechnung abgeschlossen")

    def calculate_festgeld(self, selected_person: dict, date_value: date | datetime):
        logger.debug("AccountController.calculate_festgeld: Person=%s, Datum=%s", selected_person, date_value)
        person_id = self._extract_person_id(selected_person)
        if not person_id:
            return
        normalized_date = self._as_date(date_value)
        person = self.data_manager.get_person(person_id)
        if not person:
            logger.warning("AccountController.calculate_festgeld: Person nicht gefunden")
            return
        konten = person.get("Konten", [])
        if not isinstance(konten, list):
            logger.warning("AccountController.calculate_festgeld: Konten ist kein list-Typ für Person %s", person_id)
            return
        for konto in konten:
            if not isinstance(konto, dict):
                logger.warning("AccountController.calculate_festgeld: Ungültiger Kontoeintrag übersprungen: %s", konto)
                continue
            if konto.get("Kontotyp") != "Festgeldkonto":
                continue
            konto_id = konto.get("id")
            if not konto_id:
                logger.warning("AccountController.calculate_festgeld: Festgeldkonto ohne id übersprungen: %s", konto)
                continue
            wert = self.data_manager.calculate_festgeld_for_date(konto_id, normalized_date)
            self.data_manager.update_account_balance(konto_id, normalized_date.strftime("%Y-%m-%d"), wert)
            logger.debug("Festgeld-Konto %s: Zinswert=%s", konto_id, wert)
        logger.info("AccountController.calculate_festgeld: Festgeld-Berechnung abgeschlossen")

    def calculate(self, selected_person: dict, date_value: date | datetime):
        logger.debug("AccountController.calculate: Starte alle Berechnungen")
        self.calculate_depot(selected_person, date_value)
        self.calculate_festgeld(selected_person, date_value)

    def update_account_overview(self, selected_person: dict, date_value: date | datetime, entries: list):
        logger.debug(
            "AccountController.update_account_overview: Person=%s, Datum=%s, Einträge=%d",
            selected_person,
            date_value,
            len(entries),
        )
        if not isinstance(entries, list):
            logger.warning("AccountController.update_account_overview: entries ist kein list-Typ: %s", type(entries).__name__)
            return

        for entry in entries:
            if not isinstance(entry, dict):
                logger.warning("AccountController.update_account_overview: Ungültiger Eintrag übersprungen: %s", entry)
                continue
            account_type = entry.get("Kontotyp")
            account_data = entry.get("Data")
            if not account_type and isinstance(entry.get("konto"), dict):
                account_type = entry["konto"].get("Kontotyp")
                konto_data = entry["konto"].copy()
                konto_data.pop("DepotDetails", None)
                if account_type == "Depot":
                    konto_data["DepotDetails"] = entry.get("details", [])
                else:
                    konto_data["Kontostand"] = entry.get("balance", 0.0)
                account_data = konto_data
            if not account_type:
                logger.warning("AccountController.update_account_overview: Eintrag ohne Kontotyp übersprungen: %s", entry)
                continue
            if not isinstance(account_data, dict):
                logger.warning(
                    "AccountController.update_account_overview: Data für Kontotyp %s ist ungültig (%s) und wird übersprungen",
                    account_type,
                    type(account_data).__name__,
                )
                continue
            self.add_account(selected_person, account_type, account_data)
        self.calculate(selected_person, date_value)
        logger.info("AccountController.update_account_overview: Übersicht aktualisiert und neu berechnet")
