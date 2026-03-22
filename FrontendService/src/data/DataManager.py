import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DataManager:
    """
    DataManager zum Laden, Speichern und Berechnen von Kontodaten.
    Alle aktien-bezogenen Abfragen (Preis, Firmenname, Kennzahlen) sind
    in FileGetStockInfos ausgelagert.
    """

    def __init__(
        self,
        personen_file="data/personen.json",
        banken_file="data/banken.json",
        kontotypen_file="data/kontotypen.json",
    ):
        self.personen_file = personen_file
        self.banken_file = banken_file
        self.kontotypen_file = kontotypen_file
        logger.debug(
            "DataManager: initialized with files personen=%s banken=%s kontotypen=%s",
            personen_file,
            banken_file,
            kontotypen_file,
        )

    def load_personen(self):
        logger.debug("load_personen: Laden aus %s", self.personen_file)
        try:
            with open(self.personen_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            personen = data.get("personen", [])
            logger.debug("load_personen: %d Personen geladen", len(personen))
            return personen
        except Exception:
            logger.exception("load_personen: Fehler beim Laden")
            return []

    def save_personen(self, personen):
        logger.debug("save_personen: Speichere %d Personen", len(personen))
        try:
            with open(self.personen_file, "w", encoding="utf-8") as f:
                json.dump({"personen": personen}, f, indent=4)
            logger.debug("save_personen: Speichern erfolgreich")
        except Exception:
            logger.exception("save_personen: Fehler beim Speichern")

    def get_person_data(self, selected_person):
        logger.debug("get_person_data: Suche nach %s", selected_person)
        for p in self.load_personen():
            if (p.get("Name") == selected_person.get("Name") and
                p.get("Nachname") == selected_person.get("Nachname")):
                logger.debug("get_person_data: Person gefunden")
                return p
        logger.debug("get_person_data: Person nicht gefunden")
        return None

    def save_person_data(self, updated_person):
        logger.debug("save_person_data: Aktualisiere %s", updated_person)
        personen = self.load_personen()
        for i, p in enumerate(personen):
            if (p.get("Name") == updated_person.get("Name") and
                p.get("Nachname") == updated_person.get("Nachname")):
                personen[i] = updated_person
                self.save_personen(personen)
                logger.debug("save_person_data: Aktualisierung erfolgreich")
                return
        logger.warning("save_person_data: Person nicht gefunden")

    def update_account(self, selected_person, account_type, account_data):
        logger.debug("update_account: Hinzufügen %s für %s", account_type, selected_person)
        personen = self.load_personen()
        for person in personen:
            if (person.get("Name") == selected_person.get("Name") and
                person.get("Nachname") == selected_person.get("Nachname")):
                konto = {"Kontotyp": account_type}
                konto.update(account_data)
                person.setdefault("Konten", []).append(konto)
                self.save_personen(personen)
                logger.debug("update_account: Konto hinzugefügt")
                return
        logger.warning("update_account: Person nicht gefunden")

    def duplicate_account(self, selected_person, account_type, account_data):
        logger.debug("duplicate_account: Prüfe Duplikat für %s", selected_person)
        for person in self.load_personen():
            if (person.get("Name") == selected_person.get("Name") and
                person.get("Nachname") == selected_person.get("Nachname")):
                for acct in person.get("Konten", []):
                    if (acct.get("Kontotyp") == account_type and
                        acct.get("Bank") == account_data.get("Bank") and
                        acct.get("Kontonummer", acct.get("Deponummer")) ==
                        account_data.get("Kontonummer", account_data.get("Deponummer"))):
                        logger.debug("duplicate_account: Duplikat gefunden")
                        return True
        logger.debug("duplicate_account: Kein Duplikat")
        return False

    def update_kontostaende(self, konto, datum_str, wert):
        logger.debug("update_kontostaende: %s am %s = %.2f", konto.get('Kontotyp'), datum_str, wert)
        existing = {}
        for entry in konto.get("Kontostaende", []):
            parts = entry.split(": ")
            if len(parts) == 2:
                existing[parts[0]] = parts[1]
        existing[datum_str] = f"{wert:.2f}"
        konto["Kontostaende"] = [f"{d}: {existing[d]}" for d in sorted(existing)]
        logger.debug("update_kontostaende: Aktualisiert")

    def save_account_balance(self, selected_person, account, balance, date_value):
        logger.debug("save_account_balance: %.2f am %s", balance, date_value)
        personen = self.load_personen()
        updated = False
        for i, person in enumerate(personen):
            if (person.get("Name") == selected_person.get("Name") and
                person.get("Nachname") == selected_person.get("Nachname")):
                for acct in person.get("Konten", []):
                    if (acct.get("BIC", "") == account.get("BIC", "") and
                        acct.get("Kontonummer", acct.get("Deponummer")) ==
                        account.get("Kontonummer", account.get("Deponummer"))):
                        self.update_kontostaende(
                            acct,
                            date_value.strftime("%Y-%m-%d"),
                            balance,
                        )
                        updated = True
                        break
                break
        if updated:
            self.save_personen(personen)
            logger.debug("save_account_balance: Gespeichert")
        else:
            logger.warning("save_account_balance: Konto nicht gefunden")

    def update_depot_details(self, selected_person, account, depot_details):
        logger.debug("update_depot_details: Aktualisiere DepotDetails")
        personen = self.load_personen()
        updated = False
        for i, person in enumerate(personen):
            if (person.get("Name") == selected_person.get("Name") and
                person.get("Nachname") == selected_person.get("Nachname")):
                for j, acct in enumerate(person.get("Konten", [])):
                    if (acct.get("BIC", "") == account.get("BIC") and
                        acct.get("Deponummer", "") == account.get("Deponummer")):
                        acct["DepotDetails"] = depot_details
                        updated = True
                        break
                break
        if updated:
            self.save_personen(personen)
            logger.debug("update_depot_details: Gespeichert")
        else:
            logger.warning("update_depot_details: Depot nicht gefunden")

    def load_bank_data(self):
        logger.debug("load_bank_data: Laden aus %s", self.banken_file)
        try:
            with open(self.banken_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.exception("load_bank_data: Fehler")
            return {}

    def load_kontotypen(self):
        logger.debug("load_kontotypen: Laden aus %s", self.kontotypen_file)
        try:
            with open(self.kontotypen_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.exception("load_kontotypen: Fehler")
            return {}

    def calculate_festgeld_for_date(self, konto: dict, date) -> float:
        if isinstance(date, datetime):
            dt = date.date()
        else:
            dt = date
        anlagedatum_str = konto.get("Anlagedatum", "")
        try:
            anlagedatum = datetime.strptime(anlagedatum_str, "%Y-%m-%d").date()
        except ValueError:
            try:
                anlagedatum = datetime.strptime(anlagedatum_str, "%d.%m.%Y").date()
            except Exception:
                anlagedatum = dt
        try:
            anlagebetrag = float(konto.get("Anlagebetrag", 0))
        except Exception:
            anlagebetrag = 0.0
        try:
            zinssatz = float(konto.get("Zinssatz", 0))
        except Exception:
            zinssatz = 0.0
        try:
            laufzeit = int(konto.get("Laufzeit_in_Tagen", 0))
        except Exception:
            laufzeit = 0
        end_date = anlagedatum + timedelta(days=laufzeit)
        if dt < anlagedatum:
            return anlagebetrag
        tage = (min(dt, end_date) - anlagedatum).days
        zinsen = anlagebetrag * (zinssatz / 100.0) * (tage / 360.0)
        return anlagebetrag + zinsen
