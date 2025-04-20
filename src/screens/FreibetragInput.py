import customtkinter
import json
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.data.DataManager import DataManager


def create_screen(app, navigator, selected_person, **kwargs):
    clear_ui(app)
    data_manager = DataManager()

    def add_freibetrag():
        bank = bank_dropdown.get()
        betrag = entry_betrag.get().strip()
        if bank and betrag:
            person_data = data_manager.get_person_data(selected_person)
            if person_data:
                fb = person_data.get("Freibetrag", {})
                fb[bank] = betrag
                person_data["Freibetrag"] = fb
                data_manager.save_person_data(person_data)
                print(f"Freibetrag {betrag} für {bank} hinzugefügt.")
                entry_betrag.delete(0, "end")
            else:
                print("Personendaten nicht gefunden.")
        else:
            print("Bitte alle Felder ausfüllen!")

    def back():
        navigator.navigate("PersonInfo", selected_person=selected_person)

    def load_banken():
        person_data = data_manager.get_person_data(selected_person)
        if person_data:
            return person_data.get("Banken", [])
        return []

    label_bank = customtkinter.CTkLabel(app, text="Bank:")
    label_bank.grid(row=0, column=0, padx=20, pady=10)
    banken_liste = load_banken()
    bank_dropdown = customtkinter.CTkComboBox(app, values=banken_liste, state="readonly")
    bank_dropdown.grid(row=0, column=1, padx=20, pady=10)

    label_betrag = customtkinter.CTkLabel(app, text="Freibetrag:")
    label_betrag.grid(row=1, column=0, padx=20, pady=10)
    entry_betrag = customtkinter.CTkEntry(app)
    entry_betrag.grid(row=1, column=1, padx=20, pady=10)

    btn_add = customtkinter.CTkButton(app, text="Hinzufügen", command=add_freibetrag)
    btn_add.grid(row=2, column=0, columnspan=2, padx=20, pady=10)

    btn_back = customtkinter.CTkButton(app, text="Zurück", command=back)
    btn_back.grid(row=3, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)

