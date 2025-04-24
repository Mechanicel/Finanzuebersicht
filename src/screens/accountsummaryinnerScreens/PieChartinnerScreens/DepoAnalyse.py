# src/screens/accountsummaryinnerScreens/PieChartinnerScreens/DepoAnalyseScreens/DepoAnalyse.py

import customtkinter as ctk
from src.helpers.UniversalMethoden import clear_ui
from src.models import AppState
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.DepotPositionPieScreen import create_screen as create_depot_pie
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.AktienAnalyseScreen import create_screen as create_stock_analysis

def create_screen(app, navigator, state: AppState, depot_index: int = 0, **kwargs):
    clear_ui(app)

    # ← Zurück zu AccountSummary (Tortendiagramm)
    ctk.CTkButton(
        app,
        text="← Zurück",
        command=lambda: navigator.navigate("AccountSummary", selected_tab="piechart")
    ).grid(row=0, column=0, padx=20, pady=10, sticky="w")

    # Obere Hälfte: Depot-Positions-PieChart
    top_frame = ctk.CTkFrame(app, fg_color="transparent")
    top_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5,5))

    # Untere Hälfte: Platzhalter oder Aktien-Detail
    bot_frame = ctk.CTkFrame(app, fg_color="transparent")
    bot_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0,10))



    # Initialer Platzhalter unten
    ctk.CTkLabel(
        bot_frame,
        text="Keine Aktie ausgewählt",
        font=("Arial", 14)
    ).pack(expand=True)

    # Callback, der später unten den Aktien-Screen lädt
    def on_stock_selected(isin: str):
        clear_ui(bot_frame)
        create_stock_analysis(bot_frame, navigator, state, isin=isin)

    # Depot-PieChart laden und Klicks an on_stock_selected weiterleiten
    create_depot_pie(
        top_frame,
        navigator,
        state,
        depot_index=depot_index,
        pick_callback=on_stock_selected
    )
