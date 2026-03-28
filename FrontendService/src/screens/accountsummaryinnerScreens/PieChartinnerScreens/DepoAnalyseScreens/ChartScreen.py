import logging
from datetime import datetime, timedelta
from typing import Any

import customtkinter as ctk
import matplotlib.dates as mdates
from matplotlib.axes import Axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from finanzuebersicht_shared import get_settings
from src.helpers.UniversalMethoden import clear_ui
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.analysis_api_client import AnalysisApiClient
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.chart_interactions import (
    enable_timeseries_hover,
    open_chart_popout,
)

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


def _build_timeseries_figure(
    visible_series: dict[str, list[tuple[datetime, float]]],
    visible_keys: list[str],
    comparison_series: list[tuple[str, list[tuple[datetime, float]]]],
    figsize: tuple[float, float],
    linewidth: float = 1.7,
) -> tuple[Figure, list[Axes]]:
    lower_series = [k for k in visible_keys if k in {"returns", "drawdown", "benchmark_relative"}]
    fig = Figure(figsize=figsize, dpi=100)

    if lower_series:
        ax_price = fig.add_subplot(211)
        ax_metric = fig.add_subplot(212, sharex=ax_price)
        axes: list[Axes] = [ax_price, ax_metric]
    else:
        ax_price = fig.add_subplot(111)
        ax_metric = None
        axes = [ax_price]

    for key in ("price", "benchmark_price"):
        points = visible_series.get(key) or []
        if points:
            ax_price.plot(
                [p[0] for p in points],
                [p[1] for p in points],
                label=SERIES_LABELS.get(key, key),
                linewidth=linewidth,
            )
    for label, points in comparison_series:
        ax_price.plot(
            [p[0] for p in points],
            [p[1] for p in points],
            label=label,
            alpha=0.88,
            linewidth=max(1.4, linewidth - 0.1),
        )

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
                ax_metric.plot(
                    [p[0] for p in points],
                    [p[1] for p in points],
                    label=SERIES_LABELS.get(key, key),
                    linewidth=linewidth,
                )
        ax_metric.grid(alpha=0.3)
        ax_metric.set_xlabel("Datum")
        ax_metric.set_ylabel("Wert")
        ax_metric.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax_metric.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax_metric.xaxis.get_major_locator()))
        ax_metric.legend(loc="best")
    else:
        ax_price.set_xlabel("Datum")

    fig.tight_layout()
    return fig, axes


