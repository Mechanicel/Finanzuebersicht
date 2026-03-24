import logging

import customtkinter as ctk

from finanzuebersicht_shared import get_settings
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.DepotPositionPieScreen import (
    create_screen as create_depot_pie,
)
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.TableScreen import (
    create_screen as create_table_screen,
)
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.ChartScreen import (
    create_screen as create_chart_screen,
)
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.analysis_api_client import AnalysisApiClient
from src.ui.components import create_page, empty_state, section_card

logger = logging.getLogger(__name__)
settings = get_settings()


def _to_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_number(value, digits: int = 2):
    val = _to_float(value)
    return "—" if val is None else f"{val:,.{digits}f}".replace(",", " ")


def _fmt_currency(value, currency: str = "EUR", digits: int = 2):
    val = _to_float(value)
    return "—" if val is None else f"{val:,.{digits}f} {currency}".replace(",", " ")


def _display_value(value):
    if value in (None, ""):
        return "—"
    return str(value)


def _render_snapshot(parent, isin: str, data: dict):
    instrument = data.get("instrument", {}) if isinstance(data.get("instrument"), dict) else {}
    market = data.get("market", {}) if isinstance(data.get("market"), dict) else {}
    profile = data.get("profile", {}) if isinstance(data.get("profile"), dict) else {}

    header, body = section_card(parent, "Header / Snapshot")
    body.grid_columnconfigure((0, 1), weight=1)

    name = instrument.get("long_name") or instrument.get("short_name") or instrument.get("symbol") or isin
    ctk.CTkLabel(body, text=name, font=("Arial", 23, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
    ctk.CTkLabel(
        body,
        text=(
            f"Symbol: {_display_value(instrument.get('symbol'))}   |   "
            f"ISIN: {_display_value(instrument.get('isin') or isin)}"
        ),
        text_color="gray70",
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 8))

    currency = market.get("currency") or instrument.get("currency") or "EUR"
    summary_items = [
        ("Aktueller Kurs", _fmt_currency(market.get("currentPrice"), currency)),
        ("Marktkapitalisierung", _fmt_currency(market.get("marketCap"), currency, 0)),
        ("Ø Volumen", _fmt_number(market.get("averageVolume"), 0)),
        ("Sektor", _display_value(profile.get("sector"))),
        ("Branche", _display_value(profile.get("industry"))),
        ("Land", _display_value(profile.get("country"))),
        ("Website", _display_value(profile.get("website"))),
    ]

    grid = ctk.CTkFrame(body, fg_color="transparent")
    grid.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 8))
    for col in range(2):
        grid.grid_columnconfigure(col, weight=1)

    for idx, (label, value) in enumerate(summary_items):
        card = ctk.CTkFrame(grid, corner_radius=10)
        card.grid(row=idx // 2, column=idx % 2, padx=6, pady=6, sticky="ew")
        ctk.CTkLabel(card, text=label, text_color="gray70", font=("Arial", 11)).pack(anchor="w", padx=10, pady=(8, 0))
        ctk.CTkLabel(card, text=value, font=("Arial", 16, "bold"), justify="left", wraplength=480).pack(
            anchor="w", padx=10, pady=(2, 8)
        )

    profile_card, profile_body = section_card(body, "Business Summary")
    profile_card.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
    ctk.CTkLabel(
        profile_body,
        text=_display_value(profile.get("business_summary")),
        justify="left",
        wraplength=1000,
        text_color="gray80",
    ).pack(anchor="w")


def create_screen(app, navigator, state, depot_index: int = 0, **kwargs):
    ui = create_page(
        app,
        "Depot-Analyse",
        "Analyse-Workspace für Unternehmens- und Wertpapierdaten",
        back_command=lambda: navigator.navigate("AccountSummary", selected_tab="piechart"),
        scrollable=True,
    )
    client = AnalysisApiClient(settings.marketdata_base_url)

    _, top_body = section_card(ui["content"], "Depot-Aufteilung", "Klicken Sie auf eine Position, um den Workspace zu laden.")
    _, workspace_body = section_card(ui["content"], "Analyse-Workspace")

    empty_state(workspace_body, "Bitte oben eine Position auswählen.")

    def _render_workspace(isin: str):
        for widget in workspace_body.winfo_children():
            widget.destroy()

        payload, warnings = client.load_company_analysis(isin)
        if not payload:
            msg = "Analyse konnte nicht geladen werden."
            if warnings:
                msg = f"{msg} {' | '.join(warnings)}"
            empty_state(workspace_body, msg)
            return

        has_core_data = any(
            isinstance(payload.get(block), dict) and bool(payload.get(block))
            for block in ("instrument", "market", "profile")
        )
        if not has_core_data:
            empty_state(workspace_body, "Keine verwertbaren Analyseblöcke vorhanden (instrument/market/profile fehlen).")
            return

        _render_snapshot(workspace_body, isin, payload)

        data_section, data_body = section_card(workspace_body, "Datenübersicht")
        data_section.pack(fill="x", expand=False, pady=(8, 8))
        create_table_screen(data_body, isin=isin, client=client)

        chart_section, chart_body = section_card(workspace_body, "Chart")
        chart_section.pack(fill="both", expand=True, pady=(8, 0))
        create_chart_screen(chart_body, isin=isin, client=client)

        if warnings:
            ctk.CTkLabel(workspace_body, text="Hinweise: " + " | ".join(warnings), text_color="#ffb347").pack(
                anchor="w", pady=(8, 0)
            )

    def on_stock_selected(ev):
        sel_isin = ev.get("isin")
        logger.debug("DepoAnalyse: Instrument ausgewählt ISIN=%s", sel_isin)
        if not sel_isin:
            empty_state(workspace_body, "Ungültige Auswahl: keine ISIN")
            return
        _render_workspace(sel_isin)

    create_depot_pie(top_body, navigator, state, depot_index=depot_index, pick_callback=on_stock_selected)
