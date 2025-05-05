import customtkinter
from FrontendService.src.helpers.UniversalMethoden import clear_ui, zentrieren
from FrontendService.src.models.AppState import AppState


def create_screen(app, navigator, state: AppState, **kwargs):
    clear_ui(app)
    person = state.selected_person
    banks = [b['Name'] for b in state.banken]

    var = customtkinter.StringVar()
    customtkinter.CTkLabel(app, text="Bank auswählen:").grid(row=0, column=0, padx=20, pady=10)
    customtkinter.CTkComboBox(app, variable=var, values=banks, state="readonly").grid(row=0, column=1, padx=20, pady=10)

    def add():
        name = var.get()
        if name and name not in person['Banken']:
            person['Banken'].append(name)
            state.save_person(person)
            print(f"Bank '{name}' hinzugefügt.")
        else:
            print("Bitte wählen Sie eine neue Bank aus.")

    customtkinter.CTkButton(app, text="Hinzufügen", command=add).grid(row=1, column=0, columnspan=2, padx=20, pady=10)
    customtkinter.CTkButton(app, text="Zurück", command=lambda: navigator.navigate("PersonInfo")).grid(row=2, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)