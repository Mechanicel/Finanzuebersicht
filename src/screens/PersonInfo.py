import customtkinter
from helpers.UniversalMethoden import clear_ui, zentrieren
from controllers.AccountController import AccountController

def create_screen(app, navigator, selected_person, **kwargs):
    clear_ui(app)
    account_controller = AccountController()

    # Header: Name der Person
    label = customtkinter.CTkLabel(app, text=f"{selected_person.get('Name','')} {selected_person.get('Nachname','')}")
    label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)

    # Button: Kontozusammenfassung anzeigen
    btn_account_summary = customtkinter.CTkButton(
        app, text="Kontozusammenfassung",
        command=lambda: navigator.navigate("AccountSummary", selected_person=selected_person)
    )
    btn_account_summary.grid(row=1, column=0, columnspan=2, padx=20, pady=10)

    # Button: Freibetrag eingeben
    btn_freibetrag_input = customtkinter.CTkButton(
        app, text="Freibetrag eingeben",
        command=lambda: navigator.navigate("FreibetragInput", selected_person=selected_person)
    )
    btn_freibetrag_input.grid(row=2, column=0, columnspan=2, padx=20, pady=10)

    # Button: Kontoübersicht erstellen
    btn_account_overview = customtkinter.CTkButton(
        app, text="Kontoübersicht",
        command=lambda: navigator.navigate("AccountOverview", selected_person=selected_person)
    )
    btn_account_overview.grid(row=3, column=0, columnspan=2, padx=20, pady=10)

    # Button: Bank hinzufügen
    btn_bank_assignment = customtkinter.CTkButton(
        app, text="Bank hinzufügen",
        command=lambda: navigator.navigate("BankAssignment", selected_person=selected_person)
    )
    btn_bank_assignment.grid(row=4, column=0, columnspan=2, padx=20, pady=10)

    # Button: Konto hinzufügen
    btn_account_addition = customtkinter.CTkButton(
        app, text="Konto hinzufügen",
        command=lambda: navigator.navigate("AccountAddition", selected_person=selected_person)
    )
    btn_account_addition.grid(row=5, column=0, columnspan=2, padx=20, pady=10)

    # Neuer Button: Konten bearbeiten
    btn_edit_accounts = customtkinter.CTkButton(
        app, text="Konten bearbeiten",
        command=lambda: navigator.navigate("AccountEditing", selected_person=selected_person)
    )
    btn_edit_accounts.grid(row=6, column=0, columnspan=2, padx=20, pady=10)

    # Optionaler Button: Calculate Festgeld (berechnet automatische Festgeldwerte)
    btn_calculate = customtkinter.CTkButton(
        app, text="Calculate Festgeld",
        command=lambda: account_controller.calculate_festgeld(selected_person)
    )
    btn_calculate.grid(row=7, column=0, columnspan=2, padx=20, pady=10)

    # Zurück-Button: Zur Personenauswahl
    btn_back = customtkinter.CTkButton(
        app, text="Zurück", command=lambda: navigator.navigate("PersonSelection")
    )
    btn_back.grid(row=8, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)
