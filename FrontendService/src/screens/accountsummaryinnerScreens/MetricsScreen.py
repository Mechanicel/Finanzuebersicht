import statistics

import customtkinter as ctk

from src.models.AppState import AppState
from src.ui.components import stats_row, section_card, empty_state


def create_screen(app, navigator, state: AppState, **kwargs):
    person = state.selected_person
    konten = person.get("Konten", []) if person else []

    all_values = []
    for konto in konten:
        for ent in konto.get("Kontostaende", []):
            _, val_str = ent.split(": ")
            try:
                all_values.append(float(val_str))
            except Exception:
                pass

    if not all_values:
        empty_state(app, "Keine Kennzahlen verfügbar, da keine Kontostände vorhanden sind.")
        return

    avg = statistics.mean(all_values)
    mn = min(all_values)
    mx = max(all_values)
    cnt = len(all_values)

    stats_row(app, [("Datenpunkte", str(cnt)), ("Ø Saldo", f"{avg:.2f}"), ("Minimum", f"{mn:.2f}"), ("Maximum", f"{mx:.2f}")])

    _, details = section_card(app, "Kennzahlen-Details")
    for text in [
        f"Anzahl Datenpunkte: {cnt}",
        f"Durchschnittlicher Saldo: {avg:.2f}",
        f"Tiefster Saldo: {mn:.2f}",
        f"Höchster Saldo: {mx:.2f}",
    ]:
        ctk.CTkLabel(details, text=text, anchor="w").pack(fill="x", pady=4)
