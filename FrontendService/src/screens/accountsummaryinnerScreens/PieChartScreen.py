import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.helpers.ui_flow import extract_latest_balance
from src.models.AppState import AppState
from src.ui.components import section_card, empty_state


def create_screen(app, navigator, state: AppState, **kwargs):
    person_data = state.selected_person
    if not person_data:
        empty_state(app, "Keine Person ausgewählt.")
        return

    konten = person_data.get("Konten", [])
    labels, sizes = [], []
    for konto in konten:
        val = extract_latest_balance(konto)
        labels.append(konto.get("Kontotyp", "Unbekannt"))
        sizes.append(val)

    if not any(sizes):
        empty_state(app, "Keine Kontostände vorhanden. Bitte zuerst Daten in der Kontoübersicht erfassen.")
        return

    _, body = section_card(app, "Vermögensaufteilung", "Tipp: Klicken Sie auf einen Depot-Anteil für die Detailanalyse.")
    fig = Figure(figsize=(6, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    wedges, _, _ = ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.set_title("Vermögensaufteilung nach Kontotyp")

    for w in wedges:
        w.set_picker(True)

    def on_pick(event):
        wedge = event.artist
        try:
            idx = wedges.index(wedge)
        except ValueError:
            return
        if konten[idx].get("Kontotyp") == "Depot":
            navigator.navigate("DepoAnalyse", depot_index=idx)

    canvas = FigureCanvasTkAgg(fig, master=body)
    canvas.draw()
    canvas.mpl_connect("pick_event", on_pick)
    canvas.get_tk_widget().pack(fill="both", expand=True)
