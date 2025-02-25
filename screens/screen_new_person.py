# screens/screen_new_person.py
import json
import customtkinter
from helper.universalMethoden import clear_ui, zentrieren

def new_person_screen(app, navigator, **kwargs):
    clear_ui(app)
    try:
        with open("personen.json", "r") as file:
            data = json.load(file)
            persons = data.get("personen", [])
    except:
        persons = []

    def proceed():
        name = entry_name.get().strip()
        nachname = entry_nachname.get().strip()
        if not name or not nachname:
            if not name:
                entry_name.configure(fg_color="lightcoral")
            if not nachname:
                entry_nachname.configure(fg_color="lightcoral")
            return
        if any(p.get("Name") == name and p.get("Nachname") == nachname for p in persons):
            print("Diese Person existiert bereits.")
            return
        neue_person = {"Name": name, "Nachname": nachname, "Freibetrag": {}, "Banken": []}
        persons.append(neue_person)
        with open("personen.json", "w") as file:
            json.dump({"personen": persons}, file, indent=4)
        navigator.navigate("main_screen")

    def reset_bg(event):
        entry_name.configure(fg_color="white")
        entry_nachname.configure(fg_color="white")

    label_name = customtkinter.CTkLabel(app, text="Name:")
    label_name.grid(row=0, column=0, padx=20, pady=10)
    entry_name = customtkinter.CTkEntry(app)
    entry_name.grid(row=0, column=1, padx=20, pady=10)
    entry_name.bind("<FocusIn>", reset_bg)

    label_nachname = customtkinter.CTkLabel(app, text="Nachname:")
    label_nachname.grid(row=1, column=0, padx=20, pady=10)
    entry_nachname = customtkinter.CTkEntry(app)
    entry_nachname.grid(row=1, column=1, padx=20, pady=10)
    entry_nachname.bind("<FocusIn>", reset_bg)

    btn_proceed = customtkinter.CTkButton(app, text="Fortfahren", command=proceed)
    btn_proceed.grid(row=2, column=0, columnspan=2, padx=20, pady=10)

    btn_back = customtkinter.CTkButton(app, text="Zurück", command=lambda: navigator.navigate("main_screen"))
    btn_back.grid(row=3, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)
