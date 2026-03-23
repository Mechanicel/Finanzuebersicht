import customtkinter as ctk

from src.models.AppState import AppState
from src.ui.components import create_page, section_card, action_bar_grid, primary_button, set_status


def create_screen(app, navigator, state: AppState, **kwargs):
    ui = create_page(app, "Neue Bank", "Bankname und BIC erfassen.", back_command=lambda: navigator.navigate("MainScreen"))
    status = ui["status"]

    _, body = section_card(ui["content"], "Bankdaten")

    name_var = ctk.StringVar()
    bic_var = ctk.StringVar()

    ctk.CTkLabel(body, text="Bankname *").grid(row=0, column=0, sticky="w", pady=(0, 4))
    entry_name = ctk.CTkEntry(body, textvariable=name_var)
    entry_name.grid(row=1, column=0, sticky="ew", pady=(0, 8))

    ctk.CTkLabel(body, text="BIC *").grid(row=2, column=0, sticky="w", pady=(0, 4))
    entry_bic = ctk.CTkEntry(body, textvariable=bic_var)
    entry_bic.grid(row=3, column=0, sticky="ew")

    def add_bank():
        name = name_var.get().strip()
        bic = bic_var.get().strip()

        entry_name.configure(border_color=("#565B5E", "#565B5E"))
        entry_bic.configure(border_color=("#565B5E", "#565B5E"))

        if not name or not bic:
            if not name:
                entry_name.configure(border_color="#B00020")
            if not bic:
                entry_bic.configure(border_color="#B00020")
            set_status(status, "Bitte füllen Sie alle Felder aus.", "warning")
            return

        banks = state.banken
        for bank in banks:
            if bank["Name"] == name:
                if bic not in bank.get("BIC", []):
                    bank["BIC"].append(bic)
                    set_status(status, "BIC zur bestehenden Bank hinzugefügt.", "success")
                else:
                    set_status(status, "Diese BIC existiert bereits für die Bank.", "info")
                break
        else:
            banks.append({"Name": name, "BIC": [bic]})
            set_status(status, "Neue Bank erfolgreich angelegt.", "success")

        state.data_manager.save_bank_data({"Banken": banks})
        state.banken = banks
        name_var.set("")
        bic_var.set("")

    bar = action_bar_grid(body, row=4)
    primary_button(bar, "Bank speichern", add_bank, column=0)