class TimeSeriesChartModule:
    PRESETS = [
        ("1M", 30),
        ("3M", 90),
        ("6M", 180),
        ("1J", 365),
        ("3J", 365 * 3),
        ("Max", None),
    ]

    def __init__(
        self,
        parent,
        isin: str,
        visible_keys: list[str],
        all_series: dict[str, list[tuple[datetime, float]]],
        comparison_series: list[tuple[str, list[tuple[datetime, float]]]],
    ):
        self.parent = parent
        self.isin = isin
        self.visible_keys = visible_keys
        self.all_series = all_series
        self.comparison_series = comparison_series

        self.canvas: FigureCanvasTkAgg | None = None
        self.axes: list[Axes] = []
        self.hover_ids: tuple[int, int, int] | None = None
        self.toolbar: NavigationToolbar2Tk | None = None
        self.date_error_var = ctk.StringVar(value="")

        min_date, max_date = self._compute_bounds()
        self.min_date = min_date
        self.max_date = max_date
        self.from_var = ctk.StringVar(value=self._fmt_date(min_date))
        self.to_var = ctk.StringVar(value=self._fmt_date(max_date))

        self._build_layout()
        self.update_chart()

    @staticmethod
    def _fmt_date(value: datetime | None) -> str:
        if not value:
            return ""
        return value.strftime("%Y-%m-%d")

    @staticmethod
    def _parse_date(value: str) -> datetime | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        try:
            return datetime.strptime(raw, "%Y-%m-%d")
        except ValueError:
            return None

    def _compute_bounds(self) -> tuple[datetime | None, datetime | None]:
        all_dates: list[datetime] = []
        for key in self.visible_keys:
            all_dates.extend([point[0] for point in self.all_series.get(key) or []])
        for _, series in self.comparison_series:
            all_dates.extend([point[0] for point in series])
        if not all_dates:
            return None, None
        return min(all_dates), max(all_dates)

    def _build_layout(self):
        actions_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        actions_frame.pack(fill="x", padx=2, pady=(0, 3))

        controls_frame = ctk.CTkFrame(actions_frame)
        controls_frame.pack(anchor="center", pady=(2, 2))

        ctk.CTkLabel(controls_frame, text="Von", font=("Arial", 13, "bold")).grid(row=0, column=0, padx=(10, 6), pady=10)
        from_entry = ctk.CTkEntry(controls_frame, textvariable=self.from_var, width=130, height=34)
        from_entry.grid(row=0, column=1, padx=(0, 14), pady=10)

        ctk.CTkLabel(controls_frame, text="Bis", font=("Arial", 13, "bold")).grid(row=0, column=2, padx=(0, 6), pady=10)
        to_entry = ctk.CTkEntry(controls_frame, textvariable=self.to_var, width=130, height=34)
        to_entry.grid(row=0, column=3, padx=(0, 14), pady=10)

        ctk.CTkButton(controls_frame, text="Anwenden", width=100, height=34, command=self.update_chart).grid(row=0, column=4, padx=(0, 12), pady=10)

        presets = ctk.CTkFrame(controls_frame, fg_color="transparent")
        presets.grid(row=0, column=5, padx=(0, 10), pady=8)
        for idx, (label, days) in enumerate(self.PRESETS):
            ctk.CTkButton(
                presets,
                text=label,
                width=50,
                height=30,
                command=lambda d=days: self.apply_preset(d),
            ).grid(row=0, column=idx, padx=2)

        for entry in (from_entry, to_entry):
            entry.bind("<Return>", lambda *_: self.update_chart())

        self.error_label = ctk.CTkLabel(self.parent, textvariable=self.date_error_var, text_color="#ffb347")
        self.error_label.pack(anchor="center", pady=(0, 2))

        chart_host = ctk.CTkFrame(self.parent, fg_color="transparent")
        chart_host.pack(fill="both", expand=True)

        self.chart_area = ctk.CTkFrame(chart_host, fg_color="transparent")
        self.chart_area.pack(fill="both", expand=True)

        footer = ctk.CTkFrame(chart_host, fg_color="transparent")
        footer.pack(fill="x", pady=(0, 2))

        self.toolbar_frame = ctk.CTkFrame(footer, fg_color="transparent")
        self.toolbar_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            footer,
            text="🗖",
            width=30,
            height=28,
            command=self.open_popout,
            fg_color="#374151",
            hover_color="#4b5563",
        ).pack(side="right", padx=(0, 2), pady=(0, 2))

    def _filter_points(self, points: list[tuple[datetime, float]], start: datetime | None, end: datetime | None):
        if not points:
            return []
        filtered = points
        if start is not None:
            filtered = [p for p in filtered if p[0] >= start]
        if end is not None:
            filtered = [p for p in filtered if p[0] <= end]
        return filtered

    def _destroy_canvas(self):
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.toolbar is not None:
            self.toolbar.destroy()
            self.toolbar = None

    def update_chart(self):
        start = self._parse_date(self.from_var.get())
        end = self._parse_date(self.to_var.get())
        if self.from_var.get().strip() and start is None:
            self.date_error_var.set("Ungültiges Datum für 'Von'. Format: YYYY-MM-DD")
            return
        if self.to_var.get().strip() and end is None:
            self.date_error_var.set("Ungültiges Datum für 'Bis'. Format: YYYY-MM-DD")
            return
        if start and end and start > end:
            self.date_error_var.set("'Von' muss vor 'Bis' liegen.")
            return
        self.date_error_var.set("")

        visible_series = {key: self._filter_points(self.all_series.get(key) or [], start, end) for key in self.visible_keys}
        comparison_series = [(label, self._filter_points(points, start, end)) for label, points in self.comparison_series]
        comparison_series = [(label, points) for label, points in comparison_series if points]

        lower = any(key in {"returns", "drawdown", "benchmark_relative"} for key in self.visible_keys)
        fig, axes = _build_timeseries_figure(
            visible_series=visible_series,
            visible_keys=self.visible_keys,
            comparison_series=comparison_series,
            figsize=(7, 4.35 if lower else 3.05),
        )

        self._destroy_canvas()
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_area)
        self.axes = axes
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.hover_ids = enable_timeseries_hover(self.canvas, axes)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

    def apply_preset(self, days: int | None):
        if not self.max_date:
            return
        if days is None or not self.min_date:
            self.from_var.set(self._fmt_date(self.min_date))
            self.to_var.set(self._fmt_date(self.max_date))
            self.update_chart()
            return

        start = self.max_date - timedelta(days=days)
        if self.min_date and start < self.min_date:
            start = self.min_date
        self.from_var.set(self._fmt_date(start))
        self.to_var.set(self._fmt_date(self.max_date))
        self.update_chart()

    def _collect_current_filter(self) -> tuple[datetime | None, datetime | None]:
        return self._parse_date(self.from_var.get()), self._parse_date(self.to_var.get())

    def open_popout(self):
        start, end = self._collect_current_filter()

        filtered_series = {key: self._filter_points(self.all_series.get(key) or [], start, end) for key in self.visible_keys}
        filtered_comparisons = [
            (label, self._filter_points(points, start, end)) for label, points in self.comparison_series
        ]
        filtered_comparisons = [(label, points) for label, points in filtered_comparisons if points]

        popout, popout_canvas, popout_axes = open_chart_popout(
            parent=self.parent,
            title=f"Chart-Detailansicht: {self.isin}",
            build_figure=lambda: _build_timeseries_figure(
                visible_series=filtered_series,
                visible_keys=self.visible_keys,
                comparison_series=filtered_comparisons,
                figsize=(13.5, 8.2),
                linewidth=2.0,
            ),
            size="1500x920",
        )
        enable_timeseries_hover(popout_canvas, popout_axes)
        popout.focus_force()


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

    TimeSeriesChartModule(
        parent=frame,
        isin=isin,
        visible_keys=visible_keys,
        all_series=visible_series,
        comparison_series=comparison_series,
    )

    if effective_warnings:
        ctk.CTkLabel(frame, text="Hinweise: " + " | ".join(effective_warnings), text_color="#ffb347").pack(anchor="w", pady=(8, 0))
