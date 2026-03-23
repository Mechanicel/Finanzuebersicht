import customtkinter as ctk

from src.models.AppState import AppState
from src.ui.components import create_page, section_card, action_bar, primary_button, set_status, empty_state


def create_screen(app, navigator, state: AppState, **kwargs):
    persons = state.personen
    all_names = [f"{p['Name']} {p['Nachname']}" for p in persons]

    ui = create_page(
        app,
        title="Person auswählen",
        subtitle="Wählen Sie eine vorhandene Person und öffnen Sie deren Übersicht.",
        back_command=lambda: navigator.navigate("MainScreen"),
    )
    status = ui["status"]
    _, body = section_card(ui["content"], "Personen", "Suche und Auswahl")

    if not all_names:
        empty_state(body, "Es sind noch keine Personen vorhanden. Legen Sie zuerst eine Person an.")
        return

    selected_person_var = ctk.StringVar(value=all_names[0])
    search_var = ctk.StringVar()

    ctk.CTkLabel(body, text="Suche").pack(anchor="w", pady=(0, 4))
    search_entry = ctk.CTkEntry(body, textvariable=search_var, placeholder_text="Name oder Nachname")
    search_entry.pack(fill="x", pady=(0, 8))

    ctk.CTkLabel(body, text="Person").pack(anchor="w", pady=(4, 4))
    dropdown = ctk.CTkComboBox(body, variable=selected_person_var, values=all_names, state="readonly")
    dropdown.pack(fill="x")

    def apply_filter(*_):
        query = search_var.get().strip().lower()
        filtered = [n for n in all_names if query in n.lower()] if query else all_names
        dropdown.configure(values=filtered or ["Keine Treffer"])
        selected_person_var.set((filtered or ["Keine Treffer"])[0])

    search_var.trace_add("write", apply_filter)

    def confirm():
        selected = selected_person_var.get()
        if selected == "Keine Treffer" or " " not in selected:
            set_status(status, "Bitte wählen Sie eine gültige Person aus.", "warning")
            return
        vorname, nachname = selected.split(" ", 1)
        person = state.select_person(vorname, nachname)
        if person:
            navigator.navigate("PersonInfo")
        else:
            set_status(status, "Die ausgewählte Person wurde nicht gefunden.", "error")

    bar = action_bar(body)
    primary_button(bar, "Öffnen", confirm, column=0)
