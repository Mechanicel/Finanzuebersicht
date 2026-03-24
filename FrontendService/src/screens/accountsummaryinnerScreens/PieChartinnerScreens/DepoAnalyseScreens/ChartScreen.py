import logging
from datetime import datetime

import customtkinter as ctk
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from finanzuebersicht_shared import get_settings
from src.helpers.UniversalMethoden import clear_ui
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.analysis_api_client import AnalysisApiClient

logger = logging.getLogger(__name__)
settings = get_settings()


def _to_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_price_history(payload: dict) -> list[tuple[datetime, float]]:
    timeseries = payload.get("timeseries", {}) if isinstance(payload, dict) else {}
    history = timeseries.get("price_history") if isinstance(timeseries, dict) else None
    if not isinstance(history, list):
        return []

    points: list[tuple[datetime, float]] = []
    for entry in history:
        if not isinstance(entry, dict):
            continue
        date_raw = entry.get("date")
        close = _to_float(entry.get("close"))
        if not date_raw or close is None:
            continue
        try:
            points.append((datetime.fromisoformat(str(date_raw)), close))
        except ValueError:
            continue

    return sorted(points, key=lambda x: x[0])


def create_screen(parent, isin: str, client: AnalysisApiClient | None = None):
    """Rendert den Kursverlauf ausschließlich aus timeseries.price_history."""
    logger.debug("ChartScreen: Initialisiere für ISIN %s", isin)
    clear_ui(parent)

    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    ctk.CTkLabel(frame, text="Historische Entwicklung", font=(None, 16, "bold")).pack(pady=(0, 8))

    analysis_client = client or AnalysisApiClient(settings.marketdata_base_url)
    data, warnings = analysis_client.load_company_analysis(isin)
    points = _extract_price_history(data)

    if not points:
        ctk.CTkLabel(
            frame,
            text="Keine Zeitreihe verfügbar (timeseries.price_history fehlt oder ist leer).",
            justify="left",
        ).pack(pady=20)
        if warnings:
            ctk.CTkLabel(frame, text="Hinweise: " + " | ".join(warnings), text_color="#ffb347").pack(anchor="w")
        return

    fig = Figure(figsize=(6, 3), dpi=100)
    ax = fig.add_subplot(111)
    dates = [p[0] for p in points]
    values = [p[1] for p in points]
    ax.plot(dates, values, label="Close")
    ax.grid(alpha=0.3)
    ax.set_xlabel("Datum")
    ax.set_ylabel("Preis")
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
    ax.legend(loc="best")

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    if warnings:
        ctk.CTkLabel(frame, text="Hinweise: " + " | ".join(warnings), text_color="#ffb347").pack(anchor="w", pady=(8, 0))
