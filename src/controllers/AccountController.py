# src/controllers/AccountController.py

import logging
from datetime import datetime, time
from data.DataManager import DataManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AccountController:
    """
    Steuert das Anlegen, manuelle Aktualisieren und die Berechnung von Kontenwerten.
    Unterstützt nun Stichtags-Berechnungen und manuelle Eingaben über den AccountOverview-Screen.
    """
    def __init__(self):
        self.data_manager = DataManager()
        logger.debug("AccountController initialized")

    def add_account(self, selected_person: dict, account_type: str, account_data: dict) -> bool:
        logger.debug(f"add_account: {selected_person}, Typ {account_type}, Data {account_data}")
        if self.is_duplicate_account(selected_person, account_type, account_data):
            logger.warning("add_account: Duplikat erkannt")
            return False
        self.data_manager.update_account(selected_person, account_type, account_data)
        logger.debug("add_account: Konto hinzugefügt")
        return True

    def is_duplicate_account(self, selected_person: dict, account_type: str, account_data: dict) -> bool:
        logger.debug(f"is_duplicate_account: Prüfe für {selected_person}, {account_type}")
        return self.data_manager.duplicate_account(selected_person, account_type, account_data)

    def calculate_festgeld(self, selected_person: dict, date: datetime):
        logger.debug(f"calculate_festgeld: {selected_person}, Datum {date}")
        data = self.data_manager.load_personen()
        heute_str = date.strftime("%Y-%m-%d")
        updated = False

        for person in data:
            if (person.get("Name") == selected_person.get("Name")
                    and person.get("Nachname") == selected_person.get("Nachname")):
                for konto in person.get("Konten", []):
                    if konto.get("Kontotyp") != "Festgeldkonto":
                        continue
                    wert = self.data_manager.calculate_festgeld_for_date(konto, date)
                    self.data_manager.update_kontostaende(konto, heute_str, wert)
                    logger.debug(f"calculate_festgeld: {konto} -> {wert:.2f}")
                    updated = True
                break

        if updated:
            self.data_manager.save_personen(data)
            logger.info(f"[Calculate Festgeld] Festgeldwerte für {heute_str} aktualisiert.")
        else:
            logger.info("[Calculate Festgeld] Keine Festgeldkonten gefunden.")

    def calculate_depot(self, selected_person: dict, date: datetime):
        logger.debug(f"calculate_depot: {selected_person}, Datum {date}")
        data = self.data_manager.load_personen()
        heute_str = date.strftime("%Y-%m-%d")
        updated = False

        for person in data:
            if (person.get("Name") == selected_person.get("Name")
                    and person.get("Nachname") == selected_person.get("Nachname")):
                for konto in person.get("Konten", []):
                    if konto.get("Kontotyp") != "Depot":
                        continue
                    wert = self.data_manager.get_depot_value(konto, date)
                    self.data_manager.update_kontostaende(konto, heute_str, wert)
                    logger.debug(f"calculate_depot: {konto} -> {wert:.2f}")
                    updated = True
                break

        if updated:
            self.data_manager.save_personen(data)
            logger.info(f"[Calculate Depot] Depotwerte für {heute_str} aktualisiert.")
        else:
            logger.info("[Calculate Depot] Keine Depotkonten gefunden.")

    def calculate(self, selected_person: dict, date: datetime):
        logger.debug(f"calculate: Starte Gesamtberechnung für {selected_person} am {date}")
        self.calculate_festgeld(selected_person, date)
        self.calculate_depot(selected_person, date)
        logger.info(f"[Calculate] Alle Konto-Berechnungen für {date.strftime('%Y-%m-%d')} abgeschlossen.")

    def update_account_overview(self, selected_person: dict, date: datetime, inputs: list):
        logger.debug(f"update_account_overview: {selected_person}, Datum {date}, Inputs {inputs}")
        if not isinstance(date, datetime):
            date = datetime.combine(date, time.min)
            logger.debug(f"update_account_overview: Datum in datetime umgewandelt: {date}")

        for item in inputs:
            konto = item.get('konto')
            if 'details' in item:
                details = item.get('details', [])
                logger.debug(f"update_account_overview: DepotDetails für {konto}: {details}")
                self.data_manager.update_depot_details(selected_person, konto, details)
                total = 0.0
                for det in details:
                    try:
                        menge = float(det.get('Menge', 0))
                    except:
                        menge = 0.0
                    price = self.data_manager.get_price_by_isin(det.get('ISIN', '').strip(), date)
                    total += price * menge
                logger.debug(f"update_account_overview: Neuer Depotwert {total:.2f}")
                self.data_manager.save_account_balance(selected_person, konto, total, date)
            else:
                balance = item.get('balance', 0.0)
                logger.debug(f"update_account_overview: Manueller Saldo für {konto}: {balance:.2f}")
                self.data_manager.save_account_balance(selected_person, konto, balance, date)
