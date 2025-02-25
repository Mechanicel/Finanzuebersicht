# screens/screen_account_overview.py
from datetime import datetime
import json
import customtkinter
from tkcalendar import DateEntry
from data_manager import get_person_konten
from helper.universalMethoden import clear_ui, zentrieren

def account_overview_screen(app, navigator, selected_person, **kwargs):
    """
    Zeigt der Reihe nach alle Konten einer Person an und erlaubt die Eingabe
    eines neuen Kontostands plus Datum. Ein 'Zurück'-Button ist vorhanden,
    verschwindet aber, sobald der Benutzer den ersten Kontostand gespeichert hat.
    """

    clear_ui(app)
    konten = get_person_konten(selected_person)
    kontostaende = {}
    index = [0]  # mutable Zähler für das aktuelle Konto

    # -------------------------------------------------
    # Zurück-Button (zu Beginn sichtbar)
    # -------------------------------------------------
    btn_back = customtkinter.CTkButton(
        app,
        text="Zurück",
        command=lambda: navigator.navigate("person_info", selected_person=selected_person)
    )
    btn_back.grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky='w')

    # -------------------------------------------------
    # Konto-Label (für Kontotyp/Bank/BIC etc.)
    # -------------------------------------------------
    label_acct = customtkinter.CTkLabel(app, text="Konto:")
    label_acct.grid(row=1, column=0, columnspan=2, padx=20, pady=10)

    # -------------------------------------------------
    # Kontostand und Datum
    # -------------------------------------------------
    customtkinter.CTkLabel(app, text="Kontostand:").grid(row=2, column=0, padx=20, pady=10)
    entry_balance = customtkinter.CTkEntry(app)
    entry_balance.grid(row=2, column=1, padx=20, pady=10)

    customtkinter.CTkLabel(app, text="Datum:").grid(row=3, column=0, padx=20, pady=10)
    entry_date = DateEntry(app, date_pattern='yyyy-mm-dd')
    entry_date.grid(row=3, column=1, padx=20, pady=10)

    # -------------------------------------------------
    # Buttons für Weiter und Fertig
    # -------------------------------------------------
    btn_next = customtkinter.CTkButton(app, text="Weiter")
    btn_next.grid(row=4, column=0, columnspan=2, padx=20, pady=10)

    btn_finish = customtkinter.CTkButton(app, text="Fertig", state="disabled")
    btn_finish.grid(row=5, column=0, columnspan=2, padx=20, pady=10)

    # -------------------------------------------------
    # update_ui() - zeigt das aktuelle Konto an
    # -------------------------------------------------
    def update_ui():
        """Zeigt Informationen zum aktuellen Konto an und setzt die Eingabefelder zurück."""
        if index[0] < len(konten):
            acct = konten[index[0]]
            # Baue Info-Text für Kontotyp, Bank, BIC, Kontonummer etc.
            info_lines = []

            # Beispielhafte Felder
            if "Kontotyp" in acct:
                info_lines.append(f"Kontotyp: {acct['Kontotyp']}")
            if "Bank" in acct:
                info_lines.append(f"Bank: {acct['Bank']}")
            if "BIC" in acct:
                info_lines.append(f"BIC: {acct['BIC']}")
            if "Kontonummer" in acct:
                info_lines.append(f"Kontonummer: {acct['Kontonummer']}")
            if "Deponummer" in acct:
                info_lines.append(f"Deponummer: {acct['Deponummer']}")
            # Weitere Felder (optional)
            for field in ["Laufzeit", "Zinssatz", "Erstelldatum", "Endedatum"]:
                if field in acct:
                    info_lines.append(f"{field}: {acct[field]}")

            label_acct.configure(text="\n".join(info_lines))
            # Eingabefelder zurücksetzen
            entry_balance.delete(0, customtkinter.END)
            entry_date.set_date(datetime.today())

            # Buttons
            btn_next.configure(state="normal")
        else:
            # Keine Konten mehr -> Label anpassen und "Weiter" deaktivieren
            label_acct.configure(text="Keine Konten vorhanden")
            entry_balance.delete(0, customtkinter.END)
            btn_next.configure(state="disabled")
            btn_finish.invoke()  # Automatisch fertig, wenn keine Konten mehr

    # -------------------------------------------------
    # Speichert Kontostand + Datum
    # -------------------------------------------------
    def save_account():
        if index[0] < len(konten):
            acct = konten[index[0]]
            balance = entry_balance.get().strip()
            date_val = entry_date.get_date().strftime('%Y-%m-%d')
            key = f"{acct.get('BIC','')}_{acct.get('Kontonummer', acct.get('Deponummer',''))}"
            if key not in kontostaende:
                kontostaende[key] = []
            kontostaende[key].append(f"{date_val}: {balance}")

            # Personen.json aktualisieren
            try:
                with open("personen.json", "r") as file:
                    data = json.load(file)
                for person in data.get("personen", []):
                    if (person["Name"] == selected_person["Name"] and
                        person["Nachname"] == selected_person["Nachname"]):
                        for acct_data in person.get("Konten", []):
                            if (acct_data.get("BIC","") == acct.get("BIC","") and
                                acct_data.get("Kontonummer","") == acct.get("Kontonummer","") and
                                acct_data.get("Deponummer","") == acct.get("Deponummer","")):
                                if "Kontostaende" not in acct_data:
                                    acct_data["Kontostaende"] = []
                                existing = {}
                                for s in acct_data["Kontostaende"]:
                                    parts = s.split(": ")
                                    if len(parts) == 2:
                                        existing[parts[0]] = parts[1]
                                existing[date_val] = balance
                                acct_data["Kontostaende"] = [f"{d}: {existing[d]}" for d in sorted(existing)]
                with open("personen.json", "w") as file:
                    json.dump(data, file, indent=4)
            except Exception as e:
                print(e)

    # -------------------------------------------------
    # next_account(): Speichert und geht zum nächsten
    # -------------------------------------------------
    def next_account():
        # Sobald der Benutzer den ersten Kontostand speichert, entfernen wir den Zurück-Button.
        if index[0] == 0:
            btn_back.grid_forget()

        save_account()
        index[0] += 1
        update_ui()

    # -------------------------------------------------
    # finish(): Letztes Konto speichern und zurück
    # -------------------------------------------------
    def finish():
        save_account()
        navigator.navigate("person_info", selected_person=selected_person)

    # -------------------------------------------------
    # Button-Commands
    # -------------------------------------------------
    btn_next.configure(command=next_account)
    btn_finish.configure(command=finish)

    # -------------------------------------------------
    # check_finish(): Aktiviert "Fertig" beim letzten Konto
    # -------------------------------------------------
    def check_finish():
        if index[0] < len(konten):
            # Falls letztes Konto und Kontostand vorhanden
            if index[0] == len(konten) - 1 and entry_balance.get().strip():
                btn_finish.configure(state="normal")
        else:
            # Keine Konten -> Fertig freischalten
            btn_finish.configure(state="normal")

    entry_balance.bind("<KeyRelease>", lambda e: check_finish())

    # -------------------------------------------------
    # UI initialisieren
    # -------------------------------------------------
    update_ui()
    zentrieren(app)
