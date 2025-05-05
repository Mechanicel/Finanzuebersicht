import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict
from FrontendService.src.helpers.UniversalMethoden import clear_ui
from FrontendService.src.models import AppState


def create_screen(app, navigator, state: AppState, **kwargs):
    clear_ui(app)
    person = state.selected_person
    konten = person.get('Konten', [])

    # Saldo zum Monatsende pro Konto sammeln
    monthly = defaultdict(float)  # { 'YYYY-MM': sum }
    for konto in konten:
        for ent in konto.get('Kontostaende', []):
            date_str, val_str = ent.split(': ')
            m = date_str[:7]
            try:
                monthly[m] += float(val_str)
            except:
                pass

    # Sortieren nach Monat
    months = sorted(monthly.keys())
    values = [monthly[m] for m in months]

    # Diagramm
    fig = Figure(figsize=(6,4), dpi=100)
    ax = fig.add_subplot(111)
    ax.bar(months, values)
    ax.set_title('Monatliche Saldo-Differenz')
    ax.set_xlabel('Monat')
    ax.set_ylabel('Gesamtsaldo')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y')

    canvas = FigureCanvasTkAgg(fig, master=app)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.pack(fill=ctk.BOTH, expand=True)
