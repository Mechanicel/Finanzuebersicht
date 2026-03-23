import customtkinter as ctk

from src.models.AppState import AppState
from src.ui.components import create_page, section_card, action_bar, primary_button, secondary_button, danger_button, set_status, empty_state


def create_screen(app, navigator, state: AppState, selected_index: int = 0, **kwargs):
    person = state.selected_person
    konten = person.get("Konten", [])
    if not konten:
        ui = create_page(app, "Konten bearbeiten", "Keine Konten verfügbar.", back_command=lambda: navigator.navigate("PersonInfo"))
        empty_state(ui["content"], "Es sind keine Konten vorhanden.")
        return

    idx = max(0, min(selected_index, len(konten) - 1))
    account = konten[idx]

    ui = create_page(
        app,
        title="Konten bearbeiten",
        subtitle=f"{person['Name']} {person['Nachname']}",
        back_command=lambda: navigator.navigate("PersonInfo", selected_person=person),
        scrollable=True,
    )
    status = ui["status"]

    _, select_body = section_card(ui["content"], "Kontoauswahl")
    choices = [f"{i}: {k['Kontotyp']} – {k.get('Kontonummer', k.get('Deponummer', ''))}" for i, k in enumerate(konten)]
    sel_var = ctk.StringVar(value=choices[idx])
    ctk.CTkComboBox(
        select_body,
        values=choices,
        variable=sel_var,
        state="readonly",
        command=lambda v: navigator.navigate("AccountEditing", selected_person=person, selected_index=int(v.split(":", 1)[0])),
    ).pack(fill="x")

    _, form_body = section_card(ui["content"], "Bearbeitung")
    form_body.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(form_body, text="Kontotyp").grid(row=0, column=0, sticky="w", pady=4)
    ctk.CTkLabel(form_body, text=account.get("Kontotyp", "")).grid(row=0, column=1, sticky="w", pady=4)

    bank_var = ctk.StringVar(value=account.get("Bank", ""))
    bic_var = ctk.StringVar(value=account.get("BIC", ""))
    blz_var = ctk.StringVar(value=account.get("BLZ", ""))

    def update_bank_fields(_=None):
        b = next((x for x in state.banken if x["Name"] == bank_var.get()), {})
        bics = b.get("BIC", []) or [""]
        blzs = b.get("BLZ", []) or [""]
        bic_menu.configure(values=bics)
        blz_menu.configure(values=blzs)
        if bic_var.get() not in bics:
            bic_var.set(bics[0])
        if blz_var.get() not in blzs:
            blz_var.set(blzs[0])

    ctk.CTkLabel(form_body, text="Bank").grid(row=1, column=0, sticky="w", pady=4)
    ctk.CTkOptionMenu(form_body, variable=bank_var, values=person.get("Banken", []), command=update_bank_fields).grid(row=1, column=1, sticky="ew")
    ctk.CTkLabel(form_body, text="BIC").grid(row=2, column=0, sticky="w", pady=4)
    bic_menu = ctk.CTkOptionMenu(form_body, variable=bic_var, values=[])
    bic_menu.grid(row=2, column=1, sticky="ew")
    ctk.CTkLabel(form_body, text="BLZ").grid(row=3, column=0, sticky="w", pady=4)
    blz_menu = ctk.CTkOptionMenu(form_body, variable=blz_var, values=[])
    blz_menu.grid(row=3, column=1, sticky="ew")
    update_bank_fields()

    detail_entries = {}
    row = 4
    for key, val in account.items():
        if key in ("Kontotyp", "Bank", "BIC", "BLZ", "Kontostaende", "DepotDetails", "Auszahlungskonto", "Verrechnungskonto"):
            continue
        ctk.CTkLabel(form_body, text=key).grid(row=row, column=0, sticky="w", pady=4)
        ent = ctk.CTkEntry(form_body)
        ent.insert(0, str(val))
        ent.grid(row=row, column=1, sticky="ew")
        detail_entries[key] = ent
        row += 1

    detail_frame = ctk.CTkFrame(form_body, fg_color="transparent")
    detail_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    def delete_account():
        konten.pop(idx)
        state.save_person(person)
        set_status(status, "Konto gelöscht.", "success")
        navigator.navigate("PersonInfo", selected_person=person)

    if account.get("Kontotyp") == "Depot":
        def add_row():
            account.setdefault("DepotDetails", []).append({"ISIN": "", "Menge": 0})
            refresh_depot()

        def delete_row(ridx):
            account["DepotDetails"].pop(ridx)
            refresh_depot()

        def refresh_depot():
            for w in detail_frame.winfo_children():
                w.destroy()
            for r, det in enumerate(account.get("DepotDetails", [])):
                e_i = ctk.CTkEntry(detail_frame)
                e_i.insert(0, det.get("ISIN", ""))
                e_i.grid(row=r, column=0, padx=4, pady=2, sticky="ew")
                e_m = ctk.CTkEntry(detail_frame)
                e_m.insert(0, str(det.get("Menge", "")))
                e_m.grid(row=r, column=1, padx=4, pady=2, sticky="ew")
                ctk.CTkButton(detail_frame, text="✕", width=34, fg_color="#A61B1B", command=lambda ridx=r: delete_row(ridx)).grid(row=r, column=2, padx=4)
            ctk.CTkButton(detail_frame, text="Position hinzufügen", command=add_row).grid(row=len(account.get("DepotDetails", [])), column=0, columnspan=3, pady=6)

        def save_depot():
            new_details = []
            for r in range(len(account.get("DepotDetails", []))):
                isin = detail_frame.grid_slaves(row=r, column=0)[0].get().strip()
                qty_text = detail_frame.grid_slaves(row=r, column=1)[0].get().strip()
                try:
                    qty = float(qty_text)
                except Exception:
                    qty = qty_text
                if isin:
                    new_details.append({"ISIN": isin, "Menge": qty})
            account["DepotDetails"] = new_details
            account["Bank"] = bank_var.get()
            account["BIC"] = bic_var.get()
            account["BLZ"] = blz_var.get()
            state.save_person(person)
            set_status(status, "Depotkonto gespeichert.", "success")
            navigator.navigate("PersonInfo", selected_person=person)

        refresh_depot()
        bar = action_bar(form_body)
        primary_button(bar, "Speichern", save_depot, column=0)
        danger_button(bar, "Löschen", delete_account, column=2)
    else:
        def save_generic():
            account["Bank"] = bank_var.get()
            account["BIC"] = bic_var.get()
            account["BLZ"] = blz_var.get()
            for k, ent in detail_entries.items():
                account[k] = ent.get().strip()
            state.save_person(person)
            set_status(status, "Konto gespeichert.", "success")
            navigator.navigate("PersonInfo", selected_person=person)

        bar = action_bar(form_body)
        primary_button(bar, "Speichern", save_generic, column=0)
        danger_button(bar, "Löschen", delete_account, column=2)
