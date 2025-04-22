import customtkinter as ctk
from tkcalendar import DateEntry
from datetime import datetime, time
from data.DataManager import DataManager
from controllers.AccountController import AccountController
from src.helpers.UniversalMethoden import clear_ui


def create_screen(app, navigator, selected_person):
    clear_ui(app)
    dm = DataManager()
    ac = AccountController()
    person_data = dm.get_person_data(selected_person) or {}
    # Alle Festgeldkonten überspringen
    konten = [k for k in person_data.get("Konten", []) if k.get("Kontotyp") != "Festgeldkonto"]

    inputs = []
    index = -1
    selected_date = None

    # Widgets für wiederverwendbare Referenzen
    entry_date = None
    entry_balance = None
    frame_details = None
    rows = []
    btn_add = None

    # Schriftarten definieren
    TITLE_FONT = ("Arial", 20, "bold")
    SUBTITLE_FONT = ("Arial", 16)

    def show_date():
        nonlocal entry_date, index
        clear_ui(app)
        # Header
        header_frame = ctk.CTkFrame(app)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="we", pady=(20,10))
        header_label = ctk.CTkLabel(header_frame, text="Kontoübersicht", font=TITLE_FONT)
        header_label.pack(padx=20, pady=10)
        # Stichtag-Auswahl
        date_label = ctk.CTkLabel(app, text="Wähle Stichtag:", font=SUBTITLE_FONT)
        date_label.grid(row=1, column=0, padx=20, pady=10, sticky="e")
        entry_date = DateEntry(app, date_pattern='yyyy-mm-dd', width=12)
        entry_date.grid(row=1, column=1, padx=20, pady=10, sticky="w")
        # Weiter-Button
        btn_next = ctk.CTkButton(app, text="Weiter", width=12, command=on_next)
        btn_next.grid(row=2, column=0, columnspan=2, pady=(0,20))
        # Spalten konfigurieren
        app.grid_columnconfigure(0, weight=1)
        app.grid_columnconfigure(1, weight=1)

    def show_account():
        nonlocal entry_balance, frame_details, rows, btn_add, index
        clear_ui(app)
        konto = konten[index]
        # Kontoinfo-Header
        header = ctk.CTkLabel(
            app,
            text=f"{konto.get('Kontotyp')} – {konto.get('Bank','')} {konto.get('Kontonummer', konto.get('Deponummer',''))}",
            font=SUBTITLE_FONT
        )
        header.grid(row=0, column=0, columnspan=2, pady=(20,10))

        if konto.get('Kontotyp') == 'Depot':
            # Depot-Details-Frame
            frame_details = ctk.CTkFrame(app)
            frame_details.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
            frame_details.columnconfigure((0,1), weight=1)
            # Spaltenüberschriften
            ctk.CTkLabel(frame_details, text="ISIN", font=("Arial", 12, "underline")).grid(row=0, column=0, padx=5)
            ctk.CTkLabel(frame_details, text="Menge", font=("Arial", 12, "underline")).grid(row=0, column=1, padx=5)
            rows = []

            def make_add_row():
                r = len(rows) + 1
                e_isin = ctk.CTkEntry(frame_details, placeholder_text="DE000...")
                e_menge = ctk.CTkEntry(frame_details, placeholder_text="0.0")
                e_isin.grid(row=r, column=0, padx=5, pady=2, sticky="ew")
                e_menge.grid(row=r, column=1, padx=5, pady=2, sticky="ew")
                rows.append((e_isin, e_menge))
                btn_add.grid(row=len(rows)+1, column=0, columnspan=2, pady=(10,5))

            btn_add = ctk.CTkButton(frame_details, text="Position hinzufügen", command=make_add_row)
            # Vorbefüllung
            for detail in konto.get('DepotDetails', []):
                make_add_row()
                rows[-1][0].insert(0, detail.get('ISIN',''))
                rows[-1][1].insert(0, str(detail.get('Menge','')))
            btn_add.grid(row=len(rows)+1, column=0, columnspan=2, pady=(10,5))

        else:
            # Manuelle Saldo-Eingabe für Nicht-Depot
            entry_balance = ctk.CTkEntry(app, placeholder_text="z.B. 1000.00")
            entry_balance.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")

        # Weiter oder Fertig
        btn_label = "Weiter" if index < len(konten)-1 else "Fertig"
        btn_next = ctk.CTkButton(app, text=btn_label, width=12, command=on_next)
        btn_next.grid(row=2, column=0, columnspan=2, pady=(0,20))
        app.grid_columnconfigure(0, weight=1)
        app.grid_columnconfigure(1, weight=1)

    def on_next():
        nonlocal index, selected_date, entry_balance, rows
        if index == -1:
            # Datum übernehmen
            d = entry_date.get_date()
            selected_date = datetime.combine(d, time.min)
            index = 0
            show_account()
            return

        konto = konten[index]
        if konto.get('Kontotyp') == 'Depot':
            details = []
            for e_isin, e_menge in rows:
                isin_val = e_isin.get().strip()
                try:
                    menge_val = float(e_menge.get())
                except:
                    menge_val = 0.0
                if isin_val:
                    details.append({'ISIN': isin_val, 'Menge': menge_val})
            inputs.append({'konto': konto, 'details': details})
        else:
            try:
                bal = float(entry_balance.get())
            except:
                bal = 0.0
            inputs.append({'konto': konto, 'balance': bal})

        index += 1
        if index < len(konten):
            show_account()
        else:
            ac.update_account_overview(selected_person, selected_date, inputs)
            navigator.navigate("PersonInfo", selected_person=selected_person)

    # Start
    show_date()