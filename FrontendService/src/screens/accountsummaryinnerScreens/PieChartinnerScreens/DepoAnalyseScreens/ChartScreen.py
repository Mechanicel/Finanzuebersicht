import logging
from datetime import datetime
from typing import Any

import customtkinter as ctk
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from finanzuebersicht_shared import get_settings
from src.helpers.UniversalMethoden import clear_ui
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.analysis_api_client import AnalysisApiClient

logger = logging.getLogger(__name__)
settings = get_settings()

SERIES_LABELS = {
    "price": "Price",
    "benchmark_price": "Benchmark",
    "returns": "Returns",
    "drawdown": "Drawdown",
    "benchmark_relative": "Relative Spread",
}


def _to_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_points(entries: Any, value_key: str, field_name: str) -> list[tuple[datetime, float]]:
    if not isinstance(entries, list):
        return []

    points: list[tuple[datetime, float]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        date_raw = entry.get("date")
        value = _to_float(entry.get(field_name))
        if date_raw and value is None and value_key != field_name:
            value = _to_float(entry.get(value_key))
        if not date_raw or value is None:
            continue
        try:
            points.append((datetime.fromisoformat(str(date_raw)), value))
        except ValueError:
            continue

    return sorted(points, key=lambda x: x[0])


def _extract_timeseries_api_series(payload: dict[str, Any]) -> dict[str, list[tuple[datetime, float]]]:
    series = payload.get("series", {}) if isinstance(payload, dict) else {}
    if not isinstance(series, dict):
        return {}

    return {
        "price": _parse_points(series.get("price"), "close", "close"),
        "benchmark_price": _parse_points(series.get("benchmark_price"), "close", "close"),
        "returns": _parse_points(series.get("returns"), "value", "value"),
        "drawdown": _parse_points(series.get("drawdown"), "value", "value"),
        "benchmark_relative": _parse_points(series.get("benchmark_relative"), "relative_spread", "relative_spread"),
    }


def create_screen(
    parent,
    isin: str,
    client: AnalysisApiClient | None = None,
    payload: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    selected_series: list[str] | None = None,
    benchmark: str | None = None,
    comparison_payload: dict[str, Any] | None = None,
):
    """Rendert Kurs-/Performance-Verläufe aus dem /timeseries-Endpoint."""
    logger.debug("ChartScreen: Initialisiere für ISIN %s", isin)
    clear_ui(parent)

    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=4, pady=4)

    effective_warnings = list(warnings or [])
    data = payload

    if data is None:
        analysis_client = client or AnalysisApiClient(settings.marketdata_base_url)
        query_series = selected_series or ["price", "returns", "drawdown", "benchmark_relative", "benchmark_price"]
        data, fetch_error = analysis_client.load_timeseries(isin, series=",".join(query_series), benchmark=benchmark)
        if fetch_error:
            effective_warnings.append(fetch_error)

    series_map = _extract_timeseries_api_series(data or {})
    comparison_series: list[tuple[str, list[tuple[datetime, float]]]] = []
    comparisons = (comparison_payload or {}).get("comparisons") if isinstance(comparison_payload, dict) else []
    if isinstance(comparisons, list):
        for item in comparisons:
            if not isinstance(item, dict):
                continue
            points = _parse_points(item.get("series"), "close", "close")
            if not points:
                continue
            label = str(item.get("name") or item.get("symbol") or "Vergleich")
            comparison_series.append((label, points))
    meta = (comparison_payload or {}).get("meta") if isinstance(comparison_payload, dict) else {}
    if isinstance(meta, dict):
        for warning in meta.get("warnings") or []:
            if isinstance(warning, str) and warning.strip():
                effective_warnings.append(warning)
    selected = selected_series or ["price", "returns", "drawdown", "benchmark_relative", "benchmark_price"]
    visible_keys = [key for key in selected if key in series_map]

    if not visible_keys:
        ctk.CTkLabel(frame, text="Keine Serie ausgewählt.", justify="left").pack(pady=20)
        return

    visible_series = {key: series_map.get(key) or [] for key in visible_keys}
    if not any(visible_series.values()):
        ctk.CTkLabel(frame, text="Keine Zeitreihendaten für die gewählten Serien vorhanden.", justify="left").pack(pady=20)
        if effective_warnings:
            ctk.CTkLabel(frame, text="Hinweise: " + " | ".join(effective_warnings), text_color="#ffb347").pack(anchor="w")
        return

    lower_series = [k for k in visible_keys if k in {"returns", "drawdown", "benchmark_relative"}]
    fig = Figure(figsize=(7, 4.3 if lower_series else 3), dpi=100)

    if lower_series:
        ax_price = fig.add_subplot(211)
        ax_metric = fig.add_subplot(212, sharex=ax_price)
    else:
        ax_price = fig.add_subplot(111)
        ax_metric = None

    for key in ("price", "benchmark_price"):
        points = visible_series.get(key) or []
        if points:
            ax_price.plot([p[0] for p in points], [p[1] for p in points], label=SERIES_LABELS.get(key, key))
    for label, points in comparison_series:
        ax_price.plot([p[0] for p in points], [p[1] for p in points], label=label, alpha=0.85, linewidth=1.6)

    ax_price.grid(alpha=0.3)
    ax_price.set_ylabel("Preis")
    ax_price.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax_price.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax_price.xaxis.get_major_locator()))
    if any(visible_series.get(k) for k in ("price", "benchmark_price")) or comparison_series:
        ax_price.legend(loc="best")

    if ax_metric is not None:
        for key in lower_series:
            points = visible_series.get(key) or []
            if points:
                ax_metric.plot([p[0] for p in points], [p[1] for p in points], label=SERIES_LABELS.get(key, key))
        ax_metric.grid(alpha=0.3)
        ax_metric.set_xlabel("Datum")
        ax_metric.set_ylabel("Wert")
        ax_metric.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax_metric.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax_metric.xaxis.get_major_locator()))
        ax_metric.legend(loc="best")
    else:
        ax_price.set_xlabel("Datum")

    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    if effective_warnings:
        ctk.CTkLabel(frame, text="Hinweise: " + " | ".join(effective_warnings), text_color="#ffb347").pack(anchor="w", pady=(8, 0))
