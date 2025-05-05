# src/screens/AccountEditing.py

import customtkinter as ctk
from FrontendService.src.helpers.UniversalMethoden import clear_ui, zentrieren
from FrontendService.src.models import AppState


def create_screen(app, navigator, state: AppState, selected_index: int = 0, **kwargs):
    clear_ui(app)

    person = state.selected_person
    konten = person.get("Konten", [])
    if not konten:
        return navigator.navigate("PersonInfo", selected_person=person)

    idx = max(0, min(selected_index, len(konten) - 1))
    account = konten[idx]

    # Header + Auswahl-Dropdown
    ctk.CTkLabel(
        app,
        text=f"Konten bearbeiten – {person['Name']} {person['Nachname']}",
        font=("Arial", 16, "bold")
    ).grid(row=0, column=0, columnspan=4, padx=20, pady=10, sticky="w")

    choices = [
        f"{i}: {k['Kontotyp']} – {k.get('Kontonummer', k.get('Deponummer',''))}"
        for i, k in enumerate(konten)
    ]
    sel_var = ctk.StringVar(value=choices[idx])
    ctk.CTkComboBox(
        app,
        values=choices,
        variable=sel_var,
        state="readonly",
        command=lambda v: navigator.navigate(
            "AccountEditing",
            selected_person=person,
            selected_index=int(v.split(":", 1)[0])
        )
    ).grid(row=1, column=0, columnspan=4, padx=20, pady=5, sticky="we")

    # Detail-Frame
    frame = ctk.CTkFrame(app)
    frame.grid(row=2, column=0, columnspan=4, padx=20, pady=10, sticky="nsew")
    zentrieren(frame)

    # Statischer Kontotyp
    ctk.CTkLabel(frame, text="Kontotyp:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    ctk.CTkLabel(frame, text=account.get("Kontotyp","")).grid(row=0, column=1, columnspan=3, sticky="w", padx=5, pady=5)

    # Bank / BIC / BLZ
    bank_var = ctk.StringVar(value=account.get("Bank",""))
    bic_var  = ctk.StringVar(value=account.get("BIC",""))
    blz_var  = ctk.StringVar(value=account.get("BLZ",""))

    def update_bank_fields(_=None):
        banken = state.banken
        b = next((b for b in banken if b["Name"] == bank_var.get()), {})
        bics = b.get("BIC", [])
        blzs = b.get("BLZ", [])
        bic_menu.configure(values=bics)
        if bics and bic_var.get() not in bics:
            bic_var.set(bics[0])
        blz_menu.configure(values=blzs)
        if blzs and blz_var.get() not in blzs:
            blz_var.set(blzs[0])

    ctk.CTkLabel(frame, text="Bank:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    ctk.CTkOptionMenu(frame, variable=bank_var, values=person.get("Banken", []), command=update_bank_fields)\
        .grid(row=1, column=1, sticky="we", padx=5, pady=5)
    ctk.CTkLabel(frame, text="BIC:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    bic_menu = ctk.CTkOptionMenu(frame, variable=bic_var, values=[])
    bic_menu.grid(row=2, column=1, sticky="we", padx=5, pady=5)
    ctk.CTkLabel(frame, text="BLZ:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
    blz_menu = ctk.CTkOptionMenu(frame, variable=blz_var, values=[])
    blz_menu.grid(row=3, column=1, sticky="we", padx=5, pady=5)

    update_bank_fields()

    # Dynamische Felder (z.B. Kontonummer)
    detail_entries = {}
    row = 4
    for key, val in account.items():
        if key in ("Kontotyp","Bank","BIC","BLZ","Kontostaende","DepotDetails","Auszahlungskonto","Verrechnungskonto"):
            continue
        ctk.CTkLabel(frame, text=f"{key}:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        ent = ctk.CTkEntry(frame)
        ent.insert(0, str(val))
        ent.grid(row=row, column=1, columnspan=3, sticky="we", padx=5, pady=5)
        detail_entries[key] = ent
        row += 1

    # Speicher- und Lösch-Funktion für Nicht-Depot
    def delete_account():
        konten.pop(idx)
        state.save_person(person)
        navigator.navigate("PersonInfo", selected_person=person)

    # Sonderfall Depot mit dynamischen Rows
    if account.get("Kontotyp") == "Depot":
        detail_frame = ctk.CTkFrame(frame)
        detail_frame.grid(row=row, column=0, columnspan=4, sticky="we", pady=(10,5))
        zentrieren(detail_frame)

        def add_row():
            account.setdefault("DepotDetails", []).append({"ISIN":"", "Menge":0})
            refresh_depot()

        def delete_row(ridx):
            account["DepotDetails"].pop(ridx)
            refresh_depot()

        def refresh_depot():
            # Nur die Einträge in detail_frame neu erzeugen
            for w in detail_frame.winfo_children():
                w.destroy()
            for r, det in enumerate(account.get("DepotDetails", [])):
                e_i = ctk.CTkEntry(detail_frame)
                e_i.insert(0, det.get("ISIN",""))
                e_i.grid(row=r, column=0, padx=5, pady=2, sticky="we")
                e_m = ctk.CTkEntry(detail_frame)
                e_m.insert(0, str(det.get("Menge","")))
                e_m.grid(row=r, column=1, padx=5, pady=2, sticky="we")
                btn_del = ctk.CTkButton(
                    detail_frame, text="✕", width=30,
                    command=lambda ridx=r: delete_row(ridx)
                )
                btn_del.grid(row=r, column=2, padx=5, pady=2)
            # "Position hinzufügen"-Button immer neu anlegen
            btn_add = ctk.CTkButton(detail_frame, text="Position hinzufügen", command=add_row)
            btn_add.grid(row=len(account.get("DepotDetails", [])), column=0, columnspan=3, pady=5)

        def save_depot():
            # Alle Einträge zurück in account["DepotDetails"]
            new_details = []
            # Wir lesen Reihenweise anhand der aktuellen Liste
            for r in range(len(account.get("DepotDetails", []))):
                isin = detail_frame.grid_slaves(row=r, column=0)[0].get().strip()
                qty_text = detail_frame.grid_slaves(row=r, column=1)[0].get().strip()
                try:
                    qty = float(qty_text)
                except:
                    qty = qty_text
                if isin:
                    new_details.append({"ISIN": isin, "Menge": qty})
            account["DepotDetails"] = new_details
            state.save_person(person)
            navigator.navigate("PersonInfo", selected_person=person)

        # Initial render und Buttons
        refresh_depot()
        ctk.CTkButton(frame, text="Speichern", command=save_depot).grid(row=row+1, column=0, padx=5, pady=10)
        ctk.CTkButton(frame, text="Löschen", command=delete_account).grid(row=row+1, column=1, padx=5, pady=10)

    else:
        # Nicht-Depot: Standard-Save/Delete
        def save_generic():
            account["Bank"] = bank_var.get()
            account["BIC"] = bic_var.get()
            account["BLZ"] = blz_var.get()
            for k, ent in detail_entries.items():
                account[k] = ent.get().strip()
            state.save_person(person)
            navigator.navigate("PersonInfo", selected_person=person)

        ctk.CTkButton(frame, text="Speichern", command=save_generic).grid(row=row, column=0, padx=5, pady=10)
        ctk.CTkButton(frame, text="Löschen", command=delete_account).grid(row=row, column=1, padx=5, pady=10)

    # Rückkehr-Button
    ctk.CTkButton(
        app,
        text="Zurück",
        command=lambda: navigator.navigate("PersonInfo", selected_person=person)
    ).grid(row=row+2, column=0, columnspan=4, pady=10)

    zentrieren(app)
