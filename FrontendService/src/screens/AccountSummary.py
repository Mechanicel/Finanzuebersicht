import customtkinter as ctk

from src.models.AppState import AppState
from src.ui.components import create_page, section_card, set_status
from src.screens.accountsummaryinnerScreens.TimeSeriesScreen import create_screen as create_time_series
from src.screens.accountsummaryinnerScreens.PieChartScreen import create_screen as create_pie_chart
from src.screens.accountsummaryinnerScreens.MonthlyComparisonScreen import create_screen as create_monthly_comparison
from src.screens.accountsummaryinnerScreens.MetricsScreen import create_screen as create_metrics
from src.screens.accountsummaryinnerScreens.HeatmapScreen import create_screen as create_heatmap
from src.screens.accountsummaryinnerScreens.ForecastScreen import create_screen as create_forecast


def create_screen(app, navigator, state: AppState, selected_tab: str = None, **kwargs):
    person = state.selected_person
    subtitle = f"Analyse-Dashboard für {person['Name']} {person['Nachname']}" if person else "Analyse-Dashboard"
    ui = create_page(app, "Kontozusammenfassung", subtitle, back_command=lambda: navigator.navigate("PersonInfo"))

    tabs = [
        ("Zeitreihe", "timeseries", create_time_series),
        ("Tortendiagramm", "piechart", create_pie_chart),
        ("Monatsvergleich", "monthly", create_monthly_comparison),
        ("Kennzahlen", "metrics", create_metrics),
        ("Heatmap", "heatmap", create_heatmap),
        ("Forecast", "forecast", create_forecast),
    ]

    _, tab_body = section_card(ui["content"], "Ansicht wählen")
    tab_body.grid_columnconfigure(tuple(range(len(tabs))), weight=1)

    _, content_body = section_card(ui["content"], "Analyse")
    content_body.pack_propagate(False)
    content_body.configure(height=520)

    def load_screen(screen_func, label: str):
        for w in content_body.winfo_children():
            w.destroy()
        target = ctk.CTkFrame(content_body, fg_color="transparent")
        target.pack(fill="both", expand=True)
        screen_func(target, navigator, state)
        set_status(ui["status"], f"Aktive Ansicht: {label}", "info")

    for idx, (label, key, func) in enumerate(tabs):
        ctk.CTkButton(tab_body, text=label, height=38, command=lambda f=func, l=label: load_screen(f, l)).grid(
            row=0, column=idx, padx=4, pady=4, sticky="ew"
        )

    tab_map = {k: (label, fn) for label, k, fn in tabs}
    default_label, default_fn = tab_map.get((selected_tab or "").lower(), ("Zeitreihe", create_time_series))
    load_screen(default_fn, default_label)
