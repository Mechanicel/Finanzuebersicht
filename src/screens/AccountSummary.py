import customtkinter
from tkcalendar import DateEntry
from datetime import datetime
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.data.DataManager import DataManager

def create_screen(app, navigator, selected_person, **kwargs):
    clear_ui(app)
    dm = DataManager()
    person_data = dm.get_person_data(selected_person)
    konten = person_data.get("Konten", []) if person_data else []

    # Zurück-Button
    btn_back = customtkinter.CTkButton(
        app,
        text="Zurück",
        command=lambda: navigator.navigate("PersonInfo", selected_person=selected_person)
    )
    btn_back.grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky="w")

    # Titel
    label_title = customtkinter.CTkLabel(app, text="Kontostände pro Tag")
    label_title.grid(row=1, column=0, columnspan=2, padx=20, pady=10)

    # Datumsauswahl
    label_datum = customtkinter.CTkLabel(app, text="Datum:")
    label_datum.grid(row=2, column=0, padx=20, pady=10, sticky="e")
    date_entry = DateEntry(app, date_pattern='yyyy-mm-dd')
    date_entry.grid(row=2, column=1, padx=20, pady=10, sticky="w")

    # Button zum Anzeigen
    btn_show = customtkinter.CTkButton(
        app,
        text="Anzeigen",
        command=lambda: zeige_kontostaende_fuer_tag(
            date_entry.get_date(), konten, app
        )
    )
    btn_show.grid(row=3, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)

def zeige_kontostaende_fuer_tag(gew_datum, konten, app):
    """
    Zeigt für jedes Konto den gespeicherten Kontostand zum gewählten Datum
    aus dem Eintrag in 'Kontostaende'. Falls kein Eintrag existiert, 0.00.
    """
    # Baue Tabelle
    tab_zeilen = [["Kontotyp", "Bank", "Kontostand"]]
    gesamt = 0.0

    for konto in konten:
        kt = konto.get("Kontotyp", "Unbekannt")
        bank = konto.get("Bank", "Unbekannt")

        # Ließt aus Kontostaende den Wert zum Datum
        wert = get_kontostand_am_tag(konto, gew_datum)

        gesamt += wert
        tab_zeilen.append([kt, bank, f"{wert:.2f}"])

    # Summenzeile
    tab_zeilen.append(["-", "-", f"{gesamt:.2f}"])

    # Textformatierung
    col_w = [max(len(row[i]) for row in tab_zeilen) for i in range(3)]
    lines = []
    header = (
        f"{tab_zeilen[0][0].ljust(col_w[0])} | "
        f"{tab_zeilen[0][1].ljust(col_w[1])} | "
        f"{tab_zeilen[0][2].rjust(col_w[2])}"
    )
    lines.append(header)
    lines.append("-" * (sum(col_w) + 6))
    for row in tab_zeilen[1:]:
        lines.append(
            f"{row[0].ljust(col_w[0])} | "
            f"{row[1].ljust(col_w[1])} | "
            f"{row[2].rjust(col_w[2])}"
        )
    ausgabe = "\n".join(lines)

    # Anzeige
    summary_label = customtkinter.CTkLabel(app, text=ausgabe)
    summary_label.grid(row=4, column=0, columnspan=2, padx=20, pady=10)

def get_kontostand_am_tag(konto, gew_datum):
    """
    Durchsucht konto["Kontostaende"] nach "YYYY-MM-DD: Wert" mit Datum == gew_datum.
    Gibt float zurück, oder 0.0, falls nicht vorhanden.
    """
    datum_str = gew_datum.strftime("%Y-%m-%d")
    for eintrag in konto.get("Kontostaende", []):
        parts = eintrag.split(": ")
        if len(parts) == 2 and parts[0] == datum_str:
            try:
                return float(parts[1])
            except:
                return 0.0
    return 0.0
