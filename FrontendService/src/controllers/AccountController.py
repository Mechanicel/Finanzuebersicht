import logging
from datetime import datetime

from dotenv import load_dotenv

from src.data.DataManager import DataManager

logger = logging.getLogger(__name__)
load_dotenv()


class AccountController:
    """
    Steuert Konten-Operationen und Berechnungen, kommuniziert über DataManager mit dem Backend.
    """

    def __init__(self):
        self.data_manager = DataManager()
        logger.debug("AccountController: Initialisiert")

    def add_account(self, selected_person: dict, account_type: str, account_data: dict) -> bool:
        """
        Legt ein neues Konto für eine Person an, wenn kein Duplikat existiert.
        """
        logger.debug(
            "AccountController.add_account: Person=%s, Typ=%s",
            selected_person,
            account_type,
        )
        if self.data_manager.duplicate_account(selected_person['id'], account_type, account_data):
            logger.warning("AccountController.add_account: Duplikat erkannt, Abbruch")
            return False
        result = self.data_manager.create_account(selected_person['id'], account_type, account_data)
        if result:
            logger.debug("AccountController.add_account: Konto erfolgreich angelegt")
        else:
            logger.error("AccountController.add_account: Fehler beim Anlegen des Kontos")
        return result

    def calculate_depot(self, selected_person: dict, date_value: datetime):
        logger.debug("AccountController.calculate_depot: Person=%s, Datum=%s", selected_person, date_value)
        person = self.data_manager.get_person(selected_person['id'])
        if not person:
            logger.warning("AccountController.calculate_depot: Person nicht gefunden")
            return
        for konto in person.get("Konten", []):
            if konto.get("Kontotyp") != "Depot":
                continue
            details = []
            for det in konto.get("DepotDetails", []):
                isin = det.get("ISIN", "").strip()
                menge = float(det.get("Menge", 0) or 0)
                price = self.data_manager.get_price(isin, date_value.date())
                company = self.data_manager.get_company_name(isin)
                value = price * menge
                details.append({
                    "ISIN": isin,
                    "company": company,
                    "price": price,
                    "Menge": menge,
                    "value": value,
                })
            self.data_manager.update_depot_details(selected_person['id'], konto['id'], details)
        logger.info("AccountController.calculate_depot: Depot-Berechnung abgeschlossen")

    def calculate_festgeld(self, selected_person: dict, date_value: datetime):
        logger.debug("AccountController.calculate_festgeld: Person=%s, Datum=%s", selected_person, date_value)
        person = self.data_manager.get_person(selected_person['id'])
        if not person:
            logger.warning("AccountController.calculate_festgeld: Person nicht gefunden")
            return
        for konto in person.get("Konten", []):
            if konto.get("Kontotyp") != "Festgeldkonto":
                continue
            wert = self.data_manager.calculate_festgeld_for_date(konto['id'], date_value)
            self.data_manager.update_account_balance(konto['id'], date_value.strftime("%Y-%m-%d"), wert)
            logger.debug("Festgeld-Konto %s: Zinswert=%s", konto['id'], wert)
        logger.info("AccountController.calculate_festgeld: Festgeld-Berechnung abgeschlossen")

    def calculate(self, selected_person: dict, date_value: datetime):
        logger.debug("AccountController.calculate: Starte alle Berechnungen")
        self.calculate_depot(selected_person, date_value)
        self.calculate_festgeld(selected_person, date_value)

    def update_account_overview(self, selected_person: dict, date_value: datetime, entries: list):
        logger.debug(
            "AccountController.update_account_overview: Person=%s, Datum=%s, Einträge=%d",
            selected_person,
            date_value,
            len(entries),
        )
        for entry in entries:
            account_type = entry.get("Kontotyp")
            account_data = entry.get("Data")
            self.add_account(selected_person, account_type, account_data)
        self.calculate(selected_person, date_value)
        logger.info("AccountController.update_account_overview: Übersicht aktualisiert und neu berechnet")
