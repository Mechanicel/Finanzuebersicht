# screens/screen_account_addition.py

from datetime import datetime
import json
import customtkinter
from tkcalendar import DateEntry
from helper.universalMethoden import clear_ui, zentrieren

# Hilfsfunktionen
from helper.account_addition_helpers import (
    load_account_types,
    load_banks_for_person,
    get_bics_for_bank,
    get_blzs_for_bank,
    load_own_accounts,
    duplicate_account,
    update_account,
    compute_iban_de
)

def account_addition_screen(app, navigator, selected_person, **kwargs):
    """
    Screen zum Hinzufügen eines neuen Kontos für die übergebene Person.

    Besondere Logik für:
      1) Festgeldkonto:
         - Laufzeit_in_Tagen, Anlagedatum, Zinsintervall, Anlagebetrag, Zinssatz
         - Auszahlungskonto (Checkbox fremdes Konto / eigenes Konto)
      2) Depot:
         - Deponummer
         - Verrechnungskonto (Checkbox fremdes Konto / eigenes Konto), analog zu 'Auszahlungskonto' bei Festgeld
           => Falls fremd: IBAN-Eingabe
           => Falls eigenes: Dropdown eigener Konten + IBAN-Berechnung aus BLZ + Kontonummer

    Erstellungsdatum wird bei Festgeld ignoriert, falls es in kontotypen.json vorhanden ist.
    """

    clear_ui(app)

    # Zurück-Button
    btn_back = customtkinter.CTkButton(
        app,
        text="Zurück",
        command=lambda: navigator.navigate("person_info", selected_person=selected_person)
    )
    btn_back.grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky='w')

    # Hauptvariablen
    acct_var = customtkinter.StringVar(value="Bitte wählen")  # Kontotyp
    bank_var = customtkinter.StringVar(value="Bitte wählen")  # Bank
    bic_var = customtkinter.StringVar(value="")               # BIC
    blz_var = customtkinter.StringVar(value="")               # BLZ

    # Allgemeine Eingabefelder (z. B. Kontonummer)
    entries = {}

    # Festgeld-spezifisch
    checkbox_fremdes_konto_fg = customtkinter.BooleanVar(value=False)
    fremde_iban_fg_var = customtkinter.StringVar(value="")
    own_account_fg_var = customtkinter.StringVar(value="Bitte wählen")

    # Depot-spezifisch (Verrechnungskonto)
    checkbox_fremdes_konto_depot = customtkinter.BooleanVar(value=False)
    fremde_iban_depot_var = customtkinter.StringVar(value="")
    own_account_depot_var = customtkinter.StringVar(value="Bitte wählen")

    # Beispiele für Zinsintervall
    zinsinterval_values = ["monatlich", "vierteljährlich", "jährlich"]

    # Kontotypen aus JSON laden
    field_list = load_account_types()

    def build_form():
        # Entferne vorherige Widgets ab Zeile 2
        for widget in app.grid_slaves():
            if int(widget.grid_info()["row"]) >= 2:
                widget.grid_forget()

        current_row = 2

        # Kontotyp
        label_acct = customtkinter.CTkLabel(app, text="Kontotyp:")
        label_acct.grid(row=current_row, column=0, padx=20, pady=10)
        dropdown_acct = customtkinter.CTkOptionMenu(
            app,
            variable=acct_var,
            values=list(field_list.keys()),
            command=lambda _: build_form()
        )
        dropdown_acct.set(acct_var.get())
        dropdown_acct.grid(row=current_row, column=1, padx=20, pady=10)
        current_row += 1

        # Bank
        label_bank = customtkinter.CTkLabel(app, text="Bank:")
        label_bank.grid(row=current_row, column=0, padx=20, pady=10)
        banks = load_banks_for_person(selected_person)
        dropdown_bank = customtkinter.CTkOptionMenu(
            app,
            variable=bank_var,
            values=banks,
            command=lambda _: build_form()
        )
        dropdown_bank.set(bank_var.get())
        dropdown_bank.grid(row=current_row, column=1, padx=20, pady=10)
        current_row += 1

        # BIC
        selected_bank = bank_var.get()
        if selected_bank not in ["", "Bitte wählen"]:
            bics = get_bics_for_bank(selected_bank)
            if len(bics) > 1:
                label_bic = customtkinter.CTkLabel(app, text="BIC:")
                label_bic.grid(row=current_row, column=0, padx=20, pady=10)
                dropdown_bic = customtkinter.CTkOptionMenu(app, variable=bic_var, values=bics)
                if bic_var.get() in bics:
                    dropdown_bic.set(bic_var.get())
                else:
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

        # BLZ
        if selected_bank not in ["", "Bitte wählen"]:
            blzs = get_blzs_for_bank(selected_bank)
            if len(blzs) > 1:
                label_blz = customtkinter.CTkLabel(app, text="BLZ:")
                label_blz.grid(row=current_row, column=0, padx=20, pady=10)
                dropdown_blz = customtkinter.CTkOptionMenu(app, variable=blz_var, values=blzs)
                if blz_var.get() in blzs:
                    dropdown_blz.set(blz_var.get())
                else:
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

        # Basierend auf Kontotyp Felder anlegen
        acct_type = acct_var.get()
        if acct_type != "Bitte wählen":
            fields = field_list.get(acct_type, [])

            if acct_type == "Festgeldkonto":
                # Festgeld-Felder
                for field in fields:
                    if field in ["Bank", "BIC", "Erstellungsdatum"]:
                        continue
                    if field == "Anlagedatum":
                        label_ad = customtkinter.CTkLabel(app, text="Anlagedatum:")
                        label_ad.grid(row=current_row, column=0, padx=20, pady=10)
                        if "Anlagedatum" not in entries:
                            entries["Anlagedatum"] = DateEntry(app, date_pattern="yyyy-mm-dd")
                        entries["Anlagedatum"].grid(row=current_row, column=1, padx=20, pady=10)
                        current_row += 1
                        continue
                    if field == "Laufzeit_in_Tagen":
                        label_lt = customtkinter.CTkLabel(app, text="Laufzeit (Tage):")
                        label_lt.grid(row=current_row, column=0, padx=20, pady=10)
                        if "Laufzeit_in_Tagen" not in entries:
                            entries["Laufzeit_in_Tagen"] = customtkinter.CTkEntry(app)
                        entries["Laufzeit_in_Tagen"].grid(row=current_row, column=1, padx=20, pady=10)
                        current_row += 1
                        continue
                    if field == "Zinsintervall":
                        label_zi = customtkinter.CTkLabel(app, text="Zinsintervall:")
                        label_zi.grid(row=current_row, column=0, padx=20, pady=10)
                        if "Zinsintervall" not in entries:
                            entries["Zinsintervall"] = customtkinter.StringVar(value="monatlich")
                        dropdown_zi = customtkinter.CTkOptionMenu(
                            app,
                            variable=entries["Zinsintervall"],
                            values=zinsinterval_values
                        )
                        dropdown_zi.grid(row=current_row, column=1, padx=20, pady=10)
                        current_row += 1
                        continue
                    if field == "Zinssatz":
                        label_zs = customtkinter.CTkLabel(app, text="Zinssatz (%):")
                        label_zs.grid(row=current_row, column=0, padx=20, pady=10)
                        if "Zinssatz" not in entries:
                            entries["Zinssatz"] = customtkinter.CTkEntry(app)
                        entries["Zinssatz"].grid(row=current_row, column=1, padx=20, pady=10)
                        current_row += 1
                        continue
                    if field == "Auszahlungskonto":
                        label_aus = customtkinter.CTkLabel(app, text="Auszahlungskonto:")
                        label_aus.grid(row=current_row, column=0, padx=20, pady=10)
                        check_box = customtkinter.CTkCheckBox(
                            app,
                            text="Fremdes Konto?",
                            variable=checkbox_fremdes_konto_fg,
                            command=lambda: build_form()
                        )
                        check_box.grid(row=current_row, column=1, padx=20, pady=10)
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
                            own_acc_list = load_own_accounts(selected_person)
                            dropdown_ok = customtkinter.CTkOptionMenu(
                                app,
                                variable=own_account_fg_var,
                                values=own_acc_list
                            )
                            dropdown_ok.grid(row=current_row, column=1, padx=20, pady=10)
                            current_row += 1
                        continue
                    if field == "Anlagebetrag":
                        label_ab = customtkinter.CTkLabel(app, text="Anlagebetrag:")
                        label_ab.grid(row=current_row, column=0, padx=20, pady=10)
                        if "Anlagebetrag" not in entries:
                            entries["Anlagebetrag"] = customtkinter.CTkEntry(app)
                        entries["Anlagebetrag"].grid(row=current_row, column=1, padx=20, pady=10)
                        current_row += 1
                        continue

                    # Fallback
                    label_f = customtkinter.CTkLabel(app, text=f"{field}:")
                    label_f.grid(row=current_row, column=0, padx=20, pady=10)
                    if field not in entries:
                        entries[field] = customtkinter.CTkEntry(app)
                    entries[field].grid(row=current_row, column=1, padx=20, pady=10)
                    current_row += 1

            elif acct_type == "Depot":
                # Depot-Felder
                for field in fields:
                    if field in ["Bank", "BIC", "Erstellungsdatum"]:
                        continue
                    if field == "Verrechnungskonto":
                        # Gleiche Logik wie Festgeld-Auszahlungskonto
                        label_vk = customtkinter.CTkLabel(app, text="Verrechnungskonto:")
                        label_vk.grid(row=current_row, column=0, padx=20, pady=10)
                        check_box = customtkinter.CTkCheckBox(
                            app,
                            text="Fremdes Konto?",
                            variable=checkbox_fremdes_konto_depot,
                            command=lambda: build_form()
                        )
                        check_box.grid(row=current_row, column=1, padx=20, pady=10)
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
                            own_acc_list = load_own_accounts(selected_person)
                            dropdown_ok = customtkinter.CTkOptionMenu(
                                app,
                                variable=own_account_depot_var,
                                values=own_acc_list
                            )
                            dropdown_ok.grid(row=current_row, column=1, padx=20, pady=10)
                            current_row += 1
                        continue

                    # Fallback
                    label_f = customtkinter.CTkLabel(app, text=f"{field}:")
                    label_f.grid(row=current_row, column=0, padx=20, pady=10)
                    if field not in entries:
                        entries[field] = customtkinter.CTkEntry(app)
                    entries[field].grid(row=current_row, column=1, padx=20, pady=10)
                    current_row += 1

            else:
                # Andere Kontotypen
                for field in fields:
                    if field in ["Bank", "BIC"]:
                        continue
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

        # BIC
        selected_bic = bic_var.get()
        if not selected_bic:
            bics = get_bics_for_bank(selected_bank)
            selected_bic = bics[0] if bics else ""

        # BLZ
        selected_blz = blz_var.get()

        acct_data = {
            "Bank": selected_bank,
            "BIC": selected_bic
        }
        if selected_blz:
            acct_data["BLZ"] = selected_blz

        fields = field_list.get(acct_type, [])
        for field in fields:
            if field in ["Bank", "BIC"]:
                continue

            # Festgeld-Konto
            if acct_type == "Festgeldkonto":
                if field == "Erstellungsdatum":
                    continue
                if field == "Anlagedatum":
                    anlagedatum_widget = entries["Anlagedatum"]
                    anlagedatum_str = anlagedatum_widget.get_date().strftime("%Y-%m-%d")
                    acct_data["Anlagedatum"] = anlagedatum_str
                    continue
                if field == "Laufzeit_in_Tagen":
                    val = entries["Laufzeit_in_Tagen"].get().strip()
                    if not val:
                        print("Bitte füllen Sie das Feld 'Laufzeit (Tage)' aus!")
                        return
                    acct_data["Laufzeit_in_Tagen"] = val
                    continue
                if field == "Zinsintervall":
                    val = entries["Zinsintervall"].get()
                    acct_data["Zinsintervall"] = val
                    continue
                if field == "Zinssatz":
                    val = entries["Zinssatz"].get().strip()
                    if not val:
                        print("Bitte füllen Sie das Feld 'Zinssatz' aus!")
                        return
                    acct_data["Zinssatz"] = val
                    continue
                if field == "Auszahlungskonto":
                    # Checkbox fremdes_konto_fg
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
                        # z. B. "Girokonto DE1234567890"
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
                    continue
                if field == "Anlagebetrag":
                    val = entries["Anlagebetrag"].get().strip()
                    if not val:
                        print("Bitte füllen Sie das Feld 'Anlagebetrag' aus!")
                        return
                    acct_data["Anlagebetrag"] = val
                    continue

                # Fallback
                val = entries[field].get().strip()
                if not val:
                    print(f"Bitte füllen Sie das Feld '{field}' aus!")
                    return
                acct_data[field] = val

            # Depot
            elif acct_type == "Depot":
                if field == "Erstellungsdatum":
                    continue
                if field == "Verrechnungskonto":
                    # Checkbox fremdes_konto_depot
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
                    continue

                # Fallback
                val = entries[field].get().strip()
                if not val:
                    print(f"Bitte füllen Sie das Feld '{field}' aus!")
                    return
                acct_data[field] = val

            else:
                # Andere Kontotypen
                val = entries[field].get().strip()
                if not val and field == "Erstellungsdatum":
                    val = datetime.now().strftime("%Y-%m-%d")
                elif not val:
                    print(f"Bitte füllen Sie das Feld '{field}' aus!")
                    return
                acct_data[field] = val

        acct_data["Kontotyp"] = acct_type

        # Duplikatprüfung
        if duplicate_account(selected_person, acct_type, acct_data):
            print("Dieses Konto wurde bereits angelegt.")
            return

        update_account(selected_person, acct_type, acct_data)
        print(f"Konto vom Typ {acct_type} hinzugefügt.")

        # Reset
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
            if isinstance(e, customtkinter.CTkEntry):
                e.delete(0, "end")

        navigator.navigate("person_info", selected_person=selected_person)

    # Hinzufügen-Button
    btn_add = customtkinter.CTkButton(app, text="Hinzufügen", command=add_account)
    btn_add.grid_forget()

    build_form()
    zentrieren(app)
