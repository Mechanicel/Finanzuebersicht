# screens/screen_person_info.py

import customtkinter
from helper.universalMethoden import clear_ui, zentrieren

# Importiere die Calculate-Logik
from helper.calculate_helper import calculate_logic

def person_info_screen(app, navigator, selected_person, **kwargs):
    clear_ui(app)

    label = customtkinter.CTkLabel(app, text=f"{selected_person['Name']} {selected_person['Nachname']}")
    label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)

    btn_account_summary = customtkinter.CTkButton(
        app, text="Kontozusammenfassung erstellen",
        command=lambda: navigator.navigate("account_summary", selected_person=selected_person)
    )
    btn_account_summary.grid(row=1, column=0, columnspan=2, padx=20, pady=10)

    btn_freibetrag_input = customtkinter.CTkButton(
        app, text="Freibetrag eingeben",
        command=lambda: navigator.navigate("freibetrag_input", selected_person=selected_person)
    )
    btn_freibetrag_input.grid(row=2, column=0, columnspan=2, padx=20, pady=10)

    btn_account_overview = customtkinter.CTkButton(
        app, text="Übersicht erstellen",
        command=lambda: navigator.navigate("account_overview", selected_person=selected_person)
    )
    btn_account_overview.grid(row=3, column=0, columnspan=2, padx=20, pady=10)

    btn_bank_assignment = customtkinter.CTkButton(
        app, text="Bank hinzufügen",
        command=lambda: navigator.navigate("bank_assignment", selected_person=selected_person)
    )
    btn_bank_assignment.grid(row=4, column=0, columnspan=2, padx=20, pady=10)

    btn_freibetrag_display = customtkinter.CTkButton(
        app, text="Freibeträge anzeigen",
        command=lambda: navigator.navigate("freibetrag_display", selected_person=selected_person)
    )
    btn_freibetrag_display.grid(row=5, column=0, columnspan=2, padx=20, pady=10)

    btn_account_addition = customtkinter.CTkButton(
        app, text="Konto hinzufügen",
        command=lambda: navigator.navigate("account_addition", selected_person=selected_person)
    )
    btn_account_addition.grid(row=6, column=0, columnspan=2, padx=20, pady=10)

    # Neuer Button: Calculate
    btn_calculate = customtkinter.CTkButton(
        app,
        text="Calculate",
        command=lambda: calculate_logic(selected_person)
    )
    btn_calculate.grid(row=7, column=0, columnspan=2, padx=20, pady=10)

    btn_back = customtkinter.CTkButton(
        app, text="Zurück",
        command=lambda: navigator.navigate("person_selection")
    )
    btn_back.grid(row=8, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)
