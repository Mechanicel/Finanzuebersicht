# screens/screen_account_summary.py

import customtkinter
from tkcalendar import DateEntry
from helper.universalMethoden import clear_ui, zentrieren
from data_manager import *
def account_summary_screen(app, navigator, selected_person, **kwargs):
    """
    Zeigt für jedes Konto der Person den Kontostand zum gewählten Datum
    anhand des Eintrags in 'Kontostaende' an. Falls kein Eintrag vorhanden ist,
    wird 0.00 angezeigt.

    Am Ende wird eine Summenzeile ausgegeben.

    Aufbau der Tabelle (textbasiert):
      Kontotyp | Bank | Kontostand
      ----------------------------
      ...
      Summenzeile

    Hinweis:
      - Wir lesen 'Kontostaende' im Format ["YYYY-MM-DD: 123.45", ...].
      - Wir vergleichen das gewählte Datum (aus dem DateEntry) mit dem Eintrag.
      - Wird ein passender Eintrag gefunden, parseFloat -> Kontostand.
      - Sonst 0.0.
    """

    clear_ui(app)

    # -------------------------------------------------
    # 1) Grund-UI
    # -------------------------------------------------
    btn_back = customtkinter.CTkButton(
        app,
        text="Zurück",
        command=lambda: navigator.navigate("person_info", selected_person=selected_person)
    )
    btn_back.grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky='w')

    label_title = customtkinter.CTkLabel(app, text="Kontostände pro Tag")
    label_title.grid(row=1, column=0, columnspan=2, padx=20, pady=10)

    label_datum = customtkinter.CTkLabel(app, text="Datum:")
    label_datum.grid(row=2, column=0, padx=20, pady=10, sticky='e')

    date_entry = DateEntry(app, format='%Y-%m-%d')
    date_entry.grid(row=2, column=1, padx=20, pady=10, sticky='w')

    btn_show = customtkinter.CTkButton(
        app,
        text="Anzeigen",
        command=lambda: zeige_kontostaende_fuer_tag(date_entry.get_date())
    )
    btn_show.grid(row=3, column=0, columnspan=2, padx=20, pady=10)

    summary_label = customtkinter.CTkLabel(app, text="Hier wird das Ergebnis angezeigt")
    summary_label.grid(row=4, column=0, columnspan=2, padx=20, pady=10)

    zentrieren(app)

    # -------------------------------------------------
    # 2) Funktion: Kontostände pro Tag anzeigen
    # -------------------------------------------------
    def zeige_kontostaende_fuer_tag(gewähltes_datum):
        """
        Liest für jedes Konto der Person den 'Kontostand' zum gewählten Datum
        aus 'Kontostaende' (Format "YYYY-MM-DD: 123.45").
        Wird kein Eintrag gefunden, 0.0.
        Gibt eine textbasierte Tabelle aus.
        """
        try:
            konten = get_person_konten(selected_person)
        except Exception as e:
            summary_label.configure(text=f"Fehler beim Laden der Konten: {e}")
            return

        # Baue tabellen_zeilen: [[Kontotyp, Bank, Kontostand], ...]
        tabellen_zeilen = []
        tabellen_zeilen.append(["Kontotyp", "Bank", "Kontostand"])

        gesamt_summe = 0.0
        for konto in konten:
            kt = konto.get("Kontotyp", "Unbekannt")
            bank = konto.get("Bank", "Unbekannt")
            kontostand = get_kontostand_am_tag(konto, gewähltes_datum)
            gesamt_summe += kontostand
            tabellen_zeilen.append([kt, bank, f"{kontostand:.2f}"])

        # Summenzeile
        tabellen_zeilen.append(["-", "-", f"{gesamt_summe:.2f}"])

        # Formatiere die Tabelle
        col_widths = [0, 0, 0]
        for row in tabellen_zeilen:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(cell))

        lines = []
        # Kopfzeile
        header = (
            f"{tabellen_zeilen[0][0].ljust(col_widths[0])} | "
            f"{tabellen_zeilen[0][1].ljust(col_widths[1])} | "
            f"{tabellen_zeilen[0][2].rjust(col_widths[2])}"
        )
        lines.append(header)
        lines.append("-" * (sum(col_widths) + 6))

        # Daten
        for row in tabellen_zeilen[1:]:
            line = (
                f"{row[0].ljust(col_widths[0])} | "
                f"{row[1].ljust(col_widths[1])} | "
                f"{row[2].rjust(col_widths[2])}"
            )
            lines.append(line)

        ausgabe = "\n".join(lines)
        summary_label.configure(text=ausgabe)

    # -------------------------------------------------
    # 3) Hilfsfunktion: get_kontostand_am_tag
    # -------------------------------------------------
    def get_kontostand_am_tag(konto, gewähltes_datum):
        """
        Durchsucht konto["Kontostaende"] nach einem Eintrag "YYYY-MM-DD: val"
        mit dem Datum == gewähltes_datum (als date).
        Gibt val zurück (float). Falls nicht gefunden, 0.0.

        Format in Kontostaende: ["2025-01-01: 123.45", ...]
        """
        kontostaende = konto.get("Kontostaende", [])
        datum_str = gewähltes_datum.strftime("%Y-%m-%d")
        for eintrag in kontostaende:
            try:
                parts = eintrag.split(": ")
                if len(parts) == 2:
                    eintrags_datum, wert_str = parts
                    if eintrags_datum == datum_str:
                        return float(wert_str)
            except:
                pass
        return 0.0
