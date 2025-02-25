# screens/screen_person_selection.py
import json
import customtkinter
from helper.universalMethoden import clear_ui, zentrieren

def person_selection_screen(app, navigator, **kwargs):
    clear_ui(app)

    def confirm():
        selected = selected_person_var.get()
        if " " in selected:
            vorname, nachname = selected.split(" ", 1)
            person = {"Name": vorname, "Nachname": nachname}
            navigator.navigate("person_info", selected_person=person)
        else:
            print("Bitte eine gültige Person auswählen!")

    def back():
        navigator.navigate("main_screen")

    try:
        with open("personen.json", "r") as file:
            data = json.load(file)
            persons = [f"{p['Name']} {p['Nachname']}" for p in data.get("personen", [])]
    except:
        persons = []

    label = customtkinter.CTkLabel(app, text="Person Auswählen")
    label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)

    selected_person_var = customtkinter.StringVar()
    dropdown = customtkinter.CTkComboBox(app, variable=selected_person_var, values=persons, state="readonly")
    dropdown.grid(row=1, column=0, padx=20, pady=10)

    btn_confirm = customtkinter.CTkButton(app, text="Bestätigen", command=confirm)
    btn_confirm.grid(row=2, column=0, columnspan=2, padx=20, pady=10)

    btn_back = customtkinter.CTkButton(app, text="Zurück", command=back)
    btn_back.grid(row=3, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)
