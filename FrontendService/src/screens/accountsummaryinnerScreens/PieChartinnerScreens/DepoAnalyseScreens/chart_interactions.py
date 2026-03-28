from __future__ import annotations

from bisect import bisect_left
from datetime import datetime
import math
from typing import Callable

import customtkinter as ctk
import matplotlib.dates as mdates
from matplotlib.axes import Axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


def _format_date(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    try:
        converted = mdates.num2date(float(value))
        return converted.strftime("%Y-%m-%d")
    except Exception:
        return str(value)


def enable_timeseries_hover(canvas: FigureCanvasTkAgg, axes: list[Axes], precision: int = 2) -> tuple[int, int, int]:
    """Enable robust hover annotations for line charts across multiple axes."""
    annotation = axes[0].annotate(
        "",
        xy=(0, 0),
        xytext=(12, 12),
        textcoords="offset points",
        bbox={"boxstyle": "round,pad=0.3", "fc": "#1f2937", "ec": "#9ca3af", "alpha": 0.95},
        color="white",
        fontsize=9,
    )
    annotation.set_visible(False)

    def _hide_if_needed(force: bool = False):
        if annotation.get_visible() or force:
            annotation.set_visible(False)
            canvas.draw_idle()

    def _closest_index(x_values_num: list[float], x_mouse_num: float) -> int | None:
        if not x_values_num:
            return None
        insert_idx = bisect_left(x_values_num, x_mouse_num)
        if insert_idx <= 0:
            return 0
        if insert_idx >= len(x_values_num):
            return len(x_values_num) - 1
        left = x_values_num[insert_idx - 1]
        right = x_values_num[insert_idx]
        return insert_idx if abs(right - x_mouse_num) < abs(x_mouse_num - left) else insert_idx - 1

    def _on_motion(event):
        if event.inaxes not in axes or event.xdata is None:
            _hide_if_needed()
            return

        current_ax = event.inaxes
        best = None
        for line in current_ax.get_lines():
            x_values = list(line.get_xdata())
            y_values = list(line.get_ydata())
            if not x_values or not y_values or len(x_values) != len(y_values):
                continue

            try:
                x_values_num = [mdates.date2num(x) for x in x_values]
            except Exception:
                continue

            idx = _closest_index(x_values_num, float(event.xdata))
            if idx is None:
                continue
            x_num = x_values_num[idx]
            y_val = y_values[idx]
            if y_val is None:
                continue

            distance = abs(x_num - float(event.xdata))
            candidate = {
                "distance": distance,
                "x_num": x_num,
                "y": float(y_val),
                "label": str(line.get_label() or "Serie"),
            }
            if best is None or candidate["distance"] < best["distance"]:
                best = candidate

        if best is None:
            _hide_if_needed()
            return

        text = f"{best['label']}\n{_format_date(best['x_num'])}\n{best['y']:.{precision}f}"
        previous_text = annotation.get_text()
        previous_xy = annotation.xy
        annotation.xy = (best["x_num"], best["y"])
        annotation.set_text(text)
        annotation.set_visible(True)

        if text != previous_text or previous_xy != annotation.xy:
            canvas.draw_idle()

    def _on_leave(_event):
        _hide_if_needed()

    motion_id = canvas.mpl_connect("motion_notify_event", _on_motion)
    axes_leave_id = canvas.mpl_connect("axes_leave_event", _on_leave)
    figure_leave_id = canvas.mpl_connect("figure_leave_event", _on_leave)
    return motion_id, axes_leave_id, figure_leave_id


def enable_pie_hover(
    canvas: FigureCanvasTkAgg,
    ax: Axes,
    wedges: list,
    labels: list[str],
    values: list[float],
    currency: str = "EUR",
) -> tuple[int, int]:
    annotation = ax.annotate(
        "",
        xy=(0, 0),
        xytext=(16, 16),
        textcoords="offset points",
        bbox={"boxstyle": "round,pad=0.35", "fc": "#111827", "ec": "#9ca3af", "alpha": 0.95},
        color="white",
        fontsize=9,
    )
    annotation.set_visible(False)

    total = sum(v for v in values if v is not None)

    def _on_motion(event):
        if event.inaxes != ax:
            if annotation.get_visible():
                annotation.set_visible(False)
                canvas.draw_idle()
            return

        for index, wedge in enumerate(wedges):
            contains, _ = wedge.contains(event)
            if not contains:
                continue

            value = float(values[index] or 0.0)
            share = (value / total * 100.0) if total else 0.0
            text = f"{labels[index]}\n{value:,.2f} {currency}\n{share:.2f}%"
            center_angle = (wedge.theta1 + wedge.theta2) / 2
            annotation.xy = (
                wedge.center[0] + 0.7 * wedge.r * math.cos(math.radians(center_angle)),
                wedge.center[1] + 0.7 * wedge.r * math.sin(math.radians(center_angle)),
            )
            if annotation.get_text() != text or not annotation.get_visible():
                annotation.set_text(text)
                annotation.set_visible(True)
                canvas.draw_idle()
            return

        if annotation.get_visible():
            annotation.set_visible(False)
            canvas.draw_idle()

    motion_id = canvas.mpl_connect("motion_notify_event", _on_motion)
    axes_leave_id = canvas.mpl_connect("axes_leave_event", lambda _evt: _on_motion(type("E", (), {"inaxes": None})()))
    return motion_id, axes_leave_id


def open_chart_popout(
    parent,
    title: str,
    build_figure: Callable[[], tuple[Figure, list[Axes]]],
    size: str = "1400x850",
):
    popout = ctk.CTkToplevel(parent)
    popout.title(title)
    popout.geometry(size)
    popout.minsize(980, 620)

    try:
        popout.state("zoomed")
    except Exception:
        pass

    container = ctk.CTkFrame(popout, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=8, pady=8)

    figure, axes = build_figure()
    canvas = FigureCanvasTkAgg(figure, master=container)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    return popout, canvas, axes
