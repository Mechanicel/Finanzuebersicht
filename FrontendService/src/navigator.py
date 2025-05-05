# src/navigator.py

from FrontendService.src.models.AppState import AppState
from FrontendService.src.screens.MainScreen import create_screen as main_screen
from FrontendService.src.screens.PersonSelection import create_screen as person_selection
from FrontendService.src.screens.NewPerson import create_screen as new_person
from FrontendService.src.screens.NewBank import create_screen as new_bank
from FrontendService.src.screens.PersonInfo import create_screen as person_info
from FrontendService.src.screens.BankAssignment import create_screen as bank_assignment
from FrontendService.src.screens.FreibetragInput import create_screen as freibetrag_input
from FrontendService.src.screens.FreibetragDisplay import create_screen as freibetrag_display
from FrontendService.src.screens.AccountAddition import create_screen as account_addition
from FrontendService.src.screens.AccountOverview import create_screen as account_overview
from FrontendService.src.screens.AccountSummary import create_screen as account_summary
from FrontendService.src.screens.AccountEditing import create_screen as account_editing

# Die inneren Screens:
from FrontendService.src.screens.accountsummaryinnerScreens.PieChartScreen import create_screen as create_pie_chart
from FrontendService.src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyse import create_screen as create_depo_analyse


class Navigator:
    def __init__(self, app):
        self.app = app
        self.state = AppState()
        self.state.load_all()
        self.routes = {
            "MainScreen": main_screen,
            "PersonSelection": person_selection,
            "NewPerson": new_person,
            "NewBank": new_bank,
            "PersonInfo": person_info,
            "BankAssignment": bank_assignment,
            "FreibetragInput": freibetrag_input,
            "FreibetragDisplay": freibetrag_display,
            "AccountAddition": account_addition,
            "AccountOverview": account_overview,
            "AccountSummary": account_summary,
            "AccountEditing": account_editing,
            # Übersicht: Tortendiagramm aller Konten
            "PieChart": create_pie_chart,
            # Parent-Screen für Depot-Detail + Aktien-Analyse
            "DepoAnalyse": create_depo_analyse,
        }

    def navigate(self, screen_name, **kwargs):
        if screen_name not in self.routes:
            print(f"Screen '{screen_name}' nicht gefunden.")
            return
        # app, navigator, state plus beliebige kwargs
        self.routes[screen_name](self.app, self, self.state, **kwargs)
