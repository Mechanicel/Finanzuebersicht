import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import numpy as np
from collections import defaultdict
from FrontendService.src.helpers.UniversalMethoden import clear_ui
from FrontendService.src.models import AppState


def create_screen(app, navigator, state: AppState, **kwargs):
    clear_ui(app)
    person = state.selected_person
    konten = person.get('Konten', [])

    # Tagesänderungen pro Tag/Monat sammeln
    changes = defaultdict(list)  # {(month, day): [deltas]}
    for konto in konten:
        prev = None
        for ent in konto.get('Kontostaende', []):
            d_str, v_str = ent.split(': ')
            try:
                val = float(v_str)
            except:
                continue
            d = datetime.strptime(d_str, '%Y-%m-%d').date()
            if prev is not None:
                delta = val - prev
                changes[(d.month, d.day)].append(delta)
            prev = val

    # Heatmap-Datenmatrix
    months = range(1,13)
    days = range(1,32)
    matrix = np.zeros((len(days), len(months)))
    for i, day in enumerate(days):
        for j, month in enumerate(months):
            vals = changes.get((month, day), [])
            matrix[i,j] = np.mean(vals) if vals else 0.0

    # Plot
    fig = Figure(figsize=(6,4), dpi=100)
    ax = fig.add_subplot(111)
    cax = ax.imshow(matrix, aspect='auto', origin='lower')
    ax.set_xlabel('Monat')
    ax.set_ylabel('Tag')
    fig.colorbar(cax, label='Durchschnittliche tägliche Änderung')

    canvas = FigureCanvasTkAgg(fig, master=app)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=ctk.BOTH, expand=True)
