import customtkinter
from FrontendService.src.helpers.UniversalMethoden import clear_ui, zentrieren
from FrontendService.src.models.AppState import AppState


def create_screen(app, navigator, state: AppState, **kwargs):
    clear_ui(app)
    # Lade Personen aus dem zentralen Store
    persons = state.personen
    person_list = [f"{p['Name']} {p['Nachname']}" for p in persons]

    def confirm():
        selected = selected_person_var.get()
        if " " in selected:
            vorname, nachname = selected.split(" ", 1)
            person = state.select_person(vorname, nachname)
            if person:
                navigator.navigate("PersonInfo")
            else:
                print("Person nicht gefunden.")
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