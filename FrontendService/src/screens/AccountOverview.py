# src/screens/AccountOverview.py

import customtkinter as ctk
from tkcalendar import DateEntry
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.models.AppState import AppState

def create_screen(app, navigator, state: AppState, **kwargs):
    clear_ui(app)
    person = state.selected_person
    ac = state.account_controller
    konten = [k for k in person.get('Konten', []) if k.get('Kontotyp') != 'Festgeldkonto']

    # Haupt-Container
    container = ctk.CTkFrame(app, corner_radius=8)
    container.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)

    container.grid_columnconfigure(0, weight=1)
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)
    # Datumsauswahl
    date_frame = ctk.CTkFrame(container)
    date_frame.grid(row=0, column=0, sticky="ew", pady=(0,16))
    date_frame.grid_columnconfigure((0,1), weight=1)
    ctk.CTkLabel(date_frame, text="Stichtag wählen", font=("Arial", 16, "bold"))\
        .grid(row=0, column=0, columnspan=2, pady=(0,8))
    date_entry = DateEntry(date_frame, date_pattern='yyyy-mm-dd', width=20)
    date_entry.grid(row=1, column=0, sticky="e", padx=(0,8))
    ctk.CTkButton(date_frame, text="Weiter", command=lambda: on_date_selected())\
        .grid(row=1, column=1, sticky="w")

    # dynamische Frames
    content_frame = ctk.CTkFrame(container, fg_color="transparent")
    nav_frame     = ctk.CTkFrame(container, fg_color="transparent")

    current_index   = 0
    detail_widgets  = []
    add_button      = None  # Referenz auf den "Position hinzufügen"-Button

    def on_date_selected():
        state.selected_date   = date_entry.get_date()
        state.overview_inputs = [None] * len(konten)
        date_frame.destroy()
        content_frame.grid(row=0, column=0, sticky="nsew")
        nav_frame.grid(row=1, column=0, sticky="ew", pady=(16,0))
        show_account(0)

    def show_account(idx: int):
        nonlocal current_index, detail_widgets, add_button
        current_index = idx
        # clear content
        for w in content_frame.winfo_children():
            w.destroy()
        detail_widgets = []

        konto = konten[idx]
        # Meta-Info
        meta = ctk.CTkFrame(content_frame)
        meta.grid(row=0, column=0, sticky="ew", pady=(0,8))
        meta.grid_columnconfigure((0,1), weight=1)
        ctk.CTkLabel(meta, text=f"{konto.get('Kontotyp')}", font=("Arial", 14, "bold"))\
            .grid(row=0, column=0, sticky="w")
        num = konto.get("Kontonummer", konto.get("Deponummer", "–"))
        ctk.CTkLabel(meta, text=f"Nummer: {num}")\
            .grid(row=1, column=0, sticky="w", pady=(4,0))
        ctk.CTkLabel(meta, text=f"BIC: {konto.get('BIC','–')}")\
            .grid(row=1, column=1, sticky="e", pady=(4,0))

        if konto.get('Kontotyp') == 'Depot' and konto.get("Verrechnungskonto"):
            ctk.CTkLabel(meta, text=f"Verrechnungskonto: {konto.get('Verrechnungskonto')}")\
                .grid(row=2, column=0, columnspan=2, sticky="w", pady=(4,0))

        # Eingabe-Bereich
        if konto.get('Kontotyp') == 'Depot':
            for r, det in enumerate(konto.get('DepotDetails', [])):
                e_isin = ctk.CTkEntry(content_frame, placeholder_text="ISIN", width=240)
                e_isin.insert(0, det.get('ISIN',''))
                e_isin.grid(row=r+1, column=0, sticky="ew", padx=5, pady=4)
                e_qty = ctk.CTkEntry(content_frame, placeholder_text="Menge", width=80)
                e_qty.insert(0, str(det.get('Menge','')))
                e_qty.grid(row=r+1, column=1, sticky="ew", padx=5, pady=4)
                detail_widgets.append((e_isin, e_qty))
            # Button dynamisch positionieren
            if add_button:
                add_button.destroy()
            add_button = ctk.CTkButton(
                content_frame, text="Position hinzufügen", width=200, command=add_row
            )
            add_button.grid(row=len(detail_widgets)+1, column=0, columnspan=2, pady=(8,0))
        else:
            e_bal = ctk.CTkEntry(content_frame, placeholder_text="Saldo", width=240)
            e_bal.grid(row=1, column=0, columnspan=2, pady=(4,0))
            detail_widgets = [e_bal]
            # keinen add_button für andere Kontotypen
            if add_button:
                add_button.destroy()
                add_button = None

        # Navigation Buttons
        for w in nav_frame.winfo_children():
            w.destroy()
        if idx > 0:
            ctk.CTkButton(
                nav_frame, text="← Zurück", width=100,
                command=lambda: save_and_navigate(idx-1)
            ).grid(row=0, column=0, padx=(0,8))
        btn_text = "Fertig" if idx == len(konten)-1 else "Weiter →"
        ctk.CTkButton(
            nav_frame, text=btn_text, width=100,
            command=lambda: save_and_navigate(idx+1)
        ).grid(row=0, column=1, padx=(8,0))

        zentrieren(container)

    def save_and_navigate(next_idx: int):
        konto = konten[current_index]
        if konto.get('Kontotyp') == 'Depot':
            details = []
            for e_isin, e_qty in detail_widgets:
                isin = e_isin.get().strip()
                try:
                    menge = float(e_qty.get())
                except:
                    menge = 0.0
                if isin:
                    details.append({'ISIN': isin, 'Menge': menge})
            state.overview_inputs[current_index] = {'konto': konto, 'details': details}
        else:
            try:
                bal = float(detail_widgets[0].get())
            except:
                bal = 0.0
            state.overview_inputs[current_index] = {'konto': konto, 'balance': bal}

        if next_idx < len(konten):
            show_account(next_idx)
        else:
            ac.calculate_festgeld(person, state.selected_date)
            ac.update_account_overview(person, state.selected_date, state.overview_inputs)
            state.load_all()
            navigator.navigate("PersonInfo")

    def add_row():
        """Fügt neue Depot-Zeile hinzu und schiebt den Button nach unten."""
        row = len(detail_widgets) + 1
        e_isin = ctk.CTkEntry(content_frame, placeholder_text="ISIN", width=240)
        e_isin.grid(row=row, column=0, padx=5, pady=4, sticky="ew")
        e_qty = ctk.CTkEntry(content_frame, placeholder_text="Menge", width=80)
        e_qty.grid(row=row, column=1, padx=5, pady=4, sticky="ew")
        detail_widgets.append((e_isin, e_qty))
        # Button neu positionieren
        if add_button:
            add_button.grid_configure(row=len(detail_widgets)+1)

    # Start
    zentrieren(app)
