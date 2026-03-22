# src/screens/AccountSummary.py

import customtkinter as ctk
from FrontendService.src.helpers.UniversalMethoden import clear_ui, zentrieren
from FrontendService.src.models.AppState import AppState

from FrontendService.src.screens.accountsummaryinnerScreens.TimeSeriesScreen import create_screen as create_time_series
from FrontendService.src.screens.accountsummaryinnerScreens.PieChartScreen import create_screen as create_pie_chart
from FrontendService.src.screens.accountsummaryinnerScreens.MonthlyComparisonScreen import create_screen as create_monthly_comparison
from FrontendService.src.screens.accountsummaryinnerScreens.MetricsScreen import create_screen as create_metrics
from FrontendService.src.screens.accountsummaryinnerScreens.HeatmapScreen import create_screen as create_heatmap
from FrontendService.src.screens.accountsummaryinnerScreens.ForecastScreen import create_screen as create_forecast

def create_screen(app, navigator, state: AppState, selected_tab: str = None, **kwargs):
    # Root leeren
    clear_ui(app)

    # ← Zurück-Button
    ctk.CTkButton(
        app,
        text="← Zurück",
        command=lambda: navigator.navigate("PersonInfo")
    ).grid(row=0, column=0, padx=20, pady=10, sticky="w")

    # Button-Leiste
    btn_frame = ctk.CTkFrame(app, fg_color="transparent")
    btn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5,0))
    for i in range(6):
        btn_frame.grid_columnconfigure(i, weight=1)

    # Content-Container
    content_frame = ctk.CTkFrame(app)
    content_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

    # Inner Frame für dynamischen Content
    inner_frame = ctk.CTkFrame(content_frame)
    inner_frame.pack(fill="both", expand=True)

    # Funktion zum Laden eines Sub-Screens
    def load_screen(screen_func):
        clear_ui(inner_frame)
        screen_func(inner_frame, navigator, state)

    # Buttons für Auswertungen
    ctk.CTkButton(btn_frame, text="Zeitreihe",
        command=lambda: load_screen(create_time_series)
    ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
    ctk.CTkButton(btn_frame, text="Tortendiagramm",
        command=lambda: load_screen(create_pie_chart)
    ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    ctk.CTkButton(btn_frame, text="Monatsvergleich",
        command=lambda: load_screen(create_monthly_comparison)
    ).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
    ctk.CTkButton(btn_frame, text="Kennzahlen",
        command=lambda: load_screen(create_metrics)
    ).grid(row=0, column=3, padx=5, pady=5, sticky="ew")
    ctk.CTkButton(btn_frame, text="Heatmap",
        command=lambda: load_screen(create_heatmap)
    ).grid(row=0, column=4, padx=5, pady=5, sticky="ew")
    ctk.CTkButton(btn_frame, text="Forecast",
        command=lambda: load_screen(create_forecast)
    ).grid(row=0, column=5, padx=5, pady=5, sticky="ew")

    # Starte mit ausgewähltem Tab oder Zeitreihe
    tab_map = {
        "timeseries": create_time_series,
        "piechart":     create_pie_chart,
        "monthly":      create_monthly_comparison,
        "metrics":      create_metrics,
        "heatmap":      create_heatmap,
        "forecast":     create_forecast
    }
    func = tab_map.get((selected_tab or "").lower(), create_time_series)
    load_screen(func)

    # Zentrieren
    zentrieren(app)
