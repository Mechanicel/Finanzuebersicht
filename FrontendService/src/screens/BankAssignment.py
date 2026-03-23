import customtkinter as ctk

from src.models.AppState import AppState
from src.ui.components import create_page, section_card, action_bar, primary_button, secondary_button, set_status, empty_state


def create_screen(app, navigator, state: AppState, **kwargs):
    person = state.selected_person
    banks = [b["Name"] for b in state.banken]

    ui = create_page(
        app,
        "Bank zuordnen",
        f"Person: {person['Name']} {person['Nachname']}",
        back_command=lambda: navigator.navigate("PersonInfo"),
    )
    status = ui["status"]

    _, current_body = section_card(ui["content"], "Bereits zugeordnete Banken")
    if person.get("Banken"):
        for b in person["Banken"]:
            ctk.CTkLabel(current_body, text=f"• {b}").pack(anchor="w", pady=2)
    else:
        empty_state(current_body, "Der Person ist noch keine Bank zugeordnet.")

    _, select_body = section_card(ui["content"], "Neue Zuordnung")
    var = ctk.StringVar(value=banks[0] if banks else "")
    ctk.CTkLabel(select_body, text="Verfügbare Bank").pack(anchor="w", pady=(0, 4))
    ctk.CTkComboBox(select_body, variable=var, values=banks, state="readonly").pack(fill="x")

    def add():
        name = var.get()
        if not name:
            set_status(status, "Keine Bank verfügbar.", "warning")
            return
        if name in person["Banken"]:
            set_status(status, "Diese Bank ist bereits zugeordnet.", "info")
            return
        person["Banken"].append(name)
        state.save_person(person)
        set_status(status, f"Bank '{name}' wurde hinzugefügt.", "success")
        navigator.navigate("BankAssignment")

    bar = action_bar(select_body)
    primary_button(bar, "Zuordnen", add, column=0)
    secondary_button(bar, "Zurück", lambda: navigator.navigate("PersonInfo"), column=1)
