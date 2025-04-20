import json
from datetime import datetime
import yfinance as yf

class DataManager:
    def __init__(self,
                 personen_file="data/personen.json",
                 banken_file="data/banken.json",
                 kontotypen_file="data/kontotypen.json"):
        self.personen_file = personen_file
        self.banken_file = banken_file
        self.kontotypen_file = kontotypen_file

    def load_personen(self):
        try:
            with open(self.personen_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("personen", [])
        except Exception as e:
            print(f"[load_personen] Fehler beim Laden von {self.personen_file}: {e}")
            return []

    def save_personen(self, personen):
        try:
            with open(self.personen_file, "w", encoding="utf-8") as f:
                json.dump({"personen": personen}, f, indent=4)
        except Exception as e:
            print(f"[save_personen] Fehler beim Speichern von {self.personen_file}: {e}")

    def get_person_data(self, selected_person):
        for p in self.load_personen():
            if (p.get("Name") == selected_person.get("Name") and
                p.get("Nachname") == selected_person.get("Nachname")):
                return p
        return None

    def save_person_data(self, updated_person):
        personen = self.load_personen()
        for i, p in enumerate(personen):
            if (p.get("Name") == updated_person.get("Name") and
                p.get("Nachname") == updated_person.get("Nachname")):
                personen[i] = updated_person
                self.save_personen(personen)
                return
        print("[save_person_data] Person nicht gefunden, keine Daten gespeichert.")

    def update_account(self, selected_person, account_type, account_data):
        personen = self.load_personen()
        for i, person in enumerate(personen):
            if (person.get("Name") == selected_person.get("Name")
                    and person.get("Nachname") == selected_person.get("Nachname")):
                if "Konten" not in person:
                    person["Konten"] = []
                new_account = {"Kontotyp": account_type}
                new_account.update(account_data)
                person["Konten"].append(new_account)
                self.save_personen(personen)
                return
        print("[update_account] Person nicht gefunden.")

    def duplicate_account(self, selected_person, account_type, account_data):
        for person in self.load_personen():
            if (person.get("Name") == selected_person.get("Name")
                    and person.get("Nachname") == selected_person.get("Nachname")):
                for acct in person.get("Konten", []):
                    if acct.get("Kontotyp") == account_type and acct.get("Bank") == account_data.get("Bank"):
                        key = "Kontonummer" if "Kontonummer" in account_data else "Deponummer"
                        if key in acct and key in account_data and acct[key] == account_data[key]:
                            return True
        return False

    def update_kontostaende(self, konto, datum_str, wert):
        if "Kontostaende" not in konto:
            konto["Kontostaende"] = []
        existing = {}
        for entry in konto["Kontostaende"]:
            parts = entry.split(": ")
            if len(parts) == 2:
                existing[parts[0]] = parts[1]
        existing[datum_str] = f"{wert:.2f}"
        konto["Kontostaende"] = [f"{d}: {existing[d]}" for d in sorted(existing)]

    def save_account_balance(self, selected_person, account, balance, date_value):
        personen = self.load_personen()
        updated = False
        for i, person in enumerate(personen):
            if (person.get("Name") == selected_person.get("Name")
                    and person.get("Nachname") == selected_person.get("Nachname")):
                for acct in person.get("Konten", []):
                    if (acct.get("BIC", "") == account.get("BIC", "")
                            and acct.get("Kontonummer", acct.get("Deponummer", ""))
                                == account.get("Kontonummer", account.get("Deponummer", ""))):
                        self.update_kontostaende(acct, date_value.strftime("%Y-%m-%d"), balance)
                        updated = True
                        break
                personen[i] = person
                break
        if updated:
            self.save_personen(personen)
        else:
            print("[save_account_balance] Kein passendes Konto gefunden.")

    def update_depot_details(self, selected_person, account, depot_details):
        personen = self.load_personen()
        updated = False
        for i, person in enumerate(personen):
            if (person.get("Name") == selected_person.get("Name")
                    and person.get("Nachname") == selected_person.get("Nachname")):
                for j, acct in enumerate(person.get("Konten", [])):
                    if (acct.get("BIC", "") == account.get("BIC", "")
                            and acct.get("Deponummer", "") == account.get("Deponummer", "")):
                        acct["DepotDetails"] = depot_details
                        updated = True
                        break
                personen[i] = person
                break
        if updated:
            self.save_personen(personen)
        else:
            print("[update_depot_details] Kein passendes Depot gefunden.")

    def load_bank_data(self):
        try:
            with open(self.banken_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[load_bank_data] Fehler beim Laden von {self.banken_file}: {e}")
            return {}

    def load_kontotypen(self):
        try:
            with open(self.kontotypen_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[load_kontotypen] Fehler beim Laden von {self.kontotypen_file}: {e}")
            return {}

    def get_company_name_by_isin(self, isin: str) -> str:
        """
        Fragt über yahooquery.search nach dem Unternehmen zur gegebenen ISIN.
        Liefert longname oder shortname, oder 'Unbekannt'.
        """
        print(f"[DEBUG] get_company_name_by_isin: Erstelle Ticker für ISIN '{isin}'")
        try:
            ticker = yf.Ticker(isin)
            info = ticker.info
            print(f"[DEBUG] get_company_name_by_isin: ticker.info keys: {list(info.keys())}")
            name = info.get("longName") or info.get("shortName")
            print(f"[DEBUG] get_company_name_by_isin: Gefundener Name für ISIN {isin}: {name}")
            return name or "Unbekannt"
        except Exception as e:
            print(f"[ERROR] get_company_name_by_isin fehlgeschlagen für {isin}: {e}")
            return "Unbekannt"

    def get_price_by_isin(self, isin: str) -> float:
        """
        Ermittelt mit yfinance das aktuelle Close oder regularMarketPrice.
        """
        print(f"[DEBUG] get_price_by_isin: Erstelle Ticker für ISIN '{isin}'")
        try:
            ticker = yf.Ticker(isin)
            info = ticker.info
            # Versuche regularMarketPrice, sonst previousClose
            price = info.get("regularMarketPrice") or info.get("previousClose")
            if price is not None:
                price = float(price)
                print(f"[DEBUG] get_price_by_isin: Preis aus info für '{isin}': {price}")
                return price
            # Fallback auf Tages-Chart
            hist = ticker.history(period="1d")
            if not hist.empty:
                close = float(hist["Close"].iloc[-1])
                print(f"[DEBUG] get_price_by_isin: Preis aus history für '{isin}': {close}")
                return close
            print(f"[WARN] get_price_by_isin: Keine Preisdaten für ISIN '{isin}' gefunden")
            return 0.0
        except Exception as e:
            print(f"[ERROR] get_price_by_isin fehlgeschlagen für {isin}: {e}")
            return 0.0

    def get_depot_value(self, depot_account: dict) -> float:
        """
        Summiert price_by_isin * Menge für alle DepotDetails.
        """
        total = 0.0
        for detail in depot_account.get("DepotDetails", []):
            isin = detail.get("ISIN", "").strip()
            try:
                menge = float(detail.get("Menge", 0))
            except Exception:
                menge = 0.0
            price = self.get_price_by_isin(isin)
            product = price * menge
            print(f"[DEBUG] get_depot_value: ISIN={isin}, Menge={menge}, Preis={price}, Produkt={product}")
            total += product
        print(f"[DEBUG] get_depot_value: Gesamtwert={total}")
        return total
