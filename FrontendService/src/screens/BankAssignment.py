import customtkinter as ctk

from src.helpers.ui_flow import filter_bank_names
from src.models.AppState import AppState
from src.ui.components import create_page, section_card, action_bar, primary_button, set_status, empty_state


def create_screen(app, navigator, state: AppState, **kwargs):
    person = state.selected_person
    all_banks = [b["Name"] for b in state.banken]

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
    search_var = ctk.StringVar()
    filtered_banks = filter_bank_names(all_banks, search_var.get())
    var = ctk.StringVar(value=filtered_banks[0] if filtered_banks else "")
    ctk.CTkLabel(select_body, text="Bank suchen").pack(anchor="w", pady=(0, 4))
    search_entry = ctk.CTkEntry(select_body, textvariable=search_var, placeholder_text="Name eingeben...")
    search_entry.pack(fill="x", pady=(0, 8))
    ctk.CTkLabel(select_body, text="Verfügbare Bank").pack(anchor="w", pady=(0, 4))
    bank_combo = ctk.CTkComboBox(select_body, variable=var, values=filtered_banks, state="readonly")
    bank_combo.pack(fill="x")

    def update_filtered_banks(*_):
        matching = filter_bank_names(all_banks, search_var.get())
        bank_combo.configure(values=matching if matching else [""])
        current = var.get()
        if current not in matching:
            var.set(matching[0] if matching else "")

    search_var.trace_add("write", update_filtered_banks)

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
