import customtkinter
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.data.DataManager import DataManager
from src.screens.AccountAddition import compute_iban_de  # für IBAN‑Berechnung

def create_screen(app, navigator, selected_person, **kwargs):
    clear_ui(app)
    dm = DataManager()
    person = dm.get_person_data(selected_person) or {}
    konten = person.get("Konten", [])

    # aktuell ausgewähltes Konto
    idx = kwargs.get("selected_index", 0)
    if idx < 0 or idx >= len(konten):
        idx = 0
    account = konten[idx]

    # ---------------- HEADER + KONTO DROPDOWN ----------------
    header = customtkinter.CTkLabel(
        app, text=f"Konten bearbeiten – {selected_person['Name']} {selected_person['Nachname']}"
    )
    header.grid(row=0, column=0, columnspan=4, padx=20, pady=10, sticky="w")

    choices = [
        f"{i}: {k['Kontotyp']} – {k.get('Kontonummer', k.get('Deponummer',''))}"
        for i, k in enumerate(konten)
    ]
    sel_var = customtkinter.StringVar(value=choices[idx] if choices else "")
    customtkinter.CTkComboBox(
        app,
        values=choices,
        variable=sel_var,
        state="readonly",
        command=lambda v: navigator.navigate(
            "AccountEditing",
            selected_person=selected_person,
            selected_index=int(v.split(":",1)[0])
        )
    ).grid(row=1, column=0, columnspan=4, padx=20, pady=5, sticky="we")

    # ---------------- DETAIL FRAME ----------------
    frame = customtkinter.CTkFrame(app)
    frame.grid(row=2, column=0, columnspan=4, padx=20, pady=10, sticky="nsew")
    zentrieren(frame)

    # ---------------- Kontotyp (statisch) ----------------
    customtkinter.CTkLabel(frame, text="Kontotyp:")\
        .grid(row=0, column=0, sticky="w", padx=5, pady=5)
    customtkinter.CTkLabel(frame, text=account.get("Kontotyp",""))\
        .grid(row=0, column=1, columnspan=3, sticky="w", padx=5, pady=5)

    # ---------------- Bank / BIC / BLZ ----------------
    kunden_banken = person.get("Banken", [])
    bank_var = customtkinter.StringVar(value=account.get("Bank",""))
    bic_var  = customtkinter.StringVar(value=account.get("BIC",""))
    blz_var  = customtkinter.StringVar(value=account.get("BLZ",""))

    def update_bank_fields(_=None):
        bank_data = dm.load_bank_data().get("Banken", [])
        b = next((x for x in bank_data if x["Name"] == bank_var.get()), {})
        bics = b.get("BIC", [])
        bic_menu.configure(values=bics)
        if bics and bic_var.get() not in bics:
            bic_var.set(bics[0])
        blzs = b.get("BLZ", [])
        blz_menu.configure(values=blzs)
        if blzs and blz_var.get() not in blzs:
            blz_var.set(blzs[0])

    customtkinter.CTkLabel(frame, text="Bank:")\
        .grid(row=1, column=0, sticky="w", padx=5, pady=5)
    customtkinter.CTkOptionMenu(
        frame, variable=bank_var, values=kunden_banken, command=update_bank_fields
    ).grid(row=1, column=1, sticky="we", padx=5, pady=5)

    customtkinter.CTkLabel(frame, text="BIC:")\
        .grid(row=2, column=0, sticky="w", padx=5, pady=5)
    bic_menu = customtkinter.CTkOptionMenu(frame, variable=bic_var, values=[])
    bic_menu.grid(row=2, column=1, sticky="we", padx=5, pady=5)

    customtkinter.CTkLabel(frame, text="BLZ:")\
        .grid(row=3, column=0, sticky="w", padx=5, pady=5)
    blz_menu = customtkinter.CTkOptionMenu(frame, variable=blz_var, values=[])
    blz_menu.grid(row=3, column=1, sticky="we", padx=5, pady=5)

    update_bank_fields()

    # ---------------- Restliche Felder (z.B. Kontonummer) ----------------
    detail_entries = {}
    row = 4
    for key, val in account.items():
        if key in ("Kontotyp","Bank","BIC","BLZ","Kontostaende","DepotDetails","Auszahlungskonto","Verrechnungskonto"):
            continue
        customtkinter.CTkLabel(frame, text=f"{key}:")\
            .grid(row=row, column=0, sticky="w", padx=5, pady=5)
        ent = customtkinter.CTkEntry(frame)
        ent.insert(0, str(val))
        ent.grid(row=row, column=1, columnspan=3, sticky="we", padx=5, pady=5)
        detail_entries[key] = ent
        row += 1

    # ---------------- Auszahlungskonto (Festgeldkonto) ----------------
    if account.get("Kontotyp") == "Festgeldkonto":
        out_frame = customtkinter.CTkFrame(frame)
        out_frame.grid(row=row, column=0, columnspan=4, sticky="we", pady=(10,5))
        row += 1

        fremd_fg = customtkinter.BooleanVar(value=False)
        fremd_iban = customtkinter.StringVar(value=account.get("Auszahlungskonto",""))
        own_fg   = customtkinter.StringVar(value="Bitte wählen")

        def refresh_out():
            # alle Widgets entfernen
            for w in out_frame.winfo_children():
                w.destroy()
            # Label + Checkbox
            customtkinter.CTkLabel(out_frame, text="Auszahlungskonto:")\
                .grid(row=0, column=0, padx=5, pady=5, sticky="w")
            chk = customtkinter.CTkCheckBox(
                out_frame, text="Fremdes Konto?", variable=fremd_fg, command=refresh_out
            )
            chk.grid(row=0, column=1, padx=5, pady=5, sticky="w")

            if fremd_fg.get():
                ent_fk = customtkinter.CTkEntry(out_frame, textvariable=fremd_iban)
                ent_fk.grid(row=1, column=0, columnspan=2, sticky="we", padx=5, pady=5)
                detail_entries["Auszahlungskonto_input"] = fremd_iban
            else:
                # eigene Konten (ohne Festgeld/Depot)
                own = [
                    f"{k['Kontotyp']} {k.get('Kontonummer', k.get('Deponummer',''))}"
                    for k in konten if k.get("Kontotyp") not in ("Festgeldkonto","Depot")
                ] or ["Bitte wählen"]
                own_var = customtkinter.StringVar(value=own[0])
                dd = customtkinter.CTkOptionMenu(out_frame, variable=own_var, values=own)
                dd.grid(row=1, column=0, columnspan=2, sticky="we", padx=5, pady=5)
                detail_entries["Auszahlungskonto_dropdown"] = own_var

        refresh_out()

    # ---------------- DepotDetails wie gehabt ----------------
    depot_rows = []
    if account.get("Kontotyp") == "Depot":
        customtkinter.CTkLabel(frame, text="Depot Details (ISIN / Menge / Firma):")\
            .grid(row=row, column=0, columnspan=4, sticky="w", padx=5, pady=(10,5))
        row += 1

        for det in account.get("DepotDetails", []):
            ent_i = customtkinter.CTkEntry(frame)
            ent_i.insert(0, det.get("ISIN",""))
            ent_i.grid(row=row, column=0, padx=5, pady=2, sticky="we")
            ent_m = customtkinter.CTkEntry(frame)
            ent_m.insert(0, str(det.get("Menge","")))
            ent_m.grid(row=row, column=1, padx=5, pady=2, sticky="we")
            firma = dm.get_company_name_by_isin(det.get("ISIN",""))
            customtkinter.CTkLabel(frame, text=firma)\
                .grid(row=row, column=2, columnspan=2, sticky="w", padx=5, pady=2)
            depot_rows.append((ent_i, ent_m))
            row += 1

        def add_row():
            nonlocal row
            ent_i = customtkinter.CTkEntry(frame)
            ent_i.grid(row=row, column=0, padx=5, pady=2, sticky="we")
            ent_m = customtkinter.CTkEntry(frame)
            ent_m.grid(row=row, column=1, padx=5, pady=2, sticky="we")
            lbl_f = customtkinter.CTkLabel(frame, text="")
            lbl_f.grid(row=row, column=2, columnspan=2, sticky="w", padx=5, pady=2)
            ent_i.bind(
                "<FocusOut>",
                lambda e, l=lbl_f: l.configure(text=dm.get_company_name_by_isin(ent_i.get().strip()))
            )
            depot_rows.append((ent_i, ent_m))
            row += 1
            btn_add.grid_configure(row=row)
            btn_save.grid_configure(row=row)
            btn_del.grid_configure(row=row)

        btn_add = customtkinter.CTkButton(frame, text="Zeile hinzufügen", command=add_row)
        btn_save = customtkinter.CTkButton(
            frame, text="Speichern",
            command=lambda: _save(account, detail_entries, depot_rows, dm, person, selected_person, navigator)
        )
        btn_del = customtkinter.CTkButton(
            frame, text="Löschen",
            command=lambda: _delete(konten, idx, person, selected_person, navigator, dm)
        )
        # initiale Platzierung
        btn_add.grid(row=row, column=0, padx=5, pady=10, sticky="we")
        btn_save.grid(row=row, column=1, padx=5, pady=10, sticky="we")
        btn_del.grid(row=row, column=2, padx=5, pady=10, sticky="we")

    # ---------------- BACK ----------------
    customtkinter.CTkButton(
        app, text="Zurück",
        command=lambda: navigator.navigate("PersonInfo", selected_person=selected_person)
    ).grid(row=3, column=0, columnspan=4, pady=10)

    zentrieren(app)


