import customtkinter
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.data.DataManager import DataManager


def create_screen(app, navigator, **kwargs):
    clear_ui(app)
    data_manager = DataManager()
    persons = data_manager.load_personen()
    person_list = [f"{p.get('Name', '')} {p.get('Nachname', '')}" for p in persons]

    def confirm():
        selected = selected_person_var.get()
        if " " in selected:
            vorname, nachname = selected.split(" ", 1)
            person = {"Name": vorname, "Nachname": nachname}
            navigator.navigate("PersonInfo", selected_person=person)
        else:
            print("Bitte eine gültige Person auswählen!")

    def back():
        navigator.navigate("MainScreen")

    label = customtkinter.CTkLabel(app, text="Person auswählen")
    label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)

    selected_person_var = customtkinter.StringVar()
    dropdown = customtkinter.CTkComboBox(app, variable=selected_person_var, values=person_list, state="readonly")
    dropdown.grid(row=1, column=0, padx=20, pady=10)

    btn_confirm = customtkinter.CTkButton(app, text="Bestätigen", command=confirm)
    btn_confirm.grid(row=2, column=0, columnspan=2, padx=20, pady=10)

    btn_back = customtkinter.CTkButton(app, text="Zurück", command=back)
    btn_back.grid(row=3, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)
