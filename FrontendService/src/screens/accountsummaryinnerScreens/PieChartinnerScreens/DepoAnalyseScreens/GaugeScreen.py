import logging

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from finanzuebersicht_shared import get_settings
from src.helpers.UniversalMethoden import clear_ui
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.analysis_api_client import AnalysisApiClient

logger = logging.getLogger(__name__)
settings = get_settings()


def _to_percent(value):
    try:
        if value is None:
            return None
        val = float(value)
        if val <= 1:
            val *= 100
        return max(0.0, min(100.0, val))
    except (TypeError, ValueError):
        return None


def create_screen(parent, title: str, isin: str, metric_getter=None, client: AnalysisApiClient | None = None):
    """Gauge wird nur angezeigt, wenn echte numerische Kennzahl vorhanden ist."""
    logger.debug("GaugeScreen: Initialisiere '%s' für ISIN '%s'", title, isin)
    clear_ui(parent)

    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=5, pady=5)
    ctk.CTkLabel(frame, text=title, font=("Arial", 14, "bold")).pack(pady=(0, 5))

    analysis_client = client or AnalysisApiClient(settings.marketdata_base_url)
    data, warnings = analysis_client.load_company_analysis(isin)

    metric_value = metric_getter(data) if callable(metric_getter) else None
    pct = _to_percent(metric_value)
    if pct is None:
        ctk.CTkLabel(
            frame,
            text="Kein geeigneter numerischer Wert für Gauge verfügbar.",
            text_color="gray70",
        ).pack(pady=10)
        if warnings:
            ctk.CTkLabel(frame, text="Hinweise: " + " | ".join(warnings), text_color="#ffb347").pack(anchor="w")
        return frame

    fig = Figure(figsize=(2, 2), dpi=100)
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_offset(3.14)
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.set_ylim(0, 100)
    ax.barh(0, pct, height=1.0, color="#3b8ed0")
    ax.text(0, 0, f"{pct:.1f}%", ha="center", va="center", fontsize=16)

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    if warnings:
        ctk.CTkLabel(frame, text="Hinweise: " + " | ".join(warnings), text_color="#ffb347").pack(anchor="w", pady=(6, 0))

    return frame
