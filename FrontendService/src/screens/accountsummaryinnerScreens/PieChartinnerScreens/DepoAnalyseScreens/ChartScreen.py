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


def _extract_legacy_series(payload: dict[str, Any]) -> dict[str, list[tuple[datetime, float]]]:
    timeseries = payload.get("timeseries", {}) if isinstance(payload, dict) else {}
    history = timeseries.get("price_history") if isinstance(timeseries, dict) else None
    return {"price": _parse_points(history, "close", "close")}


def _extract_timeseries_api_series(payload: dict[str, Any]) -> dict[str, list[tuple[datetime, float]]]:
    series = payload.get("series", {}) if isinstance(payload, dict) else {}
    if not isinstance(series, dict):
        return {}

    return {
        "price": _parse_points(series.get("price"), "close", "close"),
        "benchmark_price": _parse_points(series.get("benchmark_price"), "close", "close"),
        "returns": _parse_points(series.get("returns"), "value", "value"),
        "drawdown": _parse_points(series.get("drawdown"), "value", "value"),
        "relative_spread": _parse_points(series.get("benchmark_relative"), "relative_spread", "relative_spread"),
    }


def create_screen(
    parent,
    isin: str,
    client: AnalysisApiClient | None = None,
    payload: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    chart_mode: str = "legacy",
):
    """Rendert Kurs-/Performance-Verläufe für legacy oder timeseries API."""
    logger.debug("ChartScreen: Initialisiere für ISIN %s", isin)
    clear_ui(parent)

    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    ctk.CTkLabel(frame, text="Historische Entwicklung", font=(None, 16, "bold")).pack(pady=(0, 8))

    effective_warnings = list(warnings or [])
    data = payload

    if data is None:
        analysis_client = client or AnalysisApiClient(settings.marketdata_base_url)
        if chart_mode == "timeseries":
            data, fetch_error = analysis_client.load_timeseries(
                isin,
                series="price,returns,drawdown,benchmark_relative,benchmark_price",
            )
            if fetch_error:
                effective_warnings.append(fetch_error)
        else:
            data, fetch_warnings = analysis_client.load_company_analysis(isin)
            effective_warnings.extend(fetch_warnings)

    if chart_mode == "timeseries":
        series_map = _extract_timeseries_api_series(data or {})
    else:
        series_map = _extract_legacy_series(data or {})

    price_points = series_map.get("price") or []
    benchmark_points = series_map.get("benchmark_price") or []
    returns_points = series_map.get("returns") or []
    drawdown_points = series_map.get("drawdown") or []
    relative_points = series_map.get("relative_spread") or []

    if not any([price_points, benchmark_points, returns_points, drawdown_points, relative_points]):
        ctk.CTkLabel(
            frame,
            text="Keine Zeitreihe verfügbar (weder legacy timeseries.price_history noch /timeseries series).",
            justify="left",
        ).pack(pady=20)
        if effective_warnings:
            ctk.CTkLabel(frame, text="Hinweise: " + " | ".join(effective_warnings), text_color="#ffb347").pack(anchor="w")
        return

    has_secondary = any([returns_points, drawdown_points, relative_points])
    fig = Figure(figsize=(7, 4 if has_secondary else 3), dpi=100)
    if has_secondary:
        ax_price = fig.add_subplot(211)
        ax_metric = fig.add_subplot(212, sharex=ax_price)
    else:
        ax_price = fig.add_subplot(111)
        ax_metric = None

    if price_points:
        ax_price.plot([p[0] for p in price_points], [p[1] for p in price_points], label="Price")
    if benchmark_points:
        ax_price.plot([p[0] for p in benchmark_points], [p[1] for p in benchmark_points], label="Benchmark")

    ax_price.grid(alpha=0.3)
    ax_price.set_ylabel("Preis")
    ax_price.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax_price.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax_price.xaxis.get_major_locator()))
    ax_price.legend(loc="best")

    if ax_metric is not None:
        if returns_points:
            ax_metric.plot([p[0] for p in returns_points], [p[1] for p in returns_points], label="Returns")
        if drawdown_points:
            ax_metric.plot([p[0] for p in drawdown_points], [p[1] for p in drawdown_points], label="Drawdown")
        if relative_points:
            ax_metric.plot([p[0] for p in relative_points], [p[1] for p in relative_points], label="Relative Spread")
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
