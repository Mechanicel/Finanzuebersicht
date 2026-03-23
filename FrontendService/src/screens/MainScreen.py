import customtkinter as ctk

from src.ui.components import create_page, section_card, primary_button, secondary_button


def create_screen(app, navigator, state, **kwargs):
    ui = create_page(
        app,
        title="Finanzübersicht",
        subtitle="Verwaltung und Analyse Ihrer Personen, Banken und Konten.",
    )
    content = ui["content"]

    _, actions = section_card(content, "Schnellstart", "Wählen Sie eine Aktion aus, um zu beginnen.")
    actions.grid_columnconfigure((0, 1, 2), weight=1)

    ctk.CTkButton(
        actions,
        text="👤 Person auswählen",
        height=54,
        command=lambda: navigator.navigate("PersonSelection"),
    ).grid(row=0, column=0, padx=8, pady=8, sticky="ew")

    ctk.CTkButton(
        actions,
        text="➕ Neue Person",
        height=54,
        command=lambda: navigator.navigate("NewPerson"),
    ).grid(row=0, column=1, padx=8, pady=8, sticky="ew")

    ctk.CTkButton(
        actions,
        text="🏦 Neue Bank",
        height=54,
        command=lambda: navigator.navigate("NewBank"),
    ).grid(row=0, column=2, padx=8, pady=8, sticky="ew")
