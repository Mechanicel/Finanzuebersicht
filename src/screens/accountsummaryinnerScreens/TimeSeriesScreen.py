import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.models import AppState


def create_screen(app, navigator, state: AppState, **kwargs):
    clear_ui(app)
    state.load_all()
    person = state.selected_person
    konten = person.get('Konten', [])

    # Erstelle Figure
    fig = Figure(figsize=(6,4), dpi=100)
    ax = fig.add_subplot(111)

    # Für jedes Konto einen Zeitreihen-Plot
    for konto in konten:
        entries = konto.get('Kontostaende', [])
        print(entries)
        dates, values = [], []
        for ent in entries:
            date_str, val_str = ent.split(': ')
            try:
                dates.append(datetime.strptime(date_str, '%Y-%m-%d'))
                values.append(float(val_str))
            except:
                continue
        ax.plot(dates, values, label=konto.get('Kontotyp', ''))

    ax.set_title('Zeitreihe der Kontostände')
    ax.set_xlabel('Datum')
    ax.set_ylabel('Saldo')
    ax.legend()
    ax.grid(True)

    # Canvas in TK-Frame einbetten
    canvas = FigureCanvasTkAgg(fig, master=app)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.pack(fill=ctk.BOTH, expand=True)
