import customtkinter
import json
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.data.DataManager import DataManager


def create_screen(app, navigator, selected_person, **kwargs):
    clear_ui(app)
    data_manager = DataManager()
    person_data = data_manager.get_person_data(selected_person)
    fb = person_data.get("Freibetrag", {}) if person_data else {}
    row = 1

    def show_table(fb, start_row):
        total = 0.0
        header = customtkinter.CTkLabel(app, text="Freibeträge:")
        header.grid(row=0, column=0, columnspan=2, padx=20, pady=10)
        for bank, betrag in fb.items():
            lbl_bank = customtkinter.CTkLabel(app, text=bank)
            lbl_bank.grid(row=start_row, column=0, padx=20, pady=10)
            lbl_betrag = customtkinter.CTkLabel(app, text=betrag)
            lbl_betrag.grid(row=start_row, column=1, padx=20, pady=10)
            try:
                total += float(betrag)
            except:
                pass
            start_row += 1
        lbl_total = customtkinter.CTkLabel(app, text=f"Gesamtsumme: {total}")
        lbl_total.grid(row=start_row, column=0, columnspan=2, padx=20, pady=10)
        # Beispielhafte Farblogik: Grün bei <= 1000, sonst Rot
        if total <= 1000:
            lbl_total.configure(fg_color="green")
        else:
            lbl_total.configure(fg_color="red")

    show_table(fb, row)

    btn_back = customtkinter.CTkButton(app, text="Zurück", command=lambda: navigator.navigate("PersonInfo",
                                                                                              selected_person=selected_person))
    btn_back.grid(row=row + 1, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)
