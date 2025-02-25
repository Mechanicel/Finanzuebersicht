# data_manager.py
import json

def get_person_konten(person):
    """
    Liefert alle Konten der übergebenen Person aus der 'personen.json'.
    Hier wird person als Dictionary erwartet, z. B. {"Name": ..., "Nachname": ...}
    """
    konten = []
    try:
        with open("personen.json", "r") as file:
            data = json.load(file)
            for p in data.get("personen", []):
                if p["Name"] == person["Name"] and p["Nachname"] == person["Nachname"]:
                    konten = p.get("Konten", [])
    except Exception as e:
        print(f"Fehler beim Laden der Konten: {e}")
    return konten
