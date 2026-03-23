import customtkinter as ctk

from src.models.AppState import AppState
from src.ui.components import create_page, section_card, secondary_button, stats_row, empty_state


def create_screen(app, navigator, state: AppState, **kwargs):
    ui = create_page(app, "Freibetragsübersicht", "Alle Freibeträge auf einen Blick.", back_command=lambda: navigator.navigate("PersonInfo"))

    freib = state.selected_person.get("Freibetrag", {})
    if not freib:
        empty_state(ui["content"], "Noch keine Freibeträge hinterlegt.")
        return

    _, body = section_card(ui["content"], "Pro Bank")
    total = 0.0

    table = ctk.CTkFrame(body, fg_color="transparent")
    table.pack(fill="x")
    table.grid_columnconfigure(0, weight=2)
    table.grid_columnconfigure(1, weight=1)

    for row, (bank, val) in enumerate(freib.items()):
        ctk.CTkLabel(table, text=bank).grid(row=row, column=0, sticky="w", pady=3)
        ctk.CTkLabel(table, text=val).grid(row=row, column=1, sticky="e", pady=3)
        try:
            total += float(str(val).replace(",", "."))
        except Exception:
            pass

    stats_row(ui["content"], [("Gesamtsumme", f"{total:.2f} €"), ("Bewertung", "Im Rahmen" if total <= 1000 else "Über 1000 €")])
