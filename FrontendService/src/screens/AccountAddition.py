import logging

import customtkinter as ctk

from src.models.AppState import AppState
from src.ui.components import create_page, section_card, action_bar, primary_button, set_status

logger = logging.getLogger(__name__)


def compute_iban_de(blz, kontonummer):
    return f"DE00{blz}{kontonummer}"


def create_screen(app, navigator, state: AppState, **kwargs):
    person = state.selected_person
    if not person:
        navigator.navigate("PersonSelection")
        return

    dm = state.data_manager
    ac = state.account_controller

    ui = create_page(
        app,
        title="Konto hinzufügen",
        subtitle=f"Person: {person['Name']} {person['Nachname']}",
        back_command=lambda: navigator.navigate("PersonInfo", selected_person=state.selected_person),
        scrollable=True,
    )
    status = ui["status"]
    _, body = section_card(ui["content"], "Kontoformular", "Kontotyp, Bankdaten und kontospezifische Felder")

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

    dynamic = ctk.CTkFrame(body, fg_color="transparent")
    dynamic.grid(row=0, column=0, sticky="ew")
    dynamic.grid_columnconfigure(1, weight=1)

    def add_row(row, label, widget):
        ctk.CTkLabel(dynamic, text=label).grid(row=row, column=0, sticky="w", pady=4)
        widget.grid(row=row, column=1, sticky="ew", pady=4)

    def build_form():
        for w in dynamic.winfo_children():
            w.destroy()
        entries.clear()
        row = 0

        types = [list(item.keys())[0] for item in state.kontotypen]
        add_row(row, "Kontotyp *", ctk.CTkOptionMenu(dynamic, variable=acct_var, values=types, command=lambda _: build_form()))
        row += 1

        banken = person.get("Banken", []) or ["Bitte wählen"]
        add_row(row, "Bank *", ctk.CTkOptionMenu(dynamic, variable=bank_var, values=banken, command=lambda _: build_form()))
        row += 1

        if bank_var.get() not in ["Bitte wählen", ""]:
            banks = dm.load_bank_data().get("Banken", [])
            bdata = next((b for b in banks if b.get("Name") == bank_var.get()), {})
            bics = bdata.get("BIC", []) or [""]
            blzs = bdata.get("BLZ", []) or [""]
            if not bic_var.get() and bics:
                bic_var.set(bics[0])
            if not blz_var.get() and blzs:
                blz_var.set(blzs[0])
            add_row(row, "BIC", ctk.CTkOptionMenu(dynamic, variable=bic_var, values=bics))
            row += 1
            add_row(row, "BLZ", ctk.CTkOptionMenu(dynamic, variable=blz_var, values=blzs))
            row += 1

        acct_type = acct_var.get()
        fields = []
        for item in state.kontotypen:
            if acct_type in item:
                fields = item.get(acct_type, [])
                break

        for f in fields:
            if f in ["Bank", "BIC", "Erstellungsdatum"]:
                continue
            if acct_type == "Festgeldkonto" and f == "Auszahlungskonto":
                chk = ctk.CTkCheckBox(dynamic, text="Fremdes Konto", variable=checkbox_fg, command=build_form)
                add_row(row, "Auszahlungskonto", chk)
                row += 1
                if checkbox_fg.get():
                    add_row(row, "IBAN", ctk.CTkEntry(dynamic, textvariable=fremde_iban_fg, placeholder_text="Fremde IBAN"))
                else:
                    own = [
                        f"{k['Kontotyp']} {k.get('Kontonummer', k.get('Deponummer',''))}"
                        for k in person.get("Konten", [])
                        if k.get("Kontotyp") not in ("Festgeldkonto", "Depot")
                    ] or ["Bitte wählen"]
                    add_row(row, "Konto", ctk.CTkOptionMenu(dynamic, variable=own_acc_fg, values=own))
                row += 1
                continue
            if acct_type == "Depot" and f == "Verrechnungskonto":
                chk = ctk.CTkCheckBox(dynamic, text="Fremdes Konto", variable=checkbox_dp, command=build_form)
                add_row(row, "Verrechnungskonto", chk)
                row += 1
                if checkbox_dp.get():
                    add_row(row, "IBAN", ctk.CTkEntry(dynamic, textvariable=fremde_iban_dp, placeholder_text="Fremde IBAN"))
                else:
                    own = [
                        f"{k['Kontotyp']} {k.get('Kontonummer', k.get('Deponummer',''))}"
                        for k in person.get("Konten", [])
                        if k.get("Kontotyp") not in ("Festgeldkonto", "Depot")
                    ] or ["Bitte wählen"]
                    add_row(row, "Konto", ctk.CTkOptionMenu(dynamic, variable=own_acc_dp, values=own))
                row += 1
                continue

            entry = ctk.CTkEntry(dynamic)
            entries[f] = entry
            add_row(row, f, entry)
            row += 1

    def add_account():
        acct_type = acct_var.get()
        if acct_type in ("", "Bitte wählen"):
            set_status(status, "Bitte einen Kontotyp auswählen.", "warning")
            return
        if bank_var.get() in ("", "Bitte wählen"):
            set_status(status, "Bitte eine Bank auswählen.", "warning")
            return

        account_data = {"Bank": bank_var.get(), "BIC": bic_var.get()}
        if blz_var.get():
            account_data["BLZ"] = blz_var.get()

        for f, entry in entries.items():
            account_data[f] = entry.get().strip()

        if acct_type == "Festgeldkonto":
            if checkbox_fg.get():
                account_data["Auszahlungskonto"] = fremde_iban_fg.get().strip()
            else:
                parts = own_acc_fg.get().split()
                if len(parts) == 2 and blz_var.get():
                    account_data["Auszahlungskonto"] = compute_iban_de(blz_var.get(), parts[1])

        if acct_type == "Depot":
            if checkbox_dp.get():
                account_data["Verrechnungskonto"] = fremde_iban_dp.get().strip()
            else:
                parts = own_acc_dp.get().split()
                if len(parts) == 2 and blz_var.get():
                    account_data["Verrechnungskonto"] = compute_iban_de(blz_var.get(), parts[1])

        logger.debug("add_account: %s, data=%s", acct_type, account_data)
        if ac.add_account(person, acct_type, account_data):
            state.load_all()
            state.select_person(person["Name"], person["Nachname"])
            set_status(status, "Konto erfolgreich hinzugefügt.", "success")
            navigator.navigate("PersonInfo", selected_person=state.selected_person)
        else:
            set_status(status, "Konto konnte nicht hinzugefügt werden (z. B. Duplikat).", "error")

    build_form()
    bar = action_bar(body)
    primary_button(bar, "Konto anlegen", add_account, column=0)
