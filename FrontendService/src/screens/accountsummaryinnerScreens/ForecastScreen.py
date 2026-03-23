from datetime import datetime

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.models.AppState import AppState
from src.ui.components import section_card, stats_row, empty_state


def create_screen(app, navigator, state: AppState, **kwargs):
    state.load_all()
    person = state.selected_person
    konten = person.get("Konten", []) if person else []

    date_vals = {}
    for konto in konten:
        for ent in konto.get("Kontostaende", []):
            d_str, v_str = ent.split(": ")
            try:
                val = float(v_str)
            except Exception:
                continue
            date_vals.setdefault(d_str, 0.0)
            date_vals[d_str] += val

    if len(date_vals) < 2:
        empty_state(app, "Für den Forecast werden mindestens zwei Datenpunkte benötigt.")
        return

    dates_sorted = sorted(date_vals.keys())
    x = np.array([datetime.strptime(d, "%Y-%m-%d").timestamp() for d in dates_sorted])
    y = np.array([date_vals[d] for d in dates_sorted])
    coeffs = np.polyfit(x, y, deg=1)
    trend = np.poly1d(coeffs)(x)

    stats_row(app, [("Startwert", f"{y[0]:.2f}"), ("Endwert", f"{y[-1]:.2f}"), ("Trend Δ", f"{(trend[-1]-trend[0]):.2f}")])

    _, body = section_card(app, "Forecast", "Ist-Zustand und linearer Trend")
    fig = Figure(figsize=(6, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    x_dt = [datetime.fromtimestamp(t) for t in x]
    ax.plot(x_dt, y, "o", label="Ist-Zustand")
    ax.plot(x_dt, trend, "-", label="Linearer Trend")
    ax.set_title("Vermögensprognose")
    ax.set_xlabel("Datum")
    ax.set_ylabel("Gesamtvermögen")
    ax.legend()
    ax.grid(True, alpha=0.35)

    canvas = FigureCanvasTkAgg(fig, master=body)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
