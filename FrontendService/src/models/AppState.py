import logging
from datetime import date
from typing import List, Optional

from src.controllers.AccountController import AccountController
from src.data.DataManager import DataManager

logger = logging.getLogger(__name__)


class AppState:
    """
    Zentrale Store-Klasse für die Finanzübersicht-App.
    Enthält alle persistente Daten, UI-Kontexte und bietet
    Zugriff auf konto- und aktienbezogene Services.
    """

    def __init__(self):
        logger.debug("AppState: Initialisierung gestartet")

        # persistente Daten
        self.personen: List[dict] = []
        self.banken: List[dict] = []
        self.kontotypen: List[dict] = []

        # aktueller Zustand/Selektion
        self.selected_person: Optional[dict] = None
        self.selected_date: Optional[date] = None

        # temporäre Eingaben im AccountOverview
        self.overview_inputs: List[dict] = []

        # Manager/Controller
        self.data_manager: DataManager = DataManager()
        self.account_controller: AccountController = AccountController()

        logger.debug("AppState: Initialisierung abgeschlossen")

    def load_all(self):
        logger.debug("AppState.load_all: Lade Basisdaten")
        prev = self.selected_person
        self.personen = self.data_manager.load_personen()
        self.banken = self.data_manager.load_bank_data().get("Banken", [])
        self.kontotypen = self.data_manager.load_kontotypen().get("Kontotypen", [])
        if prev:
            self.select_person(prev.get("Name"), prev.get("Nachname"))

    def save_person(self, person: dict):
        if not isinstance(person, dict):
            logger.warning("AppState.save_person: Ungültiger Personentyp verworfen: %s", type(person).__name__)
            return
        self.data_manager.save_person_data(person)
        for i, p in enumerate(self.personen):
            if not isinstance(p, dict):
                logger.warning("AppState.save_person: Ungültiger Personeneintrag übersprungen: %s", p)
                continue
            if p.get("Name") == person.get("Name") and p.get("Nachname") == person.get("Nachname"):
                self.personen[i] = person
                return

    def select_person(self, name: str, nachname: str):
        for p in self.personen:
            if not isinstance(p, dict):
                logger.warning("AppState.select_person: Ungültiger Personeneintrag übersprungen: %s", p)
                continue
            if p.get("Name") == name and p.get("Nachname") == nachname:
                self.selected_person = p
                return p
        self.selected_person = None
        return None

    def reset_overview(self):
        self.selected_date = None
        self.overview_inputs = []

    def add_overview_entry(self, entry: dict):
        if not isinstance(entry, dict):
            logger.warning("AppState.add_overview_entry: Ungültiger Entry verworfen: %s", entry)
            return
        self.overview_inputs.append(entry)

    def calculate_all(self):
        if self.selected_person and self.selected_date:
            self.account_controller.calculate(self.selected_person, self.selected_date)

    def commit_overview(self):
        if self.selected_person and self.selected_date:
            self.account_controller.update_account_overview(
                self.selected_person,
                self.selected_date,
                self.overview_inputs,
            )
