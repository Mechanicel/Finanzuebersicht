from datetime import datetime, time
from data.DataManager import DataManager

class AccountController:
    """
    Steuert das Anlegen, manuelle Aktualisieren und die Berechnung von Kontenwerten.
    Unterstützt nun Stichtags-Berechnungen und manuelle Eingaben über den AccountOverview-Screen.
    """
    def __init__(self):
        self.data_manager = DataManager()

    def add_account(self, selected_person: dict, account_type: str, account_data: dict) -> bool:
        """
        Legt ein neues Konto an, sofern es nicht bereits existiert.
        """
        if self.is_duplicate_account(selected_person, account_type, account_data):
            print("Dieses Konto wurde bereits angelegt.")
            return False
        self.data_manager.update_account(selected_person, account_type, account_data)
        return True

    def is_duplicate_account(self, selected_person: dict, account_type: str, account_data: dict) -> bool:
        """
        Prüft, ob ein Konto mit gleichem Typ und Nummer/BIC bereits existiert.
        """
        return self.data_manager.duplicate_account(selected_person, account_type, account_data)

    def calculate_festgeld(self, selected_person: dict, date: datetime):
        """
        Aktualisiert für alle Festgeldkonten den Wert am gegebenen Datum.
        """
        data = self.data_manager.load_personen()
        heute_str = date.strftime("%Y-%m-%d")
        updated = False

        for idx, person in enumerate(data):
            if (person.get("Name") == selected_person.get("Name")
                    and person.get("Nachname") == selected_person.get("Nachname")):
                for konto in person.get("Konten", []):
                    if konto.get("Kontotyp") != "Festgeldkonto":
                        continue
                    wert = self.data_manager.calculate_festgeld_for_date(konto, date)
                    self.data_manager.update_kontostaende(konto, heute_str, wert)
                    updated = True
                data[idx] = person
                break

        if updated:
            self.data_manager.save_personen(data)
            print(f"[Calculate Festgeld] Festgeldwerte für {heute_str} aktualisiert.")
        else:
            print("[Calculate Festgeld] Keine Festgeldkonten gefunden.")

    def calculate_depot(self, selected_person: dict, date: datetime):
        """
        Berechnet für jedes Depotkonto den Gesamtwert am gegebenen Datum.
        """
        data = self.data_manager.load_personen()
        heute_str = date.strftime("%Y-%m-%d")
        updated = False

        for idx, person in enumerate(data):
            if (person.get("Name") == selected_person.get("Name")
                    and person.get("Nachname") == selected_person.get("Nachname")):
                for konto in person.get("Konten", []):
                    if konto.get("Kontotyp") != "Depot":
                        continue
                    wert = self.data_manager.get_depot_value(konto, date)
                    self.data_manager.update_kontostaende(konto, heute_str, wert)
                    updated = True
                data[idx] = person
                break

        if updated:
            self.data_manager.save_personen(data)
            print(f"[Calculate Depot] Depotwerte für {heute_str} aktualisiert.")
        else:
            print("[Calculate Depot] Keine Depotkonten gefunden.")

    def calculate(self, selected_person: dict, date: datetime):
        """
        Führt die Berechnung aller Kontotypen für das gegebene Datum durch.
        """
        self.calculate_festgeld(selected_person, date)
        self.calculate_depot(selected_person, date)
        print(f"[Calculate] Alle Konto-Berechnungen für {date.strftime('%Y-%m-%d')} abgeschlossen.")

    def update_account_overview(self, selected_person: dict, date: datetime, inputs: list):
        """
        Speichert manuelle Eingaben für Konten (non-Depot) und Depots am gewählten Datum.
        """
        # Datum sicher in datetime umwandeln, falls nur date übergeben wurde
        if not isinstance(date, datetime):
            date = datetime.combine(date, time.min)

        for item in inputs:
            konto = item.get('konto')
            if 'details' in item:
                # Depot: Details und Kontostand aktualisieren
                details = item.get('details', [])
                self.data_manager.update_depot_details(selected_person, konto, details)
                total = 0.0
                for det in details:
                    try:
                        menge = float(det.get('Menge', 0))
                    except:
                        menge = 0.0
                    price = self.data_manager.get_price_by_isin(det.get('ISIN', '').strip(), date)
                    total += price * menge
                self.data_manager.save_account_balance(selected_person, konto, total, date)
            else:
                # Standardkonto: manueller Kontostand
                balance = item.get('balance', 0.0)
                self.data_manager.save_account_balance(selected_person, konto, balance, date)
