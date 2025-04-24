# src/screens/accountsummaryinnerScreens/PieChartinnerScreens/DepotPositionPieScreen.py

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from src.helpers.UniversalMethoden import clear_ui
from src.models import AppState

def create_screen(app, navigator, state: AppState,
                  depot_index: int = 0,
                  pick_callback: callable = None,
                  **kwargs):
    """
    Zeichnet die Depot-Positionen als Tortendiagramm.
    Verwendet den stock_data_manager aus dem AppState für Kurse und Firmennamen.
    pick_callback(isin) wird bei Klick auf ein Tortenstück aufgerufen.
    """
    clear_ui(app)

    # Aktuelles Depot aus dem State laden
    person = state.selected_person
    konten = state.data_manager.get_person_data(person).get('Konten', [])
    if depot_index >= len(konten):
        return
    konto = konten[depot_index]

    # Service-Objekt aus dem Store
    stock_svc = state.stock_data_manager
    now = datetime.now()

    # Labels und Größen berechnen
    labels, sizes = [], []
    for det in konto.get('DepotDetails', []):
        isin = det.get('ISIN', '').strip()
        try:
            menge = float(det.get('Menge', 0) or 0)
        except:
            menge = 0.0
        price = stock_svc.get_price_by_isin(isin, now)
        labels.append(stock_svc.get_company_name_by_isin(isin) or isin)
        sizes.append(price * menge)

    # Figure und Achse anlegen
    fig = Figure(figsize=(5,5), dpi=100)
    ax = fig.add_subplot(111)

    # Wenn keine Positionen vorhanden, Hinweis anzeigen
    if not any(sizes):
        ax.text(0.5, 0.5, 'Keine Positionen', ha='center', va='center')
        ax.set_title("Depot-Aufteilung")
    else:
        # Tortendiagramm zeichnen
        wedges, _, _ = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.set_title("Depot-Aufteilung")

        # Picker für interaktives Klicken
        for w in wedges:
            w.set_picker(True)

        # Standard-Callback: Navigation zum AktienAnalyse-Screen
        def default_cb(isin: str):
            navigator.navigate(
                "AktienAnalyse",
                selected_person=state.selected_person,
                isin=isin
            )

        callback = pick_callback or default_cb

        # Klick-Event verarbeiten
        def on_pick(event):
            w = event.artist
            try:
                idx = wedges.index(w)
            except ValueError:
                return
            det = konto["DepotDetails"][idx]
            isin = det.get("ISIN", "").strip()
            callback(isin)

        # Event-Handler registrieren
        canvas = FigureCanvasTkAgg(fig, master=app)
        canvas.mpl_connect("pick_event", on_pick)

    # Canvas final einbinden
    canvas = FigureCanvasTkAgg(fig, master=app)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # Layout-Resizing
    app.grid_rowconfigure(0, weight=1)
    app.grid_columnconfigure(0, weight=1)
