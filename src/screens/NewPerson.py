import customtkinter
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.data.DataManager import DataManager

def create_screen(app, navigator, **kwargs):
    clear_ui(app)
    data_manager = DataManager()
    persons = data_manager.load_personen()

    def proceed():
        name = entry_name.get().strip()
        nachname = entry_nachname.get().strip()
        if not name or not nachname:
            if not name:
                entry_name.configure(fg_color="lightcoral")
            if not nachname:
                entry_nachname.configure(fg_color="lightcoral")
            return
        # Prüfen, ob die Person bereits existiert
        for p in persons:
            if p.get("Name") == name and p.get("Nachname") == nachname:
                print("Diese Person existiert bereits.")
                return
        new_person = {
            "Name": name,
            "Nachname": nachname,
            "Freibetrag": {},
            "Banken": [],
            "Konten": []
        }
        persons.append(new_person)
        data_manager.save_personen(persons)
        navigator.navigate("MainScreen")

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

    btn_back = customtkinter.CTkButton(app, text="Zurück", command=lambda: navigator.navigate("MainScreen"))
    btn_back.grid(row=3, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)

