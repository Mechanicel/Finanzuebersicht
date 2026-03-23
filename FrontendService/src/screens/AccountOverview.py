import customtkinter as ctk
from tkcalendar import DateEntry

from src.models.AppState import AppState
from src.ui.components import create_page, section_card, set_status, empty_state


def create_screen(app, navigator, state: AppState, **kwargs):
    person = state.selected_person
    ac = state.account_controller
    konten = [k for k in person.get("Konten", []) if k.get("Kontotyp") != "Festgeldkonto"]

    ui = create_page(app, "Kontoübersicht erfassen", "Stichtag setzen und Konten Schritt für Schritt eingeben.", back_command=lambda: navigator.navigate("PersonInfo"))
    status = ui["status"]

    if not konten:
        empty_state(ui["content"], "Keine auswertbaren Konten vorhanden.")
        return

    _, date_body = section_card(ui["content"], "1) Stichtag")
    date_entry = DateEntry(date_body, date_pattern="yyyy-mm-dd", width=20)
    date_entry.grid(row=0, column=0, sticky="w", pady=4)
    ctk.CTkButton(date_body, text="Stichtag übernehmen", command=lambda: on_date_selected()).grid(row=0, column=1, padx=8)

    _, content_body = section_card(ui["content"], "2) Kontodaten")
    _, nav_body = section_card(ui["content"], "3) Navigation")

    current_index = 0
    detail_widgets = []

    def on_date_selected():
        state.selected_date = date_entry.get_date()
        state.overview_inputs = [None] * len(konten)
        set_status(status, f"Stichtag gesetzt: {state.selected_date}", "info")
        show_account(0)

    def show_account(idx):
        nonlocal current_index, detail_widgets
        current_index = idx
        for w in content_body.winfo_children():
            w.destroy()
        detail_widgets = []

        konto = konten[idx]
        ctk.CTkLabel(content_body, text=f"Konto {idx + 1} von {len(konten)}", font=("Arial", 16, "bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(content_body, text=f"Typ: {konto.get('Kontotyp')}").grid(row=1, column=0, sticky="w", pady=(4, 0))
        num = konto.get("Kontonummer", konto.get("Deponummer", "–"))
        ctk.CTkLabel(content_body, text=f"Nummer: {num}").grid(row=2, column=0, sticky="w")

        if konto.get("Kontotyp") == "Depot":
            ctk.CTkLabel(content_body, text="Depotpositionen (ISIN / Menge)", font=("Arial", 13, "bold")).grid(row=3, column=0, sticky="w", pady=(8, 4))
            for r, det in enumerate(konto.get("DepotDetails", []), start=4):
                e_isin = ctk.CTkEntry(content_body, placeholder_text="ISIN")
                e_isin.insert(0, det.get("ISIN", ""))
                e_isin.grid(row=r, column=0, sticky="ew", pady=2)
                e_qty = ctk.CTkEntry(content_body, placeholder_text="Menge")
                e_qty.insert(0, str(det.get("Menge", "")))
                e_qty.grid(row=r, column=1, sticky="ew", padx=8, pady=2)
                detail_widgets.append((e_isin, e_qty))

            ctk.CTkButton(content_body, text="Position hinzufügen", command=add_row).grid(
                row=len(detail_widgets) + 4, column=0, sticky="w", pady=(6, 0)
            )
        else:
            ctk.CTkLabel(content_body, text="Saldo", font=("Arial", 13, "bold")).grid(row=3, column=0, sticky="w", pady=(8, 4))
            e_bal = ctk.CTkEntry(content_body, placeholder_text="Saldo")
            e_bal.grid(row=4, column=0, sticky="ew")
            detail_widgets = [e_bal]

        for w in nav_body.winfo_children():
            w.destroy()
        if idx > 0:
            ctk.CTkButton(nav_body, text="← Zurück", command=lambda: save_and_navigate(idx - 1)).grid(row=0, column=0, padx=6, sticky="ew")
        next_label = "Speichern und berechnen" if idx == len(konten) - 1 else "Weiter →"
        ctk.CTkButton(nav_body, text=next_label, command=lambda: save_and_navigate(idx + 1)).grid(row=0, column=1, padx=6, sticky="ew")

    def save_and_navigate(next_idx):
        konto = konten[current_index]
        if konto.get("Kontotyp") == "Depot":
            details = []
            for e_isin, e_qty in detail_widgets:
                isin = e_isin.get().strip()
                try:
                    menge = float(e_qty.get())
                except Exception:
                    menge = 0.0
                if isin:
                    details.append({"ISIN": isin, "Menge": menge})
            state.overview_inputs[current_index] = {"konto": konto, "details": details}
        else:
            try:
                bal = float(detail_widgets[0].get())
            except Exception:
                bal = 0.0
            state.overview_inputs[current_index] = {"konto": konto, "balance": bal}

        if next_idx < len(konten):
            show_account(next_idx)
        else:
            ac.calculate_festgeld(person, state.selected_date)
            ac.update_account_overview(person, state.selected_date, state.overview_inputs)
            state.load_all()
            set_status(status, "Kontoübersicht erfolgreich gespeichert.", "success")
            navigator.navigate("PersonInfo")

    def add_row():
        row = len(detail_widgets) + 4
        e_isin = ctk.CTkEntry(content_body, placeholder_text="ISIN")
        e_isin.grid(row=row, column=0, sticky="ew", pady=2)
        e_qty = ctk.CTkEntry(content_body, placeholder_text="Menge")
        e_qty.grid(row=row, column=1, sticky="ew", padx=8, pady=2)
        detail_widgets.append((e_isin, e_qty))

    set_status(status, "Bitte zunächst den Stichtag festlegen.", "info")
