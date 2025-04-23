import customtkinter
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.models.AppState import AppState


def create_screen(app, navigator, state: AppState, **kwargs):
    clear_ui(app)
    person = state.selected_person
    banken = person.get('Banken', [])

    var = customtkinter.StringVar()
    amt = customtkinter.StringVar()

    customtkinter.CTkLabel(app, text="Bank:").grid(row=0, column=0, padx=20, pady=10)
    customtkinter.CTkComboBox(app, variable=var, values=banken, state="readonly").grid(row=0, column=1, padx=20, pady=10)
    customtkinter.CTkLabel(app, text="Freibetrag:").grid(row=1, column=0, padx=20, pady=10)
    customtkinter.CTkEntry(app, textvariable=amt).grid(row=1, column=1, padx=20, pady=10)

    def add():
        b = var.get(); wert = amt.get().strip()
        if b and wert:
            person['Freibetrag'][b] = wert
            state.save_person(person)
            print(f"Freibetrag {wert} für {b} hinzugefügt.")
        else:
            print("Bitte alle Felder ausfüllen!")

    customtkinter.CTkButton(app, text="Hinzufügen", command=add).grid(row=2, column=0, columnspan=2, padx=20, pady=10)
    customtkinter.CTkButton(app, text="Zurück", command=lambda: navigator.navigate("PersonInfo")).grid(row=3, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)