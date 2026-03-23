import customtkinter as ctk

from src.models.AppState import AppState
from src.ui.components import create_page, section_card, action_bar, primary_button, secondary_button, set_status, empty_state


def create_screen(app, navigator, state: AppState, **kwargs):
    person = state.selected_person
    banken = person.get("Banken", [])

    ui = create_page(app, "Freibetrag erfassen", "Freibetrag pro Bank verwalten.", back_command=lambda: navigator.navigate("PersonInfo"))
    status = ui["status"]

    if not banken:
        empty_state(ui["content"], "Bitte ordnen Sie zuerst mindestens eine Bank zu.")
        return

    _, body = section_card(ui["content"], "Eingabe")
    var = ctk.StringVar(value=banken[0])
    amt = ctk.StringVar()
    current_var = ctk.StringVar(value="Aktuell: –")

    ctk.CTkLabel(body, text="Bank").grid(row=0, column=0, sticky="w")
    combo = ctk.CTkComboBox(body, variable=var, values=banken, state="readonly")
    combo.grid(row=1, column=0, sticky="ew", pady=(2, 8))

    ctk.CTkLabel(body, textvariable=current_var, text_color="gray70").grid(row=2, column=0, sticky="w", pady=(0, 8))

    ctk.CTkLabel(body, text="Freibetrag (€)").grid(row=3, column=0, sticky="w")
    entry = ctk.CTkEntry(body, textvariable=amt)
    entry.grid(row=4, column=0, sticky="ew", pady=(2, 0))

    def update_current(*_):
        current = person.get("Freibetrag", {}).get(var.get(), "–")
        current_var.set(f"Aktuell: {current}")

    combo.configure(command=lambda _: update_current())
    update_current()

    def add():
        b = var.get()
        wert = amt.get().strip().replace(",", ".")
        try:
            float(wert)
        except ValueError:
            set_status(status, "Bitte einen gültigen numerischen Freibetrag eingeben.", "warning")
            entry.configure(border_color="#B00020")
            return

        person["Freibetrag"][b] = wert
        state.save_person(person)
        set_status(status, f"Freibetrag für {b} gespeichert.", "success")
        entry.configure(border_color=("#565B5E", "#565B5E"))
        update_current()

    bar = action_bar(body)
    primary_button(bar, "Speichern", add, column=0)
    secondary_button(bar, "Zurück", lambda: navigator.navigate("PersonInfo"), column=1)
