# screens/screen_new_bank.py
import json
import customtkinter
from classen import Bank
from helper.universalMethoden import clear_ui, zentrieren

def new_bank_screen(app, navigator, **kwargs):
    clear_ui(app)

    def add_bank():
        name = entry_name.get().strip()
        bic = entry_bic.get().strip()
        if name and bic:
            neue_bank = Bank(name, bic)
            save_bank(neue_bank)
            entry_name.delete(0, "end")
            entry_bic.delete(0, "end")
        else:
            print("Bitte füllen Sie alle Felder aus!")
            if not name:
                entry_name.configure(fg_color="red")
            if not bic:
                entry_bic.configure(fg_color="red")

    def reset_bg(event):
        entry_name.configure(fg_color="white")
        entry_bic.configure(fg_color="white")

    def back():
        navigator.navigate("main_screen")

    def save_bank(bank):
        try:
            with open("banken.json", "r") as file:
                data = json.load(file)
                banks = data.get("Banken", [])
                for b in banks:
                    if b["Name"] == bank.name:
                        if bank.bic not in b["BIC"]:
                            b["BIC"].append(bank.bic)
                        break
                else:
                    banks.append({"Name": bank.name, "BIC": [bank.bic]})
            with open("banken.json", "w") as file:
                json.dump({"Banken": banks}, file, indent=4)
        except FileNotFoundError:
            with open("banken.json", "w") as file:
                json.dump({"Banken": [{"Name": bank.name, "BIC": [bank.bic]}]}, file, indent=4)

    label_name = customtkinter.CTkLabel(app, text="Name:")
    label_name.grid(row=0, column=0, padx=20, pady=10)
    entry_name = customtkinter.CTkEntry(app)
    entry_name.grid(row=0, column=1, padx=20, pady=10)
    entry_name.bind("<FocusIn>", reset_bg)

    label_bic = customtkinter.CTkLabel(app, text="BIC:")
    label_bic.grid(row=1, column=0, padx=20, pady=10)
    entry_bic = customtkinter.CTkEntry(app)
    entry_bic.grid(row=1, column=1, padx=20, pady=10)
    entry_bic.bind("<FocusIn>", reset_bg)

    btn_add = customtkinter.CTkButton(app, text="Hinzufügen", command=add_bank)
    btn_add.grid(row=2, column=0, columnspan=2, padx=20, pady=10)

    btn_back = customtkinter.CTkButton(app, text="Zurück", command=back)
    btn_back.grid(row=3, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)
