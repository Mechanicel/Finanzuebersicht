import customtkinter as ctk
from src.helpers.UniversalMethoden import clear_ui
import statistics
from src.models.AppState import AppState


def create_screen(app, navigator, state: AppState, **kwargs):
    clear_ui(app)
    person = state.selected_person
    konten = person.get('Konten', [])

    # Gesamtwerte aller Konten über alle Datenpunkte
    all_values = []
    for konto in konten:
        for ent in konto.get('Kontostaende', []):
            _, val_str = ent.split(': ')
            try:
                all_values.append(float(val_str))
            except:
                pass

    avg = statistics.mean(all_values) if all_values else 0.0
    mn = min(all_values) if all_values else 0.0
    mx = max(all_values) if all_values else 0.0
    cnt = len(all_values)

    # Anzeige als Labels
    lines = [
        f"Anzahl Datenpunkte: {cnt}",
        f"Durchschnittlicher Saldo: {avg:.2f}",
        f"Tiefster Saldo: {mn:.2f}",
        f"Höchster Saldo: {mx:.2f}"
    ]

    for i, text in enumerate(lines):
        ctk.CTkLabel(app, text=text, font=("Arial", 14)).pack(anchor="w", padx=20, pady=5)
