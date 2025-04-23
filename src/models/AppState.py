from datetime import date
from typing import List, Optional

from src.controllers.AccountController import AccountController
from src.data.DataManager import DataManager


class AppState:
    """
    Zentrale Store‑Klasse für die Finanzübersicht‑App.
    Enthält alle persistente Daten und UI‑Kontexte.
    """
    def __init__(self):
        # persistente Daten
        self.personen: List[dict] = []          # geladen aus personen.json
        self.banken: List[dict] = []            # geladen aus banken.json
        self.kontotypen: List[dict] = []        # geladen aus kontotypen.json

        # aktueller Zustand/Selektion
        self.selected_person: Optional[dict] = None
        self.selected_date: Optional[date] = None

        # temporäre Eingaben im AccountOverview
        self.overview_inputs: List[dict] = []   # [{'konto':…, 'balance':…}, ...]

        # zentrale Manager/Controller
        self.data_manager: DataManager = DataManager()
        self.account_controller: AccountController = AccountController()

    # Laden/Speichern
    def load_all(self):
        self.personen    = self.data_manager.load_personen()
        self.banken      = self.data_manager.load_bank_data().get("Banken", [])
        self.kontotypen  = self.data_manager.load_kontotypen().get("Kontotypen", [])

    def save_person(self, person: dict):
        self.data_manager.save_person_data(person)
        # auch Liste im Store aktualisieren
        for i,p in enumerate(self.personen):
            if p["Name"]==person["Name"] and p["Nachname"]==person["Nachname"]:
                self.personen[i] = person
                return

    # Auswählen
    def select_person(self, name:str, nachname:str):
        for p in self.personen:
            if p["Name"]==name and p["Nachname"]==nachname:
                self.selected_person = p
                return p
        self.selected_person = None
        return None

    # Übersicht eingaben sammeln
    def reset_overview(self):
        self.selected_date = None
        self.overview_inputs = []

    def add_overview_entry(self, entry: dict):
        self.overview_inputs.append(entry)

    # Berechnungen / Updates delegieren
    def calculate_all(self):
        if self.selected_person and self.selected_date:
            self.account_controller.calculate(self.selected_person, self.selected_date)

    def commit_overview(self):
        if self.selected_person and self.selected_date:
            self.account_controller.update_account_overview(
                self.selected_person, self.selected_date, self.overview_inputs
            )
