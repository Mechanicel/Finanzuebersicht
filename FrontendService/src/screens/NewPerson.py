import customtkinter as ctk

from src.models.AppState import AppState
from src.ui.components import create_page, section_card, action_bar_grid, primary_button, set_status


def create_screen(app, navigator, state: AppState, **kwargs):
    ui = create_page(app, "Neue Person", "Erfassen Sie Vor- und Nachnamen.", back_command=lambda: navigator.navigate("MainScreen"))
    status = ui["status"]

    _, body = section_card(ui["content"], "Personenstammdaten")

    name_var = ctk.StringVar()
    nach_var = ctk.StringVar()

    ctk.CTkLabel(body, text="Vorname *").grid(row=0, column=0, sticky="w", pady=(0, 4))
    entry_name = ctk.CTkEntry(body, textvariable=name_var)
    entry_name.grid(row=1, column=0, sticky="ew", pady=(0, 8))

    ctk.CTkLabel(body, text="Nachname *").grid(row=2, column=0, sticky="w", pady=(0, 4))
    entry_nach = ctk.CTkEntry(body, textvariable=nach_var)
    entry_nach.grid(row=3, column=0, sticky="ew")

    def proceed():
        n = name_var.get().strip()
        nn = nach_var.get().strip()

        entry_name.configure(border_color=("#565B5E", "#565B5E"))
        entry_nach.configure(border_color=("#565B5E", "#565B5E"))

        if not n or not nn:
            if not n:
                entry_name.configure(border_color="#B00020")
            if not nn:
                entry_nach.configure(border_color="#B00020")
            set_status(status, "Bitte füllen Sie alle Pflichtfelder aus.", "warning")
            return

        for p in state.personen:
            if p["Name"] == n and p["Nachname"] == nn:
                set_status(status, "Diese Person existiert bereits.", "error")
                return

        new = {"Name": n, "Nachname": nn, "Freibetrag": {}, "Banken": [], "Konten": []}
        state.personen.append(new)
        state.data_manager.save_personen(state.personen)
        set_status(status, "Person erfolgreich angelegt.", "success")
        navigator.navigate("MainScreen")

    bar = action_bar_grid(body, row=4)
    primary_button(bar, "Person speichern", proceed, column=0)
