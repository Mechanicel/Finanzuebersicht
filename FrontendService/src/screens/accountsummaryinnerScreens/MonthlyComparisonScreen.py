from collections import defaultdict

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.models.AppState import AppState
from src.ui.components import section_card, empty_state


def create_screen(app, navigator, state: AppState, **kwargs):
    person = state.selected_person
    konten = person.get("Konten", []) if person else []

    monthly = defaultdict(float)
    for konto in konten:
        for ent in konto.get("Kontostaende", []):
            date_str, val_str = ent.split(": ")
            try:
                monthly[date_str[:7]] += float(val_str)
            except Exception:
                pass

    if not monthly:
        empty_state(app, "Keine Monatsdaten vorhanden.")
        return

    months = sorted(monthly.keys())
    values = [monthly[m] for m in months]

    _, body = section_card(app, "Monatsvergleich", "Gesamtsaldo aggregiert nach Monat")

    fig = Figure(figsize=(6, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    ax.bar(months, values, color="#3A78B5")
    ax.set_title("Monatliche Saldo-Entwicklung")
    ax.set_xlabel("Monat")
    ax.set_ylabel("Gesamtsaldo")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.35)

    canvas = FigureCanvasTkAgg(fig, master=body)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
