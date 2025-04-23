import customtkinter

from screens import (
    MainScreen,
    PersonSelection,
    NewPerson,
    NewBank,
    PersonInfo,
    BankAssignment,
    FreibetragInput,
    FreibetragDisplay,
    AccountAddition,
    AccountOverview,
    AccountSummary,
    AccountEditing
)
from src.models.AppState import AppState


class Navigator:
    def __init__(self, app: customtkinter.CTk, state: AppState):
        self.app = app
        self.state = state
        # Mapping der Screens auf deren Erstellungsfunktionen
        self.routes = {
            "MainScreen": MainScreen.create_screen,
            "PersonSelection": PersonSelection.create_screen,
            "NewPerson": NewPerson.create_screen,
            "NewBank": NewBank.create_screen,
            "PersonInfo": PersonInfo.create_screen,
            "BankAssignment": BankAssignment.create_screen,
            "FreibetragInput": FreibetragInput.create_screen,
            "FreibetragDisplay": FreibetragDisplay.create_screen,
            "AccountAddition": AccountAddition.create_screen,
            "AccountOverview": AccountOverview.create_screen,
            "AccountSummary": AccountSummary.create_screen,
            "AccountEditing": AccountEditing.create_screen
        }

    def navigate(self, screen_name: str, **kwargs):
        if screen_name in self.routes:
            # screens expect: app, navigator, state, **kwargs
            self.routes[screen_name](self.app, self, self.state, **kwargs)
        else:
            print(f"Screen '{screen_name}' nicht gefunden.")