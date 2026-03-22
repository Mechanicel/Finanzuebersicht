# src/screens/AccountAddition.py

import logging
import customtkinter as ctk
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.models.AppState import AppState

logger = logging.getLogger(__name__)

def compute_iban_de(blz, kontonummer):
    """Erzeugt eine vereinfachte IBAN ohne Prüfziffer."""
    logger.debug(f"compute_iban_de: BLZ={blz}, Kontonummer={kontonummer}")
    return f"DE00{blz}{kontonummer}"

def create_screen(app, navigator, state: AppState, **kwargs):
    """Screen zum Hinzufügen eines neuen Kontos für die aktuell ausgewählte Person."""
    clear_ui(app)
    person = state.selected_person
    if not person:
        navigator.navigate("PersonSelection")
        return
    dm = state.data_manager
    ac = state.account_controller

    # Variablen für Eingaben
    acct_var = ctk.StringVar(value="Bitte wählen")
    bank_var = ctk.StringVar(value="Bitte wählen")
    bic_var = ctk.StringVar()
    blz_var = ctk.StringVar()
    entries = {}
    checkbox_fg = ctk.BooleanVar(value=False)
    fremde_iban_fg = ctk.StringVar()
    own_acc_fg = ctk.StringVar(value="Bitte wählen")
    checkbox_dp = ctk.BooleanVar(value=False)
    fremde_iban_dp = ctk.StringVar()
    own_acc_dp = ctk.StringVar(value="Bitte wählen")

    # Back-Button
    ctk.CTkButton(
        app,
        text="← Zurück",
        command=lambda: navigator.navigate("PersonInfo", selected_person=state.selected_person)
    ).grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky="w")

    def build_form():
        # Entferne alle Widgets ab Zeile 2
        for w in app.grid_slaves():
            if int(w.grid_info().get("row", 0)) >= 2:
                w.grid_forget()
        row = 2

        # Kontotyp-Auswahl
        ctk.CTkLabel(app, text="Kontotyp:").grid(row=row, column=0, padx=20, pady=5, sticky="e")
        types = [list(item.keys())[0] for item in state.kontotypen]
        ctk.CTkOptionMenu(
            app, variable=acct_var, values=types, command=lambda _: build_form()
        ).grid(row=row, column=1, padx=20, pady=5, sticky="w")
        row += 1

        # Bank-Auswahl
        ctk.CTkLabel(app, text="Bank:").grid(row=row, column=0, padx=20, pady=5, sticky="e")
        ctk.CTkOptionMenu(
            app,
            variable=bank_var,
            values=person.get("Banken", []),
            command=lambda _: build_form()
        ).grid(row=row, column=1, padx=20, pady=5, sticky="w")
        row += 1

        # BIC und BLZ, abhängig von Bank
        if bank_var.get() not in ["Bitte wählen", ""]:
            banks = dm.load_bank_data().get("Banken", [])
            bdata = next((b for b in banks if b.get("Name") == bank_var.get()), {})
            bics = bdata.get("BIC", [])
            blzs = bdata.get("BLZ", [])
            ctk.CTkLabel(app, text="BIC:").grid(row=row, column=0, padx=20, pady=5, sticky="e")
            ctk.CTkOptionMenu(app, variable=bic_var, values=bics).grid(row=row, column=1, sticky="w")
            row += 1
            ctk.CTkLabel(app, text="BLZ:").grid(row=row, column=0, padx=20, pady=5, sticky="e")
            ctk.CTkOptionMenu(app, variable=blz_var, values=blzs).grid(row=row, column=1, sticky="w")
            row += 1

        # Zusätzliche Felder basierend auf Kontotyp
        acct_type = acct_var.get()
        fields = []
        for item in state.kontotypen:
            if acct_type in item:
                fields = item.get(acct_type, [])
                break

        if acct_type and acct_type != "Bitte wählen":
            for f in fields:
                if f in ["Bank", "BIC", "Erstellungsdatum"]:
                    continue
                # Festgeldkonto: Auszahlungskonto
                if acct_type == "Festgeldkonto" and f == "Auszahlungskonto":
                    ctk.CTkLabel(app, text="Auszahlungskonto:").grid(
                        row=row, column=0, padx=20, pady=5, sticky="e"
                    )
                    ctk.CTkCheckBox(
                        app,
                        text="Fremdes Konto?",
                        variable=checkbox_fg,
                        command=lambda: build_form()
                    ).grid(row=row, column=1, sticky="w")
                    row += 1
                    if checkbox_fg.get():
                        ctk.CTkEntry(app, textvariable=fremde_iban_fg).grid(
                            row=row, column=1, padx=20, pady=5, sticky="w"
                        )
                    else:
                        own = [
                            f"{k['Kontotyp']} {k.get('Kontonummer', k.get('Deponummer',''))}"
                            for k in person.get('Konten', [])
                            if k.get('Kontotyp') not in ('Festgeldkonto','Depot')
                        ] or ["Bitte wählen"]
                        ctk.CTkOptionMenu(
                            app, variable=own_acc_fg, values=own
                        ).grid(row=row, column=1, padx=20, pady=5, sticky="w")
                    row += 1
                    continue
                # Depotkonto: Verrechnungskonto
                if acct_type == "Depot" and f == "Verrechnungskonto":
                    ctk.CTkLabel(app, text="Verrechnungskonto:").grid(
                        row=row, column=0, padx=20, pady=5, sticky="e"
                    )
                    ctk.CTkCheckBox(
                        app,
                        text="Fremdes Konto?",
                        variable=checkbox_dp,
                        command=lambda: build_form()
                    ).grid(row=row, column=1, sticky="w")
                    row += 1
                    if checkbox_dp.get():
                        ctk.CTkEntry(app, textvariable=fremde_iban_dp).grid(
                            row=row, column=1, padx=20, pady=5, sticky="w"
                        )
                    else:
                        own = [
                            f"{k['Kontotyp']} {k.get('Kontonummer', k.get('Deponummer',''))}"
                            for k in person.get('Konten', [])
                            if k.get('Kontotyp') not in ('Festgeldkonto','Depot')
                        ] or ["Bitte wählen"]
                        ctk.CTkOptionMenu(
                            app, variable=own_acc_dp, values=own
                        ).grid(row=row, column=1, padx=20, pady=5, sticky="w")
                    row += 1
                    continue
                # Standardfelder
                ctk.CTkLabel(app, text=f"{f}:").grid(
                    row=row, column=0, padx=20, pady=5, sticky="e"
                )
                entry = ctk.CTkEntry(app)
                entry.grid(row=row, column=1, padx=20, pady=5, sticky="w")
                entries[f] = entry
                row += 1

        # Hinzufügen-Button
        ctk.CTkButton(app, text="Hinzufügen", command=add_account).grid(
            row=row, column=0, columnspan=2, pady=(10,20)
        )
        app.grid_columnconfigure(0, weight=1)
        app.grid_columnconfigure(1, weight=1)

    def add_account():
        acct_type = acct_var.get()
        account_data = {"Bank": bank_var.get(), "BIC": bic_var.get()}
        if blz_var.get():
            account_data["BLZ"] = blz_var.get()
        for f, entry in entries.items():
            account_data[f] = entry.get().strip()
        # Festgeldkonto
        if acct_type == "Festgeldkonto":
            if checkbox_fg.get():
                account_data["Auszahlungskonto"] = fremde_iban_fg.get().strip()
            else:
                parts = own_acc_fg.get().split()
                if len(parts) == 2 and blz_var.get():
                    account_data["Auszahlungskonto"] = compute_iban_de(
                        blz_var.get(), parts[1]
                    )
        # Depotkonto
        if acct_type == "Depot":
            if checkbox_dp.get():
                account_data["Verrechnungskonto"] = fremde_iban_dp.get().strip()
            else:
                parts = own_acc_dp.get().split()
                if len(parts) == 2 and blz_var.get():
                    account_data["Verrechnungskonto"] = compute_iban_de(
                        blz_var.get(), parts[1]
                    )

        logger.debug(f"add_account: {acct_type}, data={account_data}")
        if ac.add_account(person, acct_type, account_data):
            # State neu laden und selected_person erneut setzen:
            state.load_all()
            state.select_person(person["Name"], person["Nachname"])
            logger.info("Konto erfolgreich hinzugefügt")
            navigator.navigate("PersonInfo", selected_person=state.selected_person)
        else:
            logger.error("Konto konnte nicht hinzugefügt werden (Duplikat?)")

    build_form()
    zentrieren(app)
