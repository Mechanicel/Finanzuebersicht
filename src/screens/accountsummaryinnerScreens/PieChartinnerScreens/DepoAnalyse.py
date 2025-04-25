# src/screens/accountsummaryinnerScreens/PieChartinnerScreens/DepoAnalyseScreens/DepoAnalyse.py

import logging
import customtkinter as ctk
from src.helpers.UniversalMethoden import clear_ui
from src.models import AppState
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.DepotPositionPieScreen import (
    create_screen as create_depot_pie
)
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.AktienAnalyseScreen import (
    create_screen as create_stock_analysis
)

logger = logging.getLogger(__name__)

def create_screen(app, navigator, state: AppState, depot_index: int = 0, **kwargs):
    clear_ui(app)

    # ← Zurück
    ctk.CTkButton(
        app,
        text="← Zurück",
        command=lambda: navigator.navigate("AccountSummary", selected_tab="piechart")
    ).grid(row=0, column=0, padx=20, pady=10, sticky="w")

    # Obere Hälfte: PieChart über beide Spalten
    top_frame = ctk.CTkFrame(app, fg_color="transparent")
    top_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(5,5))

    # Untere Hälfte: links Detail, rechts Column-Selector
    bot_left  = ctk.CTkFrame(app, fg_color="transparent")
    bot_left.grid(row=2, column=0, sticky="nsew", padx=(10,5), pady=(0,10))
    bot_right = ctk.CTkFrame(app, fg_color="transparent")
    bot_right.grid(row=2, column=1, sticky="nsew", padx=(5,10), pady=(0,10))

    # Platzhalter links
    ctk.CTkLabel(bot_left, text="Keine Aktie ausgewählt", font=("Arial", 14)).pack(expand=True)

    # Callback: übergebe bot_left & bot_right
    def on_stock_selected(isin: str):
        clear_ui(bot_left)
        clear_ui(bot_right)
        create_stock_analysis(
            bot_left,
            navigator,
            state,
            isin=isin,
            column_frame=bot_right
        )

    # PieChart mit Callback
    create_depot_pie(
        top_frame,
        navigator,
        state,
        depot_index=depot_index,
        pick_callback=on_stock_selected
    )

    # Layout-Gewichte
    app.grid_rowconfigure(1, weight=3)
    app.grid_rowconfigure(2, weight=3)
    app.grid_columnconfigure(0, weight=3)
    app.grid_columnconfigure(1, weight=1)
