import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import numpy as np
from FrontendService.src.helpers.UniversalMethoden import clear_ui
from FrontendService.src.models import AppState


def create_screen(app, navigator, state: AppState, **kwargs):
    clear_ui(app)
    state.load_all()
    person = state.selected_person
    konten = person.get('Konten', [])

    # Wir prognostizieren nur Depot und Giro zusammen als Gesamtvermögen
    # Fusioniere alle Einträge nach Datum
    date_vals = {}
    for konto in konten:
        for ent in konto.get('Kontostaende', []):
            d_str, v_str = ent.split(': ')
            try:
                val = float(v_str)
            except:
                continue
            date_vals.setdefault(d_str, 0.0)
            date_vals[d_str] += val

    # Sortieren
    dates_sorted = sorted(date_vals.keys())
    x = np.array([datetime.strptime(d, '%Y-%m-%d').timestamp() for d in dates_sorted])
    y = np.array([date_vals[d] for d in dates_sorted])

    # Lineare Regression
    coeffs = np.polyfit(x, y, deg=1)
    trend = np.poly1d(coeffs)(x)

    # Plot
    fig = Figure(figsize=(6,4), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot([datetime.fromtimestamp(t) for t in x], y, 'o', label='Ist-Zustand')
    ax.plot([datetime.fromtimestamp(t) for t in x], trend, '-', label='Linearer Trend')
    ax.set_title('Vermögensprognose')
    ax.set_xlabel('Datum')
    ax.set_ylabel('Gesamtvermögen')
    ax.legend()
    ax.grid(True)

    canvas = FigureCanvasTkAgg(fig, master=app)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=ctk.BOTH, expand=True)