def _save(account, detail_entries, depot_rows, dm, person, selected_person, navigator):
    # Standard‑Felder übernehmen
    # Bank/BIC/BLZ
    account["Bank"] = detail_entries.get("Bank", {}).get()  # angepasst, falls nötig
    account["BIC"]  = detail_entries.get("BIC", {}).get()
    account["BLZ"]  = detail_entries.get("BLZ", {}).get()

    # Auszahlungs‑ bzw. Verrechnungskonto speichern
    if "Auszahlungskonto_input" in detail_entries:
        account["Auszahlungskonto"] = detail_entries["Auszahlungskonto_input"].get().strip()
    elif "Auszahlungskonto_dropdown" in detail_entries:
        sel = detail_entries["Auszahlungskonto_dropdown"].get()
        parts = sel.split()
        if len(parts)==2 and account.get("BLZ"):
            account["Auszahlungskonto"] = compute_iban_de(account["BLZ"], parts[1])
        else:
            account["Auszahlungskonto"] = sel

    # alle anderen
    for key, ent in detail_entries.items():
        if key.startswith("Auszahlungskonto") or key.startswith("Verrechnungskonto"):
            continue
        account[key] = ent.get().strip()

    # DepotDetails speichern
    if account.get("Kontotyp") == "Depot":
        dd = []
        for ent_i, ent_m in depot_rows:
            isin = ent_i.get().strip()
            menge = ent_m.get().strip()
            if isin and menge:
                try: mv = float(menge)
                except: mv = menge
                dd.append({"ISIN": isin, "Menge": mv})
        account["DepotDetails"] = dd

    dm.save_person_data(person)
    navigator.navigate("PersonInfo", selected_person=selected_person)


def _delete(konten, idx, person, selected_person, navigator, dm):
    if 0 <= idx < len(konten):
        konten.pop(idx)
        person["Konten"] = konten
        dm.save_person_data(person)
    navigator.navigate("PersonInfo", selected_person=selected_person)
