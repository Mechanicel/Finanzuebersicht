import logging
from typing import Any

import customtkinter as ctk

from finanzuebersicht_shared import get_settings
from src.helpers.UniversalMethoden import clear_ui
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.analysis_api_client import AnalysisApiClient

logger = logging.getLogger(__name__)
settings = get_settings()


CORE_SECTION_KEYS = ["instrument", "market", "profile"]
RAW_PRIORITY_KEYS = [
    "metrics",
    "risk",
    "benchmark",
    "fundamentals",
    "valuation",
    "quality",
    "growth",
    "financials",
    "timeseries",
    "meta",
]


def _format_scalar(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, float):
        return f"{value:,.2f}".replace(",", " ")
    return str(value)


def _flatten_payload(payload: Any, prefix: str = "") -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []

    if isinstance(payload, dict):
        for key, value in payload.items():
            label = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(_flatten_payload(value, label))
        return rows

    if isinstance(payload, list):
        for index, entry in enumerate(payload):
            label = f"{prefix}[{index}]" if prefix else f"[{index}]"
            rows.extend(_flatten_payload(entry, label))
        return rows

    value = _format_scalar(payload)
    if value is not None:
        rows.append((prefix or "value", value))
    return rows


def _render_section(parent, title: str, payload: Any) -> bool:
    rows = _flatten_payload(payload)
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


def _raw_sections(data: dict[str, Any]) -> list[tuple[str, Any]]:
    sections: list[tuple[str, Any]] = []
    seen = set()

    for key in RAW_PRIORITY_KEYS:
        if key in data:
            sections.append((key.replace("_", " ").title(), data.get(key)))
            seen.add(key)

    for key, value in data.items():
        if key in seen or key in CORE_SECTION_KEYS:
            continue
        sections.append((key.replace("_", " ").title(), value))
    return sections


def create_screen(
    parent,
    isin: str,
    client: AnalysisApiClient | None = None,
    payload: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    mode: str = "core",
):
    """Rendert eine Key-Value-Ansicht für Analyseblöcke."""
    logger.debug("TableScreen: Initialisiere für ISIN %s", isin)
    clear_ui(parent)

    container = ctk.CTkScrollableFrame(parent)
    container.pack(fill="both", expand=True, padx=10, pady=10)

    effective_warnings = list(warnings or [])
    analysis_payload = payload

    if analysis_payload is None:
        analysis_client = client or AnalysisApiClient(settings.marketdata_base_url)
        analysis_payload, fetched_warnings = analysis_client.load_company_analysis(isin)
        effective_warnings.extend(fetched_warnings)

    data = analysis_payload or {}

    if effective_warnings and not data:
        ctk.CTkLabel(container, text="Fehler beim Laden der Analyse", text_color="red", font=(None, 14)).pack(pady=20)
        ctk.CTkLabel(container, text="\n".join(effective_warnings), text_color="#ffb347", justify="left").pack(anchor="w", padx=8)
        return

    if mode not in {"core", "raw"}:
        mode = "core"

    if mode == "core":
        sections = [
            ("Instrument", data.get("instrument")),
            ("Market", data.get("market")),
            ("Profile", data.get("profile")),
        ]
    else:
        sections = _raw_sections(data)

    visible_sections = sum(_render_section(container, title, section_payload) for title, section_payload in sections)

    if visible_sections == 0:
        ctk.CTkLabel(container, text="Keine Analyseblöcke vorhanden", font=(None, 14)).pack(pady=20)

    if effective_warnings:
        ctk.CTkLabel(container, text="Hinweise: " + " | ".join(effective_warnings), text_color="#ffb347").pack(anchor="w", pady=(8, 0), padx=8)
