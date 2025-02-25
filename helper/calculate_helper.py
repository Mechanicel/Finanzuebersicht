# helper/calculate_helper.py

import json
from datetime import datetime, timedelta

def calculate_logic(selected_person):
    """
    Verändert die Festgeld-Logik so, dass für jedes Festgeldkonto der Person
    ein neuer Eintrag in 'Kontostaende' (mit heutigem Datum und dem berechneten Wert)
    hinzugefügt wird, anstatt die Werte auszugeben.

    Annahmen:
    - 'personen.json' existiert und enthält die Daten der Person (Name, Nachname, Konten).
    - Jedes Festgeldkonto enthält:
        * "Anlagebetrag" (z. B. "1000")
        * "Zinssatz" (z. B. "10")
        * "Anlagedatum" (z. B. "2025-01-01")
        * "Laufzeit_in_Tagen" (z. B. "180")
    - Wir rechnen mit einem 360-Tage-Jahr.
    - Nach Ablauf der Laufzeit (Anlagedatum + Laufzeit_in_Tagen) werden keine weiteren
      Zinsen gutgeschrieben (Wert wird gedeckelt).

    Ablauf:
      1. Lade 'personen.json'.
      2. Finde den Eintrag für die gewählte Person.
      3. Iteriere über ihre Konten:
         - Nur bei "Kontotyp": "Festgeldkonto" rechnen wir.
         - Bestimme den Wert (Anlagebetrag + aufgelaufene Zinsen).
         - Hänge an 'Kontostaende' ein "YYYY-MM-DD: <wert>" an (für heutiges Datum).
      4. Speichere die geänderte 'personen.json'.
    """

    # 1) Lade personen.json
    try:
        with open("personen.json", "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as e:
        print(f"[Calculate Logic] Fehler beim Laden von personen.json: {e}")
        return

    # 2) Finde den Datensatz der Person
    person_data = None
    for p in data.get("personen", []):
        if (p.get("Name") == selected_person.get("Name")
            and p.get("Nachname") == selected_person.get("Nachname")):
            person_data = p
            break

    if not person_data:
        print("[Calculate Logic] Keine Daten für diese Person gefunden.")
        return

    konten = person_data.get("Konten", [])
    if not konten:
        print("[Calculate Logic] Diese Person hat keine Konten.")
        return

    # Heutiges Datum
    heute_date = datetime.now().date()
    heute_str = heute_date.strftime("%Y-%m-%d")

    # 3) Iteriere über Konten
    for konto in konten:
        if konto.get("Kontotyp") != "Festgeldkonto":
            # Nur Festgeldkonten bearbeiten
            continue

        # Anlagebetrag
        anlage_str = konto.get("Anlagebetrag", "0")
        try:
            anlagebetrag = float(anlage_str)
        except:
            anlagebetrag = 0.0

        # Zinssatz
        zins_str = konto.get("Zinssatz", "0")
        try:
            zinssatz = float(zins_str)
        except:
            zinssatz = 0.0

        # Anlagedatum
        anlagedatum_str = konto.get("Anlagedatum", "")
        try:
            anlagedatum_date = datetime.strptime(anlagedatum_str, "%Y-%m-%d").date()
        except:
            # Ungültiges Anlagedatum => wir speichern nur den Anlagebetrag
            # (keine Zinsen)
            wert = anlagebetrag
            update_kontostaende(konto, heute_str, wert)
            continue

        # Laufzeit
        laufzeit_str = konto.get("Laufzeit_in_Tagen", "0")
        try:
            laufzeit_tage = int(laufzeit_str)
        except:
            laufzeit_tage = 0

        end_date = anlagedatum_date + timedelta(days=laufzeit_tage)

        # Berechne verstrichene Tage
        if heute_date < anlagedatum_date:
            # Vor Anlagedatum => keine Zinsen
            wert = anlagebetrag
        else:
            effektives_ende = min(heute_date, end_date)
            verstrichene_tage = (effektives_ende - anlagedatum_date).days
            if verstrichene_tage < 0:
                verstrichene_tage = 0

            # Zinsen
            zinsen = anlagebetrag * (zinssatz / 100.0) * (verstrichene_tage / 360.0)
            wert = anlagebetrag + zinsen

        # 4) Füge in 'Kontostaende' den Eintrag für heute hinzu
        update_kontostaende(konto, heute_str, wert)

    # 5) Speichere die geänderte persons.json
    try:
        with open("personen.json", "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        print("[Calculate Logic] Festgeldwerte erfolgreich in personen.json aktualisiert.")
    except Exception as e:
        print(f"[Calculate Logic] Fehler beim Speichern von personen.json: {e}")

def update_kontostaende(konto, datum_str, wert):
    """
    Hängt an konto['Kontostaende'] einen neuen Eintrag 'datum_str: wert' an.
    Falls 'Kontostaende' nicht existiert, wird sie erzeugt.
    Wir überschreiben ggf. bereits vorhandene Einträge zum selben Datum.
    """
    if "Kontostaende" not in konto:
        konto["Kontostaende"] = []

    # Vorhandene Einträge in ein dict umwandeln
    # Format: "YYYY-MM-DD: 123.45"
    existing = {}
    for entry in konto["Kontostaende"]:
        parts = entry.split(": ")
        if len(parts) == 2:
            existing_date, existing_val = parts
            existing[existing_date] = existing_val

    # Neuen Wert eintragen/überschreiben
    existing[datum_str] = f"{wert:.2f}"

    # Zurück in Liste
    konto["Kontostaende"] = [f"{d}: {existing[d]}" for d in sorted(existing)]
