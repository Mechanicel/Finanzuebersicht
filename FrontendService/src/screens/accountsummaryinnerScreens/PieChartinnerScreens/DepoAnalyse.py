import logging

import customtkinter as ctk

from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.DepotPositionPieScreen import (
    create_screen as create_depot_pie,
)
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.TableScreen import create_screen as create_table_screen
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.ChartScreen import create_screen as create_chart_screen
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.GaugeScreen import create_screen as create_gauge_screen
from src.ui.components import create_page, section_card, empty_state
from finanzuebersicht_shared import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def create_screen(app, navigator, state, depot_index: int = 0, **kwargs):
    ui = create_page(app, "Depot-Analyse", "Interaktive Detailanalyse einzelner Depotpositionen", back_command=lambda: navigator.navigate("AccountSummary", selected_tab="piechart"))

    _, top_body = section_card(ui["content"], "Depot-Aufteilung", "Klicken Sie auf ein Segment, um Details zu laden.")
    _, content_body = section_card(ui["content"], "Detailansicht")

    layout = ctk.CTkFrame(content_body, fg_color="transparent")
    layout.pack(fill="both", expand=True)
    layout.grid_columnconfigure(0, weight=1)
    layout.grid_columnconfigure(1, weight=2)
    layout.grid_columnconfigure(2, weight=1)
    layout.grid_rowconfigure(0, weight=1)

    placeholder = ctk.CTkLabel(
        content_body,
        text="Bitte oben eine Depotposition auswählen, um Tabelle, Chart und Gauges zu sehen.",
        text_color="gray70",
    )
    placeholder.pack(fill="x", pady=(8, 0))

    def on_stock_selected(ev):
        sel_isin = ev.get("isin")
        logger.debug("DepoAnalyse: Aktie ausgewählt ISIN=%s", sel_isin)
        for w in layout.winfo_children():
            w.destroy()
        placeholder.pack_forget()

        left = ctk.CTkFrame(layout, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        create_table_screen(left, api_endpoint=f"{settings.marketdata_base_url}/stock/{sel_isin}")

        mid = ctk.CTkFrame(layout, fg_color="transparent")
        mid.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        create_chart_screen(mid, api_endpoint=f"{settings.marketdata_base_url}/stock/{sel_isin}")

        right = ctk.CTkFrame(layout, fg_color="transparent")
        right.grid(row=0, column=2, sticky="nsew", padx=8, pady=8)
        right.grid_columnconfigure(0, weight=1)

        backend = settings.marketdata_base_url
        gauges = [
            ("MsciWorld", f"{backend}/stock/{sel_isin}?etf=msciworld"),
            ("Volatilität", f"{backend}/volatility?isin={sel_isin}"),
            ("Sharpe Ratio", f"{backend}/sharpe?isin={sel_isin}"),
        ]

        for i, (title, endpoint) in enumerate(gauges):
            cont = ctk.CTkFrame(right, fg_color="transparent")
            cont.grid(row=i, column=0, sticky="nsew", pady=4)
            create_gauge_screen(cont, title=title, api_endpoint=endpoint, click_callback=(lambda ep=endpoint: create_chart_screen(mid, api_endpoint=ep)))

    create_depot_pie(top_body, navigator, state, depot_index=depot_index, pick_callback=on_stock_selected)
