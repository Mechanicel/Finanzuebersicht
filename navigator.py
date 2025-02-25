# navigator.py
from screens import (
    screen_main,
    screen_person_selection,
    screen_new_person,
    screen_new_bank,
    screen_person_info,
    screen_bank_assignment,
    screen_freibetrag_input,
    screen_freibetrag_display,
    screen_account_addition,
    screen_account_overview,
    screen_account_summary,
)

class Navigator:
    def __init__(self, app):
        self.app = app
        # Definiere eine Zuordnung (Route) von Screen-Namen zu den jeweiligen Funktionen.
        self.routes = {
            "main_screen": screen_main.create_main_screen,
            "person_selection": screen_person_selection.person_selection_screen,
            "new_person": screen_new_person.new_person_screen,
            "new_bank": screen_new_bank.new_bank_screen,
            "person_info": screen_person_info.person_info_screen,
            "bank_assignment": screen_bank_assignment.bank_assignment_screen,
            "freibetrag_input": screen_freibetrag_input.freibetrag_input_screen,
            "freibetrag_display": screen_freibetrag_display.freibetrag_display_screen,
            "account_addition": screen_account_addition.account_addition_screen,
            "account_overview": screen_account_overview.account_overview_screen,
            "account_summary": screen_account_summary.account_summary_screen,
        }

    def navigate(self, screen_name, **kwargs):
        if screen_name in self.routes:
            # Alle Screen-Funktionen haben als Parameter: app, navigator, und optionale weitere Parameter.
            self.routes[screen_name](self.app, self, **kwargs)
        else:
            print(f"Screen '{screen_name}' nicht gefunden.")
