import logging
import customtkinter as ctk

from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.DepotPositionPieScreen import (
    create_screen as create_depot_pie
)
from src.helpers.UniversalMethoden import clear_ui
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.TableScreen import create_screen as create_table_screen
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.ChartScreen  import create_screen as create_chart_screen
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.GaugeScreen  import create_screen as create_gauge_screen
from shared_config import get_settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
settings = get_settings()

def create_screen(app, navigator, state, depot_index: int = 0, **kwargs):
    """
    Leimwand-Screen:
     1) Oben: Depot-Aufteilung (immer sichtbar)
     2) Unten: Table, Chart, Gauges erst nach Auswahl
    """
    logger.debug("DepoAnalyse: Baue Haupt-Screen auf für Depot %s", depot_index)
    clear_ui(app)
    logger.debug("DepoAnalyse: Ausgewählte Person: %s", state.selected_person)

    # --- Grid: zwei Zeilen, drei Spalten ---
    app.grid_rowconfigure(0, weight=1)
    app.grid_rowconfigure(1, weight=3)
    app.grid_columnconfigure(0, weight=1)
    app.grid_columnconfigure(1, weight=2)
    app.grid_columnconfigure(2, weight=1)

    # --- 1) PieChart immer anzeigen ---
    top_frame = ctk.CTkFrame(app, fg_color="transparent")
    top_frame.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)
    logger.debug("DepoAnalyse: Top-Frame für PieChart erstellt")

    # --- 2) Content-Frame leer ---
    content_frame = ctk.CTkFrame(app, fg_color="transparent")
    content_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)
    content_frame.grid_columnconfigure((0,1,2), weight=1)
    content_frame.grid_rowconfigure(0, weight=1)
    logger.debug("DepoAnalyse: Leer-Content-Frame angelegt")

    # Callback für Auswahl im PieChart
    def on_stock_selected(ev):
        sel_isin = ev.get("isin")
        logger.debug("DepoAnalyse: Aktie ausgewählt ISIN=%s", sel_isin)
        clear_ui(content_frame)

        # --- TableScreen ---
        left = ctk.CTkFrame(content_frame, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        logger.debug("DepoAnalyse: Erstelle TableScreen für ISIN %s", sel_isin)
        create_table_screen(left, api_endpoint=f"{settings.marketdata_base_url}/stock/{sel_isin}")

        # --- ChartScreen (Aktienhistorie) ---
        mid = ctk.CTkFrame(content_frame, fg_color="transparent")
        mid.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        logger.debug("DepoAnalyse: Erstelle ChartScreen für Aktie %s", sel_isin)
        create_chart_screen(mid, api_endpoint=f"{settings.marketdata_base_url}/stock/{sel_isin}")

        # --- Gauges ---
        right = ctk.CTkFrame(content_frame, fg_color="transparent")
        right.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure((0,1,2), weight=1)

        backend = settings.marketdata_base_url
        gauges = [
            ("MsciWorld", f"{backend}/stock/{sel_isin}?etf=msciworld"),
            ("Volatilität", f"{backend}/volatility?isin={sel_isin}"),
            ("Sharpe Ratio", f"{backend}/sharpe?isin={sel_isin}")
        ]

        # Klick auf Gauge lädt neues Chart in der Mitte nach
        for i, (title, endpoint) in enumerate(gauges):
            logger.debug("DepoAnalyse: Gauge '%s' Endpoint='%s'", title, endpoint)
            cont = ctk.CTkFrame(right, fg_color="transparent")
            cont.grid(row=i, column=0, sticky="nsew", pady=5)

            def make_click_cb(ep):
                return lambda *_: create_chart_screen(mid, api_endpoint=ep)

            create_gauge_screen(
                cont,
                title=title,
                api_endpoint=endpoint,
                click_callback=make_click_cb(endpoint)
            )

    # PieChart erstellen mit Callback
    create_depot_pie(
        top_frame,
        navigator,
        state,
        depot_index=depot_index,
        pick_callback=on_stock_selected
    )
