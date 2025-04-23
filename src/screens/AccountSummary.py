# src/screens/AccountSummary.py

import logging
import customtkinter as ctk
from tkcalendar import DateEntry
from datetime import datetime, time
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.models.AppState import AppState

logger = logging.getLogger(__name__)

def create_screen(app, navigator, state: AppState, **kwargs):
    """
    Zeigt die Kontostände aller Kontotypen (einschließlich Festgeld) für ein gewählten Datum an.
    Führt vorher Berechnungen für Festgeld und Depot durch und lädt die aktualisierten Daten aus dem Store.
    """
    clear_ui(app)
    person = state.selected_person
    ac = state.account_controller

    # Zurück-Button
    ctk.CTkButton(
        app,
        text="Zurück",
        command=lambda: navigator.navigate("PersonInfo")
    ).grid(row=0, column=0, padx=20, pady=10, sticky="w")

    # Titel und Datumsauswahl
    ctk.CTkLabel(app, text="Kontostände pro Tag", font=("Arial", 16, "bold")) \
        .grid(row=1, column=0, columnspan=2, padx=20, pady=(0,10))
    ctk.CTkLabel(app, text="Datum:").grid(row=2, column=0, padx=20, pady=10, sticky="e")
    de = DateEntry(app, date_pattern='yyyy-mm-dd')
    de.grid(row=2, column=1, padx=20, pady=10, sticky="w")

    # Platzhalter für Ausgabe
    output_start_row = 4

    def show():
        # Lösche alte Ausgaben
        for w in app.grid_slaves():
            info = w.grid_info()
            if info.get('row', 0) >= output_start_row:
                w.destroy()

        # Gewähltes Datum
        d = de.get_date()
        dt = datetime.combine(d, time.min)
        logger.debug(f"AccountSummary.show: Datum {dt}")

        # 1) Neue Berechnung Festgeld + Depot
        ac.calculate_festgeld(person, dt)
        ac.calculate_depot(person, dt)

        # 2) Store neu laden und selected_person aktualisieren
        prev_name = person.get('Name')
        prev_nach = person.get('Nachname')
        state.load_all()
        state.select_person(prev_name, prev_nach)
        konten = state.selected_person.get('Konten', [])

        # 3) Ausgabe bauen
        header = f"{'Kontotyp':<15} | {'Bank':<20} | {'Kontostand':>12}"
        sep = '-' * len(header)
        total = 0.0
        date_str = d.strftime('%Y-%m-%d')

        # Header
        ctk.CTkLabel(app, text=header, justify="left").grid(
            row=output_start_row, column=0, columnspan=2, sticky="w", padx=20
        )
        ctk.CTkLabel(app, text=sep, justify="left").grid(
            row=output_start_row+1, column=0, columnspan=2, sticky="w", padx=20
        )

        # Konten
        for idx, konto in enumerate(konten):
            typ = konto.get('Kontotyp', 'Unbekannt')
            bank = konto.get('Bank', 'Unbekannt')
            wert = 0.0
            for entry in konto.get('Kontostaende', []):
                parts = entry.split(': ')
                if len(parts) == 2 and parts[0] == date_str:
                    try:
                        wert = float(parts[1])
                    except:
                        wert = 0.0
                    break
            total += wert
            line = f"{typ:<15} | {bank:<20} | {wert:12.2f}"
            ctk.CTkLabel(app, text=line, justify="left").grid(
                row=output_start_row+2+idx, column=0, columnspan=2, sticky="w", padx=20
            )

        # Summenzeile
        end_row = output_start_row+2+len(konten)
        ctk.CTkLabel(app, text=sep, justify="left").grid(
            row=end_row, column=0, columnspan=2, sticky="w", padx=20
        )
        total_line = f"{'':<15} | {'Gesamt':<20} | {total:12.2f}"
        ctk.CTkLabel(app, text=total_line, justify="left").grid(
            row=end_row+1, column=0, columnspan=2, sticky="w", padx=20
        )

    # Button zum Anzeigen
    ctk.CTkButton(
        app,
        text="Anzeigen",
        command=show
    ).grid(row=3, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)
