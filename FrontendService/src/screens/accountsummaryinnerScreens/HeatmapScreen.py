from collections import defaultdict
from datetime import datetime

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.models.AppState import AppState
from src.ui.components import section_card, empty_state


def create_screen(app, navigator, state: AppState, **kwargs):
    person = state.selected_person
    konten = person.get("Konten", []) if person else []

    changes = defaultdict(list)
    for konto in konten:
        prev = None
        for ent in konto.get("Kontostaende", []):
            d_str, v_str = ent.split(": ")
            try:
                val = float(v_str)
            except Exception:
                continue
            d = datetime.strptime(d_str, "%Y-%m-%d").date()
            if prev is not None:
                changes[(d.month, d.day)].append(val - prev)
            prev = val

    if not changes:
        empty_state(app, "Keine Veränderungsdaten vorhanden.")
        return

    months = range(1, 13)
    days = range(1, 32)
    matrix = np.zeros((len(days), len(months)))
    for i, day in enumerate(days):
        for j, month in enumerate(months):
            vals = changes.get((month, day), [])
            matrix[i, j] = np.mean(vals) if vals else 0.0

    _, body = section_card(app, "Heatmap", "Durchschnittliche tägliche Änderungen über Monat und Tag")
    fig = Figure(figsize=(6, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    cax = ax.imshow(matrix, aspect="auto", origin="lower", cmap="viridis")
    ax.set_xlabel("Monat")
    ax.set_ylabel("Tag")
    fig.colorbar(cax, label="Ø tägliche Änderung")

    canvas = FigureCanvasTkAgg(fig, master=body)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
