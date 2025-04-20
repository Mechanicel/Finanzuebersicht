import customtkinter
from tkcalendar import DateEntry
from datetime import datetime
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.data.DataManager import DataManager
from src.controllers.AccountController import AccountController

def compute_iban_de(blz, kontonummer):
    """Erzeugt eine vereinfachte IBAN, ohne echte Prüfzifferberechnung."""
    return f"DE00{blz}{kontonummer}"

def load_own_accounts(selected_person, data_manager):
    """Lädt eigene Konten aus den Personendaten zur Auswahl (nicht Festgeld/Depot)."""
    person_data = data_manager.get_person_data(selected_person)
    own_accounts = []
    if person_data:
        for konto in person_data.get("Konten", []):
            if konto.get("Kontotyp") not in ["Festgeldkonto", "Depot"]:
                if "Kontonummer" in konto:
                    own_accounts.append(f"{konto['Kontotyp']} {konto['Kontonummer']}")
                elif "Deponummer" in konto:
                    own_accounts.append(f"{konto['Kontotyp']} {konto['Deponummer']}")
    return own_accounts if own_accounts else ["Bitte wählen"]

def create_screen(app, navigator, selected_person, **kwargs):
    clear_ui(app)
    data_manager = DataManager()
    account_controller = AccountController()

    # Allgemeine Variablen
    acct_var = customtkinter.StringVar(value="Bitte wählen")
    bank_var = customtkinter.StringVar(value="Bitte wählen")
    bic_var = customtkinter.StringVar(value="")
    blz_var = customtkinter.StringVar(value="")
    entries = {}

    # Variablen für Festgeld (Auszahlungskonto) und Depot (Verrechnungskonto)
    checkbox_fremdes_konto_fg = customtkinter.BooleanVar(value=False)
    fremde_iban_fg_var = customtkinter.StringVar(value="")
    own_account_fg_var = customtkinter.StringVar(value="Bitte wählen")

    checkbox_fremdes_konto_depot = customtkinter.BooleanVar(value=False)
    fremde_iban_depot_var = customtkinter.StringVar(value="")
    own_account_depot_var = customtkinter.StringVar(value="Bitte wählen")

    # Back-Button
    btn_back = customtkinter.CTkButton(
        app,
        text="Zurück",
        command=lambda: navigator.navigate("PersonInfo", selected_person=selected_person)
    )
    btn_back.grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky="w")

    def build_form():
        # Alle Widgets ab Zeile 2 entfernen
        for widget in app.grid_slaves():
            if int(widget.grid_info()["row"]) >= 2:
                widget.grid_forget()
        current_row = 2

        # Kontotyp-Dropdown (Daten aus kontotypen.json)
        label_acct = customtkinter.CTkLabel(app, text="Kontotyp:")
        label_acct.grid(row=current_row, column=0, padx=20, pady=10)
        kt_data = data_manager.load_kontotypen()
        account_types = [list(item.keys())[0] for item in kt_data.get("Kontotypen", [])]
        dropdown_acct = customtkinter.CTkOptionMenu(
            app, variable=acct_var, values=account_types, command=lambda _: build_form()
        )
        dropdown_acct.set(acct_var.get())
        dropdown_acct.grid(row=current_row, column=1, padx=20, pady=10)
        current_row += 1

        # Bank-Dropdown (aus den Personendaten)
        label_bank = customtkinter.CTkLabel(app, text="Bank:")
        label_bank.grid(row=current_row, column=0, padx=20, pady=10)
        person_data = data_manager.get_person_data(selected_person)
        banks = person_data.get("Banken", []) if person_data else []
        dropdown_bank = customtkinter.CTkOptionMenu(
            app, variable=bank_var, values=banks, command=lambda _: build_form()
        )
        dropdown_bank.set(bank_var.get())
        dropdown_bank.grid(row=current_row, column=1, padx=20, pady=10)
        current_row += 1

        # BIC (abhängig von ausgewählter Bank)
        selected_bank = bank_var.get()
        if selected_bank not in ["", "Bitte wählen"]:
            bank_data = data_manager.load_bank_data()
            bics = []
            for bank in bank_data.get("Banken", []):
                if bank.get("Name") == selected_bank:
                    bics = bank.get("BIC", [])
                    break
            if len(bics) > 1:
                label_bic = customtkinter.CTkLabel(app, text="BIC:")
                label_bic.grid(row=current_row, column=0, padx=20, pady=10)
                dropdown_bic = customtkinter.CTkOptionMenu(app, variable=bic_var, values=bics)
                if bic_var.get() not in bics:
                    bic_var.set(bics[0])
                dropdown_bic.grid(row=current_row, column=1, padx=20, pady=10)
                current_row += 1
            elif len(bics) == 1:
                bic_var.set(bics[0])
                label_bic = customtkinter.CTkLabel(app, text=f"BIC: {bics[0]}")
                label_bic.grid(row=current_row, column=0, columnspan=2, padx=20, pady=10)
                current_row += 1
            else:
                bic_var.set("")
                label_bic = customtkinter.CTkLabel(app, text="Keine BIC gefunden.")
                label_bic.grid(row=current_row, column=0, columnspan=2, padx=20, pady=10)
                current_row += 1

        # BLZ (analog)
        if selected_bank not in ["", "Bitte wählen"]:
            bank_data = data_manager.load_bank_data()
            blzs = []
            for bank in bank_data.get("Banken", []):
                if bank.get("Name") == selected_bank:
                    blzs = bank.get("BLZ", [])
                    break
            if len(blzs) > 1:
                label_blz = customtkinter.CTkLabel(app, text="BLZ:")
                label_blz.grid(row=current_row, column=0, padx=20, pady=10)
                dropdown_blz = customtkinter.CTkOptionMenu(app, variable=blz_var, values=blzs)
                if blz_var.get() not in blzs:
                    blz_var.set(blzs[0])
                dropdown_blz.grid(row=current_row, column=1, padx=20, pady=10)
                current_row += 1
            elif len(blzs) == 1:
                blz_var.set(blzs[0])
                label_blz = customtkinter.CTkLabel(app, text=f"BLZ: {blzs[0]}")
                label_blz.grid(row=current_row, column=0, columnspan=2, padx=20, pady=10)
                current_row += 1
            else:
                blz_var.set("")
                label_blz = customtkinter.CTkLabel(app, text="Keine BLZ gefunden.")
                label_blz.grid(row=current_row, column=0, columnspan=2, padx=20, pady=10)
                current_row += 1

        # Zusätzliche Felder basierend auf Kontotyp
        acct_type = acct_var.get()
        fields = []
        for item in kt_data.get("Kontotypen", []):
            if acct_type in item:
                fields = item[acct_type]
                break

        if acct_type != "Bitte wählen":
            for field in fields:
                # Felder, die automatisch belegt werden, überspringen wir
                if field in ["Bank", "BIC", "Erstellungsdatum"]:
                    continue

                # Behandlung für Festgeldkonto: Auszahlungskonto
                if acct_type == "Festgeldkonto" and field == "Auszahlungskonto":
                    label_aus = customtkinter.CTkLabel(app, text="Auszahlungskonto:")
                    label_aus.grid(row=current_row, column=0, padx=20, pady=10)
                    check_fg = customtkinter.CTkCheckBox(
                        app,
                        text="Fremdes Konto?",
                        variable=checkbox_fremdes_konto_fg,
                        command=lambda: build_form()
                    )
                    check_fg.grid(row=current_row, column=1, padx=20, pady=10)
                    current_row += 1

                    if checkbox_fremdes_konto_fg.get():
                        label_iban = customtkinter.CTkLabel(app, text="IBAN:")
                        label_iban.grid(row=current_row, column=0, padx=20, pady=10)
                        entry_iban = customtkinter.CTkEntry(app, textvariable=fremde_iban_fg_var)
                        entry_iban.grid(row=current_row, column=1, padx=20, pady=10)
                        current_row += 1
                    else:
                        label_ok = customtkinter.CTkLabel(app, text="Eigenes Konto:")
                        label_ok.grid(row=current_row, column=0, padx=20, pady=10)
                        own_acc_list = load_own_accounts(selected_person, data_manager)
                        dropdown_ok = customtkinter.CTkOptionMenu(
                            app,
                            variable=own_account_fg_var,
                            values=own_acc_list
                        )
                        dropdown_ok.grid(row=current_row, column=1, padx=20, pady=10)
                        current_row += 1
                    continue

                # Behandlung für Depot: Verrechnungskonto
                if acct_type == "Depot" and field == "Verrechnungskonto":
                    label_vk = customtkinter.CTkLabel(app, text="Verrechnungskonto:")
                    label_vk.grid(row=current_row, column=0, padx=20, pady=10)
                    check_depot = customtkinter.CTkCheckBox(
                        app,
                        text="Fremdes Konto?",
                        variable=checkbox_fremdes_konto_depot,
                        command=lambda: build_form()
                    )
                    check_depot.grid(row=current_row, column=1, padx=20, pady=10)
                    current_row += 1

                    if checkbox_fremdes_konto_depot.get():
                        label_iban = customtkinter.CTkLabel(app, text="IBAN:")
                        label_iban.grid(row=current_row, column=0, padx=20, pady=10)
                        entry_iban = customtkinter.CTkEntry(app, textvariable=fremde_iban_depot_var)
                        entry_iban.grid(row=current_row, column=1, padx=20, pady=10)
                        current_row += 1
                    else:
                        label_ok = customtkinter.CTkLabel(app, text="Eigenes Konto:")
                        label_ok.grid(row=current_row, column=0, padx=20, pady=10)
                        own_acc_list = load_own_accounts(selected_person, data_manager)
                        dropdown_ok = customtkinter.CTkOptionMenu(
                            app,
                            variable=own_account_depot_var,
                            values=own_acc_list
                        )
                        dropdown_ok.grid(row=current_row, column=1, padx=20, pady=10)
                        current_row += 1
                    continue

                # Standardfelder
                label_f = customtkinter.CTkLabel(app, text=f"{field}:")
                label_f.grid(row=current_row, column=0, padx=20, pady=10)
                if field not in entries:
                    entries[field] = customtkinter.CTkEntry(app)
                entries[field].grid(row=current_row, column=1, padx=20, pady=10)
                current_row += 1

        btn_add.grid(row=current_row, column=0, columnspan=2, padx=20, pady=10)

    def add_account():
        acct_type = acct_var.get()
        if acct_type == "Bitte wählen":
            print("Bitte wählen Sie einen Kontotyp aus.")
            return
        selected_bank = bank_var.get()
        if selected_bank in ["", "Bitte wählen"]:
            print("Bitte wählen Sie eine Bank aus.")
            return

        selected_bic = bic_var.get() if bic_var.get() else ""
        selected_blz = blz_var.get()

        acct_data = {"Bank": selected_bank, "BIC": selected_bic}
        if selected_blz:
            acct_data["BLZ"] = selected_blz

        for field in entries:
            val = entries[field].get().strip()
            if not val:
                print(f"Bitte füllen Sie das Feld '{field}' aus!")
                return
            acct_data[field] = val

        # Spezielle Verarbeitung für Festgeldkonto
        if acct_type == "Festgeldkonto":
            if checkbox_fremdes_konto_fg.get():
                iban = fremde_iban_fg_var.get().strip()
                if not iban:
                    print("Bitte IBAN für fremdes Konto eingeben!")
                    return
                acct_data["Auszahlungskonto"] = iban
            else:
                auswahl = own_account_fg_var.get()
                if auswahl in ["", "Bitte wählen"]:
                    print("Bitte ein eigenes Konto auswählen!")
                    return
                parts = auswahl.split()
                if len(parts) == 2:
                    kontonummer = parts[1]
                    if selected_blz:
                        iban_eigen = compute_iban_de(selected_blz, kontonummer)
                        acct_data["Auszahlungskonto"] = iban_eigen
                    else:
                        print("Keine BLZ ausgewählt, IBAN kann nicht berechnet werden!")
                        return
                else:
                    print("Auszahlungskonto konnte nicht geparst werden!")
                    return
        # Spezielle Verarbeitung für Depot
        elif acct_type == "Depot":
            if checkbox_fremdes_konto_depot.get():
                iban = fremde_iban_depot_var.get().strip()
                if not iban:
                    print("Bitte IBAN für fremdes Verrechnungskonto eingeben!")
                    return
                acct_data["Verrechnungskonto"] = iban
            else:
                auswahl = own_account_depot_var.get()
                if auswahl in ["", "Bitte wählen"]:
                    print("Bitte ein eigenes Konto auswählen!")
                    return
                parts = auswahl.split()
                if len(parts) == 2:
                    kontonummer = parts[1]
                    if selected_blz:
                        iban_eigen = compute_iban_de(selected_blz, kontonummer)
                        acct_data["Verrechnungskonto"] = iban_eigen
                    else:
                        print("Keine BLZ ausgewählt, IBAN kann nicht berechnet werden!")
                        return
                else:
                    print("Verrechnungskonto konnte nicht geparst werden!")
                    return

        acct_data["Kontotyp"] = acct_type

        # Hier wird das Konto über den AccountController in die JSON hinzugefügt
        if account_controller.add_account(selected_person, acct_type, acct_data):
            print(f"Konto vom Typ {acct_type} hinzugefügt.")
            reset_form()
            navigator.navigate("PersonInfo", selected_person=selected_person)
        else:
            print("Konto konnte nicht hinzugefügt werden (Duplikat vorhanden oder Fehler).")

    def reset_form():
        acct_var.set("Bitte wählen")
        bank_var.set("Bitte wählen")
        bic_var.set("")
        blz_var.set("")
        checkbox_fremdes_konto_fg.set(False)
        fremde_iban_fg_var.set("")
        own_account_fg_var.set("Bitte wählen")
        checkbox_fremdes_konto_depot.set(False)
        fremde_iban_depot_var.set("")
        own_account_depot_var.set("Bitte wählen")
        for e in entries.values():
            e.delete(0, "end")

    btn_add = customtkinter.CTkButton(app, text="Hinzufügen", command=add_account)

    build_form()
    zentrieren(app)
