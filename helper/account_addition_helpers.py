# account_helpers.py

import json
from datetime import datetime

def load_account_types():
    """
    Lädt die Kontotypen aus 'kontotypen.json' und gibt ein Dict {Kontotyp: [Felder]} zurück.
    Beispiel: { "Girokonto": ["Bank", "Kontonummer", "Erstellungsdatum"], ... }
    """
    try:
        with open("kontotypen.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        return {
            list(item.keys())[0]: list(item.values())[0]
            for item in data.get("Kontotypen", [])
        }
    except Exception as e:
        print("Fehler beim Laden von kontotypen.json:", e)
        return {}

def load_banks_for_person(selected_person):
    """
    Lädt die Banken, die in 'personen.json' für die übergebene Person hinterlegt sind.
    Gibt eine Liste von Banknamen zurück, z. B. ["Deutsche Bank", "Commerzbank"].
    """
    try:
        with open("personen.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        for person in data.get("personen", []):
            if (person.get("Name") == selected_person.get("Name")
                and person.get("Nachname") == selected_person.get("Nachname")):
                return person.get("Banken", [])
        return []
    except Exception as e:
        print("Fehler beim Laden der Banken aus personen.json:", e)
        return []

def get_bics_for_bank(bank_name):
    """
    Liest aus 'banken.json' alle BICs für eine Bank aus und gibt sie als Liste zurück.
    """
    try:
        with open("banken.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        for bank in data.get("Banken", []):
            if bank["Name"] == bank_name:
                return bank.get("BIC", [])
        return []
    except Exception as e:
        print("Fehler beim Abrufen der BICs:", e)
        return []

def get_blzs_for_bank(bank_name):
    """
    Liest aus 'banken.json' alle BLZs für eine Bank aus und gibt sie als Liste zurück.
    """
    try:
        with open("banken.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        for bank in data.get("Banken", []):
            if bank["Name"] == bank_name:
                return bank.get("BLZ", [])
        return []
    except Exception as e:
        print("Fehler beim Abrufen der BLZs:", e)
        return []

def load_own_accounts(selected_person):
    """
    Lädt alle Konten der Person aus 'personen.json', um sie als eigenes Auszahlungskonto anzubieten.
    Gibt eine Liste von Strings zurück, z. B. ["Girokonto DE1234567890", "Depot DEP0001"].

    Du kannst das Format frei wählen – hier ein Beispiel:
    <Kontotyp> <Kontonummer oder Deponummer>
    """
    konten_liste = []
    try:
        with open("personen.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        for person in data.get("personen", []):
            if (person.get("Name") == selected_person.get("Name")
                and person.get("Nachname") == selected_person.get("Nachname")):
                for konto in person.get("Konten", []):
                    kt = konto.get("Kontotyp", "Unbekannt")
                    if "Kontonummer" in konto:
                        bezeichnung = f"{kt} {konto['Kontonummer']}"
                    elif "Deponummer" in konto:
                        bezeichnung = f"{kt} {konto['Deponummer']}"
                    else:
                        bezeichnung = kt
                    konten_liste.append(bezeichnung)
                break
    except Exception as e:
        print("Fehler beim Laden eigener Konten:", e)

    return konten_liste

def duplicate_account(selected_person, acct_type, acct_data):
    """
    Prüft, ob bereits ein Konto mit gleicher Kombination (Kontotyp, Bank und Kontonummer/Deponummer) existiert.
    """
    try:
        with open("personen.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        for person in data.get("personen", []):
            if (person["Name"] == selected_person["Name"]
                and person["Nachname"] == selected_person["Nachname"]):
                for acct in person.get("Konten", []):
                    if acct.get("Kontotyp") == acct_type and acct.get("Bank") == acct_data.get("Bank"):
                        # Prüfe Kontonummer vs. Deponummer
                        key = "Kontonummer" if "Kontonummer" in acct_data else "Deponummer"
                        if key in acct and key in acct_data and acct[key] == acct_data[key]:
                            return True
        return False
    except Exception as e:
        print("Fehler bei Duplikatprüfung:", e)
        return False

def update_account(selected_person, acct_type, acct_data):
    """
    Speichert das neue Konto in 'personen.json'.
    """
    try:
        with open("personen.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        for p in data.get("personen", []):
            if p["Name"] == selected_person["Name"] and p["Nachname"] == selected_person["Nachname"]:
                if "Konten" not in p:
                    p["Konten"] = []
                new_account = {"Kontotyp": acct_type}
                new_account.update(acct_data)
                p["Konten"].append(new_account)

                with open("personen.json", "w", encoding="utf-8") as outfile:
                    json.dump(data, outfile, indent=4)
                return
    except Exception as e:
        print("Fehler beim Speichern des Kontos:", e)

def compute_iban_de(blz, kontonummer):
    """
    Erzeugt eine vereinfachte IBAN nach dem Schema 'DE00' + BLZ + Kontonummer.
    KEINE echte Prüfzifferberechnung (mod 97).
    """
    return f"DE00{blz}{kontonummer}"
