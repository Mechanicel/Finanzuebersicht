import importlib
import logging
from typing import Callable, Dict

from src.models.AppState import AppState

logger = logging.getLogger(__name__)

RouteFactory = Callable[..., None]


class Navigator:
    def __init__(self, app):
        logger.debug("Navigator: Initialisierung gestartet")
        self.app = app
        self.state = AppState()
        self.state.load_all()
        self.routes: Dict[str, str] = {
            "MainScreen": "src.screens.MainScreen:create_screen",
            "PersonSelection": "src.screens.PersonSelection:create_screen",
            "NewPerson": "src.screens.NewPerson:create_screen",
            "NewBank": "src.screens.NewBank:create_screen",
            "PersonInfo": "src.screens.PersonInfo:create_screen",
            "BankAssignment": "src.screens.BankAssignment:create_screen",
            "FreibetragInput": "src.screens.FreibetragInput:create_screen",
            "FreibetragDisplay": "src.screens.FreibetragDisplay:create_screen",
            "AccountAddition": "src.screens.AccountAddition:create_screen",
            "AccountOverview": "src.screens.AccountOverview:create_screen",
            "AccountSummary": "src.screens.AccountSummary:create_screen",
            "AccountEditing": "src.screens.AccountEditing:create_screen",
            "PieChart": "src.screens.accountsummaryinnerScreens.PieChartScreen:create_screen",
            "DepoAnalyse": "src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyse:create_screen",
        }
        logger.debug("Navigator: Initialisierung abgeschlossen")

    def _resolve_route(self, screen_name: str) -> RouteFactory:
        route_definition = self.routes[screen_name]
        module_path, function_name = route_definition.split(":", maxsplit=1)
        logger.debug("Navigator: lade Route %s aus %s", screen_name, module_path)
        module = importlib.import_module(module_path)
        return getattr(module, function_name)

    def navigate(self, screen_name, **kwargs):
        if screen_name not in self.routes:
            logger.error("Navigator.navigate: Screen '%s' nicht gefunden", screen_name)
            return
        logger.debug("Navigator.navigate: -> %s", screen_name)
        screen_factory = self._resolve_route(screen_name)
        screen_factory(self.app, self, self.state, **kwargs)
