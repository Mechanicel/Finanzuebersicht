# screens/screen_bank_assignment.py
import json
import customtkinter
from helper.universalMethoden import clear_ui, zentrieren

def bank_assignment_screen(app, navigator, selected_person, **kwargs):
    clear_ui(app)

    def add_bank():
        bank_name = bank_var.get()
        if bank_name:
            try:
                with open("personen.json", "r") as file:
                    data = json.load(file)
                for person in data.get("personen", []):
                    if person["Name"] == selected_person["Name"] and person["Nachname"] == selected_person["Nachname"]:
                        banks = person.get("Banken", [])
                        if bank_name not in banks:
                            banks.append(bank_name)
                            person["Banken"] = banks
                            with open("personen.json", "w") as file:
                                json.dump(data, file, indent=4)
                            print(f"Bank {bank_name} hinzugefügt.")
                        else:
                            print("Die Bank ist bereits vorhanden.")
                        break
            except Exception as e:
                print(e)
        else:
            print("Bitte wählen Sie eine Bank aus!")

    try:
        with open("banken.json", "r") as file:
            data = json.load(file)
            banks = [b["Name"] for b in data.get("Banken", [])]
    except:
        banks = []

    label = customtkinter.CTkLabel(app, text="Bank auswählen:")
    label.grid(row=0, column=0, padx=20, pady=10)

    bank_var = customtkinter.StringVar()
    dropdown = customtkinter.CTkComboBox(app, variable=bank_var, values=banks, state="readonly")
    dropdown.grid(row=0, column=1, padx=20, pady=10)

    btn_add = customtkinter.CTkButton(app, text="Hinzufügen", command=add_bank)
    btn_add.grid(row=1, column=0, columnspan=2, padx=20, pady=10)

    btn_back = customtkinter.CTkButton(app, text="Zurück", command=lambda: navigator.navigate("person_info", selected_person=selected_person))
    btn_back.grid(row=2, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)
