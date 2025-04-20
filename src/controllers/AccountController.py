from datetime import datetime, timedelta
from data.DataManager import DataManager

class AccountController:
    def __init__(self):
        self.data_manager = DataManager()

    def add_account(self, selected_person, account_type, account_data):
        if self.is_duplicate_account(selected_person, account_type, account_data):
            print("Dieses Konto wurde bereits angelegt.")
            return False
        self.data_manager.update_account(selected_person, account_type, account_data)
        return True

    def is_duplicate_account(self, selected_person, account_type, account_data):
        return self.data_manager.duplicate_account(selected_person, account_type, account_data)

    def calculate_festgeld(self, selected_person):
        """
        Aktualisiert für alle Festgeldkonten den aktuellen Wert
        und speichert ihn in 'Kontostaende'.
        """
        data = self.data_manager.load_personen()
        updated = False
        heute_date = datetime.now().date()
        heute_str = heute_date.strftime("%Y-%m-%d")

        for idx, person in enumerate(data):
            if (person.get("Name") == selected_person.get("Name")
                    and person.get("Nachname") == selected_person.get("Nachname")):
                for konto in person.get("Konten", []):
                    if konto.get("Kontotyp") != "Festgeldkonto":
                        continue

                    try:
                        anlagebetrag = float(konto.get("Anlagebetrag", "0"))
                    except:
                        anlagebetrag = 0.0
                    try:
                        zinssatz = float(konto.get("Zinssatz", "0"))
                    except:
                        zinssatz = 0.0
                    try:
                        anlagedatum = datetime.strptime(konto.get("Anlagedatum", ""), "%Y-%m-%d").date()
                    except:
                        anlagedatum = heute_date
                    try:
                        laufzeit = int(konto.get("Laufzeit_in_Tagen", "0"))
                    except:
                        laufzeit = 0

                    end_date = anlagedatum + timedelta(days=laufzeit)
                    if heute_date < anlagedatum:
                        wert = anlagebetrag
                    else:
                        ende = min(heute_date, end_date)
                        tage = (ende - anlagedatum).days
                        zinsen = anlagebetrag * (zinssatz / 100.0) * (tage / 360.0)
                        wert = anlagebetrag + zinsen

                    # Kontostaende updaten
                    if "Kontostaende" not in konto:
                        konto["Kontostaende"] = []
                    replaced = False
                    for i, entry in enumerate(konto["Kontostaende"]):
                        d, _ = entry.split(": ")
                        if d == heute_str:
                            konto["Kontostaende"][i] = f"{heute_str}: {wert:.2f}"
                            replaced = True
                            break
                    if not replaced:
                        konto["Kontostaende"].append(f"{heute_str}: {wert:.2f}")
                    updated = True

                data[idx] = person
                break

        if updated:
            self.data_manager.save_personen(data)
            print("[Calculate Festgeld] Festgeldwerte erfolgreich aktualisiert.")
        else:
            print("[Calculate Festgeld] Keine Festgeldkonten gefunden oder keine Änderungen nötig.")

    def calculate_depot(self, selected_person):
        """
        Berechnet für jedes Depotkonto den aktuellen Gesamtwert
        und speichert ihn in 'Kontostaende'.
        """
        data = self.data_manager.load_personen()
        updated = False
        heute_date = datetime.now().date()
        heute_str = heute_date.strftime("%Y-%m-%d")

        for idx, person in enumerate(data):
            if (person.get("Name") == selected_person.get("Name")
                    and person.get("Nachname") == selected_person.get("Nachname")):
                for konto in person.get("Konten", []):
                    if konto.get("Kontotyp") != "Depot":
                        continue

                    wert = self.data_manager.get_depot_value(konto)

                    # Kontostaende updaten
                    if "Kontostaende" not in konto:
                        konto["Kontostaende"] = []
                    replaced = False
                    for i, entry in enumerate(konto["Kontostaende"]):
                        d, _ = entry.split(": ")
                        if d == heute_str:
                            konto["Kontostaende"][i] = f"{heute_str}: {wert:.2f}"
                            replaced = True
                            break
                    if not replaced:
                        konto["Kontostaende"].append(f"{heute_str}: {wert:.2f}")
                    updated = True

                data[idx] = person
                break

        if updated:
            self.data_manager.save_personen(data)
            print("[Calculate Depot] Depotwerte erfolgreich aktualisiert.")
        else:
            print("[Calculate Depot] Keine Depotkonten gefunden oder keine Änderungen nötig.")

    def calculate(self, selected_person):
        """
        Führt nacheinander alle notwendigen Berechnungen durch:
        1) Festgeld
        2) Depot
        """
        self.calculate_festgeld(selected_person)
        self.calculate_depot(selected_person)
        print("[Calculate] Alle Konto-Berechnungen abgeschlossen.")
