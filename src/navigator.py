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
    AccountEditing  # Neuer Eintrag für den AccountEditing-Screen
)

class Navigator:
    def __init__(self, app):
        self.app = app
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
            "AccountEditing": AccountEditing.create_screen  # Neuer Screen
        }

    def navigate(self, screen_name, **kwargs):
        if screen_name in self.routes:
            # Alle Screens erhalten als Parameter: app, navigator und optionale weitere Parameter.
            self.routes[screen_name](self.app, self, **kwargs)
        else:
            print(f"Screen '{screen_name}' nicht gefunden.")
