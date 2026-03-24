import tkinter.messagebox as messagebox
from calendar import monthrange
from datetime import date

import customtkinter as ctk

from src.helpers.account_overview import (
    build_account_label,
    get_latest_balance_entry_for_account,
    latest_snapshot_date,
    validate_overview_inputs,
)
from src.models.AppState import AppState
from src.ui.components import action_bar, create_page, empty_state, primary_button, secondary_button, section_card, set_status
from src.ui.date_widgets import create_date_entry


def create_screen(app, navigator, state: AppState, **kwargs):
    if not state.selected_person:
        navigator.navigate("PersonSelection")
        return

    person = state.selected_person
    ac = state.account_controller
    konten = person.get("Konten", [])

    auto_accounts = [k for k in konten if k.get("Kontotyp") == "Festgeldkonto"]
    depot_accounts = [k for k in konten if k.get("Kontotyp") == "Depot"]
    balance_accounts = [k for k in konten if k.get("Kontotyp") not in ("Festgeldkonto", "Depot")]

    ui = create_page(
        app,
        "Kontoübersicht erfassen",
        "Alle manuellen Konten auf einem Screen erfassen und anschließend berechnen.",
        back_command=lambda: navigator.navigate("PersonInfo"),
        scrollable=True,
    )
    status = ui["status"]

    if not konten:
        empty_state(ui["content"], "Keine Konten für diese Person vorhanden.")
        return

    balance_fields = []
    depot_fields = []
    dirty_state = {"is_dirty": False}

    def mark_dirty(*_args):
        dirty_state["is_dirty"] = True

    def clear_field_errors():
        for field in balance_fields:
            field["error"].configure(text="")
        for depot in depot_fields:
            depot["error"].configure(text="")
            for row in depot["rows"]:
                row["error"].configure(text="")

    _, date_body = section_card(ui["content"], "Stichtag", "Datum auswählen und Quick-Actions nutzen.")
    date_body.grid_columnconfigure((0, 1, 2, 3), weight=1)

    selected_date = state.selected_date or date.today()
    date_entry = create_date_entry(date_body)
    date_entry.set_date(selected_date)
    date_entry.grid(row=0, column=0, sticky="w", pady=4)

    def apply_selected_date(new_date):
        current = state.selected_date
        if current and new_date != current and dirty_state["is_dirty"]:
            proceed = messagebox.askyesno(
                "Stichtag ändern",
                "Es gibt bereits Eingaben. Beim Stichtag-Wechsel sollten Werte geprüft werden. Fortfahren?",
            )
            if not proceed:
                date_entry.set_date(current)
                return

        state.selected_date = new_date
        set_status(status, f"Stichtag gesetzt: {new_date}", "info")

    ctk.CTkButton(date_body, text="Stichtag übernehmen", command=lambda: apply_selected_date(date_entry.get_date())).grid(
        row=0, column=1, padx=8, sticky="w"
    )

    def set_today():
        date_entry.set_date(date.today())
        apply_selected_date(date_entry.get_date())

    def set_month_end():
        today = date.today()
        last_day = monthrange(today.year, today.month)[1]
        date_entry.set_date(date(today.year, today.month, last_day))
        apply_selected_date(date_entry.get_date())

    def set_last_snapshot():
        latest = latest_snapshot_date(konten)
        if not latest:
            set_status(status, "Kein historischer Stichtag gefunden.", "warning")
            return
        date_entry.set_date(latest)
        apply_selected_date(date_entry.get_date())

    ctk.CTkButton(date_body, text="Heute", command=set_today).grid(row=0, column=2, padx=4, sticky="ew")
    ctk.CTkButton(date_body, text="Monatsultimo", command=set_month_end).grid(row=0, column=3, padx=4, sticky="ew")
    ctk.CTkButton(date_body, text="Letzter Stichtag", command=set_last_snapshot).grid(row=1, column=0, columnspan=2, pady=(8, 0), sticky="w")

    if auto_accounts:
        _, auto_body = section_card(
            ui["content"],
            "Festgeldkonten (read-only)",
            "Diese Konten werden automatisch durch die Berechnung aktualisiert.",
        )
        for idx, account in enumerate(auto_accounts):
            latest_date, latest_balance = get_latest_balance_entry_for_account(account)
            label = build_account_label(account)
            ctk.CTkLabel(
                auto_body,
                text=f"{idx + 1}. {label} · letzter Wert: {latest_balance:.2f} ({latest_date or 'kein Eintrag'})",
                text_color="gray70",
                anchor="w",
            ).pack(fill="x", pady=2)

    if balance_accounts:
        _, bulk_body = section_card(
            ui["content"],
            "Saldo-Erfassung (manuelle Konten)",
            "Für jedes Konto den neuen Saldo eintragen. Letzte Werte sind vorbefüllt.",
        )
        bulk_body.grid_columnconfigure(0, weight=1)

        for account in balance_accounts:
            row_card = ctk.CTkFrame(bulk_body, corner_radius=10)
            row_card.pack(fill="x", pady=6)
            row_card.grid_columnconfigure(0, weight=1)

            latest_date, latest_balance = get_latest_balance_entry_for_account(account)
            label = build_account_label(account)

            ctk.CTkLabel(row_card, text=label, font=("Arial", 14, "bold"), anchor="w").grid(
                row=0, column=0, sticky="w", padx=12, pady=(10, 2)
            )
            ctk.CTkLabel(
                row_card,
                text=f"Letzter bekannter Stand: {latest_balance:.2f} ({latest_date or 'kein Eintrag'})",
                text_color="gray70",
                anchor="w",
            ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 6))

            entry = ctk.CTkEntry(row_card, placeholder_text="Neuer Saldo")
            entry.insert(0, f"{latest_balance:.2f}")
            entry.grid(row=2, column=0, sticky="ew", padx=12)
            entry.bind("<KeyRelease>", mark_dirty)

            error_label = ctk.CTkLabel(row_card, text="", text_color="#F28B82", anchor="w")
            error_label.grid(row=3, column=0, sticky="w", padx=12, pady=(2, 10))

            balance_fields.append({"account": account, "entry": entry, "error": error_label, "account_key": id(account)})

    if depot_accounts:
        _, depot_body = section_card(
            ui["content"],
            "Depot-Erfassung",
            "Positionen je Depot bearbeiten. Zeilen können hinzugefügt oder gelöscht werden.",
        )

        def add_depot_row(depot_model, isin_value="", qty_value=""):
            row_idx = len(depot_model["rows"])
            row_frame = ctk.CTkFrame(depot_model["frame"], fg_color="transparent")
            row_frame.pack(fill="x", pady=4)
            row_frame.grid_columnconfigure((0, 1), weight=1)

            isin_entry = ctk.CTkEntry(row_frame, placeholder_text="ISIN")
            isin_entry.insert(0, isin_value)
            isin_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
            isin_entry.bind("<KeyRelease>", mark_dirty)

            qty_entry = ctk.CTkEntry(row_frame, placeholder_text="Menge")
            qty_entry.insert(0, qty_value)
            qty_entry.grid(row=0, column=1, padx=(0, 8), sticky="ew")
            qty_entry.bind("<KeyRelease>", mark_dirty)

            row_error = ctk.CTkLabel(row_frame, text="", text_color="#F28B82", anchor="w")
            row_error.grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

            def remove_row():
                row_frame.destroy()
                depot_model["rows"].remove(model)
                mark_dirty()

            ctk.CTkButton(row_frame, text="Entfernen", width=90, fg_color="#A61B1B", hover_color="#7A1010", command=remove_row).grid(
                row=0, column=2, sticky="e"
            )

            model = {"isin": isin_entry, "qty": qty_entry, "error": row_error, "index": row_idx}
            depot_model["rows"].append(model)

        for account in depot_accounts:
            card = ctk.CTkFrame(depot_body, corner_radius=10)
            card.pack(fill="x", pady=8)
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(card, text=build_account_label(account), font=("Arial", 14, "bold"), anchor="w").grid(
                row=0, column=0, padx=12, pady=(10, 2), sticky="w"
            )

            rows_frame = ctk.CTkFrame(card, fg_color="transparent")
            rows_frame.grid(row=1, column=0, sticky="ew", padx=12)

            depot_error = ctk.CTkLabel(card, text="", text_color="#F28B82", anchor="w")
            depot_error.grid(row=3, column=0, sticky="w", padx=12, pady=(2, 8))

            depot_model = {"account": account, "frame": rows_frame, "rows": [], "error": depot_error, "account_key": id(account)}
            depot_fields.append(depot_model)

            details = account.get("DepotDetails", []) or []
            if details:
                for detail in details:
                    add_depot_row(depot_model, str(detail.get("ISIN", "")), str(detail.get("Menge", "")))
            else:
                add_depot_row(depot_model)

            ctk.CTkButton(
                card,
                text="Position hinzufügen",
                command=lambda m=depot_model: add_depot_row(m),
            ).grid(row=2, column=0, sticky="w", padx=12, pady=(6, 0))

    def save_all():
        clear_field_errors()

        selected = date_entry.get_date()
        apply_selected_date(selected)
        if state.selected_date != selected:
            return

        balance_inputs = [
            {
                "account_key": field["account_key"],
                "konto": field["account"],
                "value": field["entry"].get().strip(),
            }
            for field in balance_fields
        ]
        depot_inputs = []
        for depot in depot_fields:
            rows = []
            for row in depot["rows"]:
                rows.append({"isin": row["isin"].get().strip(), "menge": row["qty"].get().strip()})
            depot_inputs.append({"account_key": depot["account_key"], "konto": depot["account"], "rows": rows})

        validation = validate_overview_inputs(balance_inputs, depot_inputs)

        for field in balance_fields:
            msg = validation["balance_errors"].get(field["account_key"], "")
            field["error"].configure(text=msg)

        for depot in depot_fields:
            row_errors = validation["depot_errors"].get(depot["account_key"], {})
            if row_errors:
                depot["error"].configure(text="Bitte markierte Depotzeilen korrigieren.")
            for idx, row in enumerate(depot["rows"]):
                row_error = row_errors.get(idx, {})
                messages = []
                if "isin" in row_error:
                    messages.append(row_error["isin"])
                if "menge" in row_error:
                    messages.append(row_error["menge"])
                row["error"].configure(text=" ".join(messages))

        if not validation["is_valid"]:
            set_status(status, " ".join(validation["messages"]), "error")
            return

        entries = validation["entries"]
        state.overview_inputs = entries
        ac.update_account_overview(person, state.selected_date, entries)
        ac.calculate_festgeld(person, state.selected_date)
        ac.calculate_depot(person, state.selected_date)
        state.load_all()
        dirty_state["is_dirty"] = False
        set_status(status, "Kontoübersicht erfolgreich gespeichert und berechnet.", "success")
        navigator.navigate("PersonInfo")

    button_bar = action_bar(ui["content"])
    secondary_button(button_bar, "Zurück", lambda: navigator.navigate("PersonInfo"), column=0)
    primary_button(button_bar, "Speichern und berechnen", save_all, column=1)

    if state.selected_date:
        set_status(status, f"Aktueller Stichtag: {state.selected_date}", "info")
    else:
        set_status(status, "Bitte Stichtag auswählen und danach speichern.", "info")
