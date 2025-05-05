import customtkinter
from FrontendService.src.helpers.UniversalMethoden import clear_ui, zentrieren
from FrontendService.src.models.AppState import AppState


def create_screen(app, navigator, state: AppState, **kwargs):
    clear_ui(app)
    person = state.selected_person
    customtkinter.CTkLabel(app, text=f"{person['Name']} {person['Nachname']}").grid(row=0, column=0, columnspan=2, padx=20, pady=10)

    customtkinter.CTkButton(app, text="Kontozusammenfassung", command=lambda: navigator.navigate("AccountSummary")).grid(row=1, column=0, columnspan=2, padx=20, pady=10)
    customtkinter.CTkButton(app, text="Freibetrag eingeben", command=lambda: navigator.navigate("FreibetragInput")).grid(row=2, column=0, columnspan=2, padx=20, pady=10)
    customtkinter.CTkButton(app, text="Kontoübersicht", command=lambda: navigator.navigate("AccountOverview")).grid(row=3, column=0, columnspan=2, padx=20, pady=10)
    customtkinter.CTkButton(app, text="Bank hinzufügen", command=lambda: navigator.navigate("BankAssignment")).grid(row=4, column=0, columnspan=2, padx=20, pady=10)
    customtkinter.CTkButton(app, text="Konto hinzufügen", command=lambda: navigator.navigate("AccountAddition")).grid(row=5, column=0, columnspan=2, padx=20, pady=10)
    customtkinter.CTkButton(app, text="Konten bearbeiten", command=lambda: navigator.navigate("AccountEditing")).grid(row=6, column=0, columnspan=2, padx=20, pady=10)
    customtkinter.CTkButton(app, text="Zurück", command=lambda: navigator.navigate("PersonSelection")).grid(row=7, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)