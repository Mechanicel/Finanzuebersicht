import customtkinter
from tkcalendar import DateEntry
from datetime import datetime
from helpers.UniversalMethoden import clear_ui, zentrieren
from data.DataManager import DataManager
from controllers.AccountController import AccountController

def create_screen(app, navigator, selected_person, **kwargs):
    clear_ui(app)
    data_manager = DataManager()
    account_controller = AccountController()
    person_data = data_manager.get_person_data(selected_person) or {}
    konten = person_data.get("Konten", [])

    index = [0]  # Zähler für aktuelles Konto

    # Zurück‑Button
    customtkinter.CTkButton(
        app, text="Zurück",
        command=lambda: navigator.navigate("PersonInfo", selected_person=selected_person)
    ).grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky="w")

    # Kontoinfo-Label
    label_acct = customtkinter.CTkLabel(app, text="Konto:")
    label_acct.grid(row=1, column=0, columnspan=2, padx=20, pady=10)

    # Eingabe Kontostand
    customtkinter.CTkLabel(app, text="Kontostand:").grid(row=2, column=0, padx=20, pady=10)
    entry_balance = customtkinter.CTkEntry(app)
    entry_balance.grid(row=2, column=1, padx=20, pady=10)

    # Datumsauswahl
    customtkinter.CTkLabel(app, text="Datum:").grid(row=3, column=0, padx=20, pady=10)
    entry_date = DateEntry(app, date_pattern='yyyy-mm-dd')
    entry_date.grid(row=3, column=1, padx=20, pady=10)

    # Navigation Buttons
    btn_next = customtkinter.CTkButton(app, text="Weiter")
    btn_next.grid(row=4, column=0, columnspan=2, padx=20, pady=10)
    btn_finish = customtkinter.CTkButton(app, text="Fertig", state="disabled")
    btn_finish.grid(row=5, column=0, columnspan=2, padx=20, pady=10)

    def update_ui():
        # Skip Festgeld- & Depotkonten
        while index[0] < len(konten) and konten[index[0]].get("Kontotyp") in ["Festgeldkonto", "Depot"]:
            index[0] += 1

        if index[0] < len(konten):
            acct = konten[index[0]]
            lines = []
            for f in ("Kontotyp", "Bank", "BIC", "Kontonummer", "Deponummer"):
                if f in acct:
                    lines.append(f"{f}: {acct[f]}")
            label_acct.configure(text="\n".join(lines))

            entry_balance.configure(state="normal")
            entry_balance.delete(0, customtkinter.END)
            entry_date.set_date(datetime.today())
            entry_date.configure(state="normal")
            btn_next.configure(state="normal")
            btn_finish.configure(state="disabled")
        else:
            # Am Ende: Festgeld UND Depot berechnen
            account_controller.calculate(selected_person)
            navigator.navigate("PersonInfo", selected_person=selected_person)

    def save_account():
        acct = konten[index[0]]
        val = entry_balance.get().strip()
        try:
            saldo = float(val)
        except ValueError:
            print(f"Ungültiger Kontostand: '{val}'")
            return False
        data_manager.save_account_balance(
            selected_person,
            acct,
            saldo,
            entry_date.get_date()
        )
        return True

    def next_account():
        # Speichern, falls erlaubt
        if konten[index[0]].get("Kontotyp") not in ["Festgeldkonto", "Depot"]:
            if not save_account():
                return
        index[0] += 1
        update_ui()

    # Bindings
    btn_next.configure(command=next_account)
    btn_finish.configure(command=lambda: navigator.navigate("PersonInfo", selected_person=selected_person))
    entry_balance.bind("<KeyRelease>", lambda e: btn_finish.configure(state="normal"))

    # Start
    update_ui()
    zentrieren(app)
