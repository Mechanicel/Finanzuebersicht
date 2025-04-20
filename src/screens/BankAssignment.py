import customtkinter
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.data.DataManager import DataManager


def create_screen(app, navigator, selected_person, **kwargs):
    clear_ui(app)
    data_manager = DataManager()

    def add_bank():
        bank_name = bank_var.get()
        if bank_name:
            person_data = data_manager.get_person_data(selected_person)
            if person_data:
                banken = person_data.get("Banken", [])
                if bank_name not in banken:
                    banken.append(bank_name)
                    person_data["Banken"] = banken
                    data_manager.save_person_data(person_data)
                    print(f"Bank '{bank_name}' hinzugefügt.")
                else:
                    print("Die Bank ist bereits vorhanden.")
            else:
                print("Personendaten nicht gefunden.")
        else:
            print("Bitte wählen Sie eine Bank aus!")

    # Lade alle verfügbaren Banken aus der Banken-Datenbank
    bank_data = data_manager.load_bank_data()
    banken_liste = [bank.get("Name") for bank in bank_data.get("Banken", [])]

    label = customtkinter.CTkLabel(app, text="Bank auswählen:")
    label.grid(row=0, column=0, padx=20, pady=10)

    bank_var = customtkinter.StringVar()
    dropdown = customtkinter.CTkComboBox(app, variable=bank_var, values=banken_liste, state="readonly")
    dropdown.grid(row=0, column=1, padx=20, pady=10)

    btn_add = customtkinter.CTkButton(app, text="Hinzufügen", command=add_bank)
    btn_add.grid(row=1, column=0, columnspan=2, padx=20, pady=10)

    btn_back = customtkinter.CTkButton(app, text="Zurück", command=lambda: navigator.navigate("PersonInfo",
                                                                                              selected_person=selected_person))
    btn_back.grid(row=2, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)

