# screens/screen_freibetrag_input.py
import json
import customtkinter
from helper.universalMethoden import clear_ui, zentrieren

def freibetrag_input_screen(app, navigator, selected_person, **kwargs):
    clear_ui(app)

    def add_freibetrag():
        bank = bank_dropdown.get()
        betrag = entry_betrag.get().strip()
        if bank and betrag:
            try:
                with open("personen.json", "r") as file:
                    data = json.load(file)
                for person in data.get("personen", []):
                    if person["Name"] == selected_person["Name"] and person["Nachname"] == selected_person["Nachname"]:
                        fb = person.get("Freibetrag", {})
                        fb[bank] = betrag
                        person["Freibetrag"] = fb
                        with open("personen.json", "w") as file:
                            json.dump(data, file, indent=4)
                        print(f"Freibetrag {betrag} für {bank} hinzugefügt.")
                        entry_betrag.delete(0, "end")
                        break
            except Exception as e:
                print(e)
        else:
            print("Bitte alle Felder ausfüllen!")

    def back():
        navigator.navigate("person_info", selected_person=selected_person)

    def load_banks():
        try:
            with open("personen.json", "r") as file:
                data = json.load(file)
            for person in data.get("personen", []):
                if person["Name"] == selected_person["Name"] and person["Nachname"] == selected_person["Nachname"]:
                    return person.get("Banken", [])
        except:
            return []

    label_bank = customtkinter.CTkLabel(app, text="Bank:")
    label_bank.grid(row=0, column=0, padx=20, pady=10)
    banks = load_banks()
    bank_dropdown = customtkinter.CTkComboBox(app, values=banks)
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
