# src/screens/accountsummaryinnerScreens/PieChartScreen.py
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from src.helpers.UniversalMethoden import clear_ui
from src.models.AppState import AppState


def create_screen(app, navigator, state: AppState, **kwargs):
    clear_ui(app)
    person_data = state.selected_person
    if not person_data:
        return
    konten = person_data.get('Konten', [])

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
        labels.append(konto.get('Kontotyp',''))
        sizes.append(val)

    fig = Figure(figsize=(5,5), dpi=100)
    ax = fig.add_subplot(111)
    wedges, _, _ = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.set_title('Vermögensaufteilung')

    for w in wedges:
        w.set_picker(True)

    def on_pick(event):
        wedge = event.artist
        try:
            idx = wedges.index(wedge)
        except ValueError:
            return
        if konten[idx].get('Kontotyp') == 'Depot':
            # Nur depot_index übergeben; state.selected_person wird intern genutzt
            navigator.navigate(
                "DepoAnalyse",
                depot_index=idx
            )

    canvas = FigureCanvasTkAgg(fig, master=app)
    canvas.draw()
    canvas.mpl_connect('pick_event', on_pick)
    widget = canvas.get_tk_widget()
    widget.pack(fill=ctk.BOTH, expand=True)
