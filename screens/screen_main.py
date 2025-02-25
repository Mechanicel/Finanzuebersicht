# screens/screen_main.py
import customtkinter
from helper.universalMethoden import clear_ui, zentrieren

def create_main_screen(app, navigator, **kwargs):
    clear_ui(app)
    title = customtkinter.CTkLabel(app, text="Person Wählen")
    title.grid(row=0, column=1, padx=20, pady=20)

    btn_person = customtkinter.CTkButton(app, text="Person Auswählen",
        command=lambda: navigator.navigate("person_selection"))
    btn_person.grid(row=1, column=0, padx=20, pady=20)

    btn_new_person = customtkinter.CTkButton(app, text="Neue Person Anlegen",
        command=lambda: navigator.navigate("new_person"))
    btn_new_person.grid(row=1, column=1, padx=20, pady=20)

    btn_new_bank = customtkinter.CTkButton(app, text="Neue Bank Anlegen",
        command=lambda: navigator.navigate("new_bank"))
    btn_new_bank.grid(row=1, column=2, padx=20, pady=20)

    zentrieren(app)
