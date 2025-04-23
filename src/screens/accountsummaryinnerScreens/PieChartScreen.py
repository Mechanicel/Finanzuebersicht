import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.models import AppState


def create_screen(app, navigator, state: AppState, **kwargs):
    clear_ui(app)
    person = state.selected_person
    konten = person.get('Konten', [])

    # Letzten Stand jedes Kontos ermitteln
    labels, sizes = [], []
    for konto in konten:
        entries = konto.get('Kontostaende', [])
        if entries:
            last = entries[-1].split(': ')[1]
            try:
                val = float(last)
            except:
                val = 0.0
        else:
            val = 0.0
        labels.append(konto.get('Kontotyp', ''))
        sizes.append(val)

    # Figure
    fig = Figure(figsize=(5,5), dpi=100)
    ax = fig.add_subplot(111)
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.set_title('Vermögensaufteilung')

    canvas = FigureCanvasTkAgg(fig, master=app)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.pack(fill=ctk.BOTH, expand=True)
