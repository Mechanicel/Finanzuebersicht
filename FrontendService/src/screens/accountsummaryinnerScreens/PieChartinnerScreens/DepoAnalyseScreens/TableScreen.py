import logging

import customtkinter as ctk

from finanzuebersicht_shared import get_settings
from src.helpers.UniversalMethoden import clear_ui
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.analysis_api_client import AnalysisApiClient

logger = logging.getLogger(__name__)
settings = get_settings()


def _format_value(value):
    if value in (None, ""):
        return None
    if isinstance(value, float):
        return f"{value:,.2f}".replace(",", " ")
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if v not in (None, "")) or None
    return str(value)


def _render_kv_section(parent, title: str, payload: dict):
    if not isinstance(payload, dict):
        return False

    rows = [(k, _format_value(v)) for k, v in payload.items()]
    rows = [(k, v) for k, v in rows if v is not None]
    if not rows:
        return False

    box = ctk.CTkFrame(parent, corner_radius=10)
    box.pack(fill="x", pady=(0, 12))
    box.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(box, text=title, font=(None, 13, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5)
    )
    for i, (key, value) in enumerate(rows, start=1):
        ctk.CTkLabel(box, text=f"{key}:", font=(None, 12, "bold")).grid(
            row=i, column=0, sticky="nw", padx=(10, 6), pady=4
        )
        ctk.CTkLabel(box, text=value, font=(None, 12), justify="left", wraplength=900).grid(
            row=i, column=1, sticky="nw", padx=(0, 10), pady=4
        )

    return True


def create_screen(parent, isin: str, client: AnalysisApiClient | None = None):
    """Rendert eine saubere Key-Value-Ansicht für instrument/market/profile."""
    logger.debug("TableScreen: Initialisiere für ISIN %s", isin)
    clear_ui(parent)

    container = ctk.CTkScrollableFrame(parent)
    container.pack(fill="both", expand=True, padx=20, pady=20)

    analysis_client = client or AnalysisApiClient(settings.marketdata_base_url)
    data, warnings = analysis_client.load_company_analysis(isin)

    if warnings and not data:
        ctk.CTkLabel(container, text="Fehler beim Laden der Analyse", text_color="red", font=(None, 14)).pack(pady=20)
        ctk.CTkLabel(container, text="\n".join(warnings), text_color="#ffb347", justify="left").pack(anchor="w", padx=8)
        return

    visible_sections = 0
    visible_sections += _render_kv_section(container, "Instrument", data.get("instrument", {}))
    visible_sections += _render_kv_section(container, "Market", data.get("market", {}))
    visible_sections += _render_kv_section(container, "Profile", data.get("profile", {}))

    if visible_sections == 0:
        ctk.CTkLabel(container, text="Keine Analyseblöcke (instrument/market/profile) vorhanden", font=(None, 14)).pack(pady=20)

    if warnings:
        ctk.CTkLabel(container, text="Hinweise: " + " | ".join(warnings), text_color="#ffb347").pack(anchor="w", pady=(8, 0), padx=8)
