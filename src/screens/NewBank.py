import customtkinter
import json
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.data.DataManager import DataManager

def create_screen(app, navigator, **kwargs):
    clear_ui(app)
    data_manager = DataManager()

    def add_bank():
        name = entry_name.get().strip()
        bic = entry_bic.get().strip()
        if name and bic:
            bank_data = data_manager.load_bank_data()
            banks = bank_data.get("Banken", [])
            # Überprüfe, ob die Bank bereits existiert
            for bank in banks:
                if bank.get("Name") == name:
                    if bic not in bank.get("BIC", []):
                        bank["BIC"].append(bic)
                    break
            else:
                banks.append({"Name": name, "BIC": [bic]})
            try:
                with open(data_manager.banken_file, "w", encoding="utf-8") as f:
                    json.dump({"Banken": banks}, f, indent=4)
                print(f"Bank '{name}' hinzugefügt.")
                entry_name.delete(0, "end")
                entry_bic.delete(0, "end")
            except Exception as e:
                print("Fehler beim Speichern der Bankdaten:", e)
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
        navigator.navigate("MainScreen")

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

