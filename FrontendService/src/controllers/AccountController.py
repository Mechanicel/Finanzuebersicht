# src/controllers/AccountController.py
import logging
from datetime import datetime
from dotenv import load_dotenv
from FrontendService.src.data.DataManager import DataManager

# Logging konfigurieren
logging.basicConfig(level=logging.DEBUG)
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
        logger.debug(f"AccountController.add_account: Person={selected_person}, Typ={account_type}, Data={account_data}")
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
        """
        Fragt alle Depot-Positionen ab, ruft Preise vom Stock-Service ab und aktualisiert im Backend.
        """
        logger.debug(f"AccountController.calculate_depot: Person={selected_person}, Datum={date_value}")
        # Backend liefert Person inkl. Konten
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
                    "value": value
                })
                logger.debug(f"Depot-Position: {isin}, Menge={menge}, Preis={price}, Wert={value}")
            # Update DepotDetails im Backend
            self.data_manager.update_depot_details(selected_person['id'], konto['id'], details)
        logger.info("AccountController.calculate_depot: Depot-Berechnung abgeschlossen")

    def calculate_festgeld(self, selected_person: dict, date_value: datetime):
        """
        Berechnet Festgeld-Zinsen für alle Festgeldkonten zum gegebenen Datum und speichert sie ab.
        """
        logger.debug(f"AccountController.calculate_festgeld: Person={selected_person}, Datum={date_value}")
        person = self.data_manager.get_person(selected_person['id'])
        if not person:
            logger.warning("AccountController.calculate_festgeld: Person nicht gefunden")
            return
        for konto in person.get("Konten", []):
            if konto.get("Kontotyp") != "Festgeldkonto":
                continue
            wert = self.data_manager.calculate_festgeld_for_date(konto['id'], date_value)
            self.data_manager.update_account_balance(konto['id'], date_value.strftime("%Y-%m-%d"), wert)
            logger.debug(f"Festgeld-Konto {konto['id']}: Zinswert={wert}")
        logger.info("AccountController.calculate_festgeld: Festgeld-Berechnung abgeschlossen")

    def calculate(self, selected_person: dict, date_value: datetime):
        """Wrapper, um alle Berechnungen gemeinsam auszuführen."""
        logger.debug("AccountController.calculate: Starte alle Berechnungen")
        self.calculate_depot(selected_person, date_value)
        self.calculate_festgeld(selected_person, date_value)

    def update_account_overview(self, selected_person: dict, date_value: datetime, entries: list):
        """
        Sendet alle neuen Konto-Übersichtseinträge ans Backend und löst anschließend Neuberechnungen aus.
        """
        logger.debug(f"AccountController.update_account_overview: Person={selected_person}, Datum={date_value}, Einträge={entries}")
        for entry in entries:
            account_type = entry.get("Kontotyp")
            account_data = entry.get("Data")
            self.add_account(selected_person, account_type, account_data)
        # Nach Anlage neuer Konten sofort neu berechnen
        self.calculate(selected_person, date_value)
        logger.info("AccountController.update_account_overview: Übersicht aktualisiert und neu berechnet")
