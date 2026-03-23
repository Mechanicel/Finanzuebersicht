import customtkinter as ctk

from src.models.AppState import AppState
from src.ui.components import create_page, section_card, stats_row


def create_screen(app, navigator, state: AppState, **kwargs):
    person = state.selected_person
    if not person:
        navigator.navigate("PersonSelection")
        return

    ui = create_page(
        app,
        title=f"{person['Name']} {person['Nachname']}",
        subtitle="Personen-Hub für Verwaltung und Analysen",
        back_command=lambda: navigator.navigate("PersonSelection"),
    )

    stats_row(
        ui["content"],
        [
            ("Banken", str(len(person.get("Banken", [])))),
            ("Konten", str(len(person.get("Konten", [])))),
            ("Freibeträge", str(len(person.get("Freibetrag", {})))),
        ],
    )

    _, manage = section_card(ui["content"], "Verwalten")
    manage.grid_columnconfigure((0, 1), weight=1)
    buttons_manage = [
        ("Freibetrag eingeben", "FreibetragInput"),
        ("Freibeträge anzeigen", "FreibetragDisplay"),
        ("Kontoübersicht erfassen", "AccountOverview"),
        ("Bank hinzufügen", "BankAssignment"),
        ("Konto hinzufügen", "AccountAddition"),
        ("Konten bearbeiten", "AccountEditing"),
    ]
    for i, (label, route) in enumerate(buttons_manage):
        ctk.CTkButton(manage, text=label, height=40, command=lambda r=route: navigator.navigate(r)).grid(
            row=i // 2, column=i % 2, padx=6, pady=6, sticky="ew"
        )

    _, analyze = section_card(ui["content"], "Analysieren")
    ctk.CTkButton(analyze, text="Kontozusammenfassung öffnen", height=44, command=lambda: navigator.navigate("AccountSummary")).pack(fill="x")
