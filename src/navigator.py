# src/navigator.py

from src.models.AppState import AppState
from src.screens.MainScreen import create_screen as main_screen
from src.screens.PersonSelection import create_screen as person_selection
from src.screens.NewPerson import create_screen as new_person
from src.screens.NewBank import create_screen as new_bank
from src.screens.PersonInfo import create_screen as person_info
from src.screens.BankAssignment import create_screen as bank_assignment
from src.screens.FreibetragInput import create_screen as freibetrag_input
from src.screens.FreibetragDisplay import create_screen as freibetrag_display
from src.screens.AccountAddition import create_screen as account_addition
from src.screens.AccountOverview import create_screen as account_overview
from src.screens.AccountSummary import create_screen as account_summary
from src.screens.AccountEditing import create_screen as account_editing

# Die inneren Screens:
from src.screens.accountsummaryinnerScreens.PieChartScreen import create_screen as create_pie_chart
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyse import create_screen as create_depo_analyse
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.AktienAnalyseScreen import create_screen as create_stock_analysis

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
            # Screen für einzelne Aktie
            "AktienAnalyse": create_stock_analysis,
        }

    def navigate(self, screen_name, **kwargs):
        if screen_name not in self.routes:
            print(f"Screen '{screen_name}' nicht gefunden.")
            return
        # app, navigator, state plus beliebige kwargs
        self.routes[screen_name](self.app, self, self.state, **kwargs)
