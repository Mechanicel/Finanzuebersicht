# screens/screen_freibetrag_display.py
import json
import customtkinter
from helper.universalMethoden import clear_ui, zentrieren

def freibetrag_display_screen(app, navigator, selected_person, **kwargs):
    clear_ui(app)
    row = 1

    def show_table(fb, start_row):
        total = 0
        header = customtkinter.CTkLabel(app, text="Freibeträge:")
        header.grid(row=0, column=0, columnspan=2, padx=20, pady=10)
        for bank, betrag in fb.items():
            lbl_bank = customtkinter.CTkLabel(app, text=bank)
            lbl_bank.grid(row=start_row, column=0, padx=20, pady=10)
            lbl_betrag = customtkinter.CTkLabel(app, text=betrag)
            lbl_betrag.grid(row=start_row, column=1, padx=20, pady=10)
            total += float(betrag)
            start_row += 1
        lbl_total = customtkinter.CTkLabel(app, text=f"Gesamtsumme: {total}")
        lbl_total.grid(row=start_row, column=0, columnspan=2, padx=20, pady=10)
        if total <= 1000:
            lbl_total.configure(fg_color="green")
        else:
            lbl_total.configure(fg_color="red")

    try:
        with open("personen.json", "r") as file:
            data = json.load(file)
        for person in data.get("personen", []):
            if person["Name"] == selected_person["Name"] and person["Nachname"] == selected_person["Nachname"]:
                fb = person.get("Freibetrag", {})
                show_table(fb, row)
                break
    except Exception as e:
        print(e)

    btn_back = customtkinter.CTkButton(app, text="Zurück", command=lambda: navigator.navigate("person_info", selected_person=selected_person))
    btn_back.grid(row=row+1, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)
