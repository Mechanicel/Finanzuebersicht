import json
from datetime import datetime, timedelta
import requests

class DataManager:
    """
    DataManager zum Laden, Speichern und Berechnen von Kontodaten.
    Nutzt freie Yahoo-Finance-REST-APIs ohne API-Key und unterstützt historische Kurse.
    """
    _isin_to_ticker_cache = {}
    _price_cache = {}

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
        print(f"[save_person_data] Person {updated_person.get('Name')} nicht gefunden.")

    def update_account(self, selected_person, account_type, account_data):
        personen = self.load_personen()
        for person in personen:
            if (person.get("Name") == selected_person.get("Name") and
                person.get("Nachname") == selected_person.get("Nachname")):
                account = {"Kontotyp": account_type}
                account.update(account_data)
                person.setdefault("Konten", []).append(account)
                self.save_personen(personen)
                return
        print(f"[update_account] Person {selected_person.get('Name')} nicht gefunden.")

    def duplicate_account(self, selected_person, account_type, account_data):
        for person in self.load_personen():
            if (person.get("Name") == selected_person.get("Name") and
                person.get("Nachname") == selected_person.get("Nachname")):
                for acct in person.get("Konten", []):
                    if (acct.get("Kontotyp") == account_type and
                        acct.get("Bank") == account_data.get("Bank") and
                        acct.get("Kontonummer", acct.get("Deponummer")) ==
                        account_data.get("Kontonummer", account_data.get("Deponummer"))):
                        return True
        return False

    def update_kontostaende(self, konto, datum_str, wert):
        existing = {}
        for entry in konto.get("Kontostaende", []):
            parts = entry.split(": ")
            if len(parts) == 2:
                existing[parts[0]] = parts[1]
        existing[datum_str] = f"{wert:.2f}"
        konto["Kontostaende"] = [f"{d}: {existing[d]}" for d in sorted(existing)]

    def save_account_balance(self, selected_person, account, balance, date_value):
        personen = self.load_personen()
        updated = False
        for i, person in enumerate(personen):
            if (person.get("Name") == selected_person.get("Name") and
                person.get("Nachname") == selected_person.get("Nachname")):
                for acct in person.get("Konten", []):
                    if (acct.get("BIC", "") == account.get("BIC", "") and
                        acct.get("Kontonummer", acct.get("Deponummer", "")) ==
                        account.get("Kontonummer", account.get("Deponummer", ""))):
                        self.update_kontostaende(
                            acct,
                            date_value.strftime("%Y-%m-%d"),
                            balance
                        )
                        updated = True
                        break
                personen[i] = person
                break
        if updated:
            self.save_personen(personen)
        else:
            print(f"[save_account_balance] Konto {account} nicht gefunden.")

    def update_depot_details(self, selected_person, account, depot_details):
        personen = self.load_personen()
        updated = False
        for i, person in enumerate(personen):
            if (person.get("Name") == selected_person.get("Name") and
                person.get("Nachname") == selected_person.get("Nachname")):
                for j, acct in enumerate(person.get("Konten", [])):
                    if (acct.get("BIC", "") == account.get("BIC", "") and
                        acct.get("Deponummer", "") == account.get("Deponummer", "")):
                        acct["DepotDetails"] = depot_details
                        updated = True
                        break
                personen[i] = person
                break
        if updated:
            self.save_personen(personen)
        else:
            print(f"[update_depot_details] Depot {account} nicht gefunden.")

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

    def get_ticker_by_isin(self, isin: str) -> str:
        if isin in self._isin_to_ticker_cache:
            return self._isin_to_ticker_cache[isin]
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={isin}"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            r = requests.get(url, headers=headers, timeout=5)
            r.raise_for_status()
            data = r.json()
            for q in data.get("quotes", []):
                if q.get("symbol"):
                    ticker = q["symbol"]
                    self._isin_to_ticker_cache[isin] = ticker
                    return ticker
        except Exception as e:
            print(f"[ERROR] get_ticker_by_isin für {isin}: {e}")
        self._isin_to_ticker_cache[isin] = None
        return None

    def get_price_by_isin(self, isin: str, date: datetime) -> float:
        """
        Holt den Schlusskurs für `date` via Yahoo Chart API.
        """
        ticker = self.get_ticker_by_isin(isin)
        if not ticker:
            return 0.0
        key = (ticker, date.strftime("%Y-%m-%d"))
        if key in self._price_cache:
            return self._price_cache[key]
        period1 = int(date.replace(hour=0, minute=0, second=0).timestamp())
        period2 = int((date + timedelta(days=1)).replace(hour=0, minute=0, second=0).timestamp())
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?period1={period1}&period2={period2}&interval=1d"
        )
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            r = requests.get(url, headers=headers, timeout=5)
            r.raise_for_status()
            data = r.json()
            result = data.get("chart", {}).get("result")
            if result:
                meta = result[0].get("meta", {})
                price = meta.get("chartPreviousClose") or meta.get("regularMarketPrice")
                if price is None:
                    inds = result[0].get("indicators", {}).get("quote", [])
                    if inds and inds[0].get("close"):
                        price = inds[0]["close"][-1]
                if price is not None:
                    price = float(price)
                    self._price_cache[key] = price
                    return price
        except Exception as e:
            print(f"[ERROR] get_price_by_isin fehlgeschlagen für {isin} am {date}: {e}")
        self._price_cache[key] = 0.0
        return 0.0

    def get_depot_value(self, depot_account: dict, date: datetime) -> float:
        total = 0.0
        for detail in depot_account.get("DepotDetails", []):
            try:
                menge = float(detail.get("Menge", 0))
            except:
                menge = 0.0
            price = self.get_price_by_isin(detail.get("ISIN", "").strip(), date)
            total += price * menge
        return total

    def calculate_festgeld_for_date(self, konto: dict, date: datetime) -> float:
        try:
            anlagebetrag = float(konto.get("Anlagebetrag", 0))
        except:
            anlagebetrag = 0.0
        try:
            zinssatz = float(konto.get("Zinssatz", 0))
        except:
            zinssatz = 0.0
        try:
            anlagedatum = datetime.strptime(konto.get("Anlagedatum", ""), "%Y-%m-%d").date()
        except:
            anlagedatum = date.date()
        try:
            laufzeit = int(konto.get("Laufzeit_in_Tagen", 0))
        except:
            laufzeit = 0
        end_date = anlagedatum + timedelta(days=laufzeit)
        if date.date() < anlagedatum:
            return anlagebetrag
        ende = min(date.date(), end_date)
        tage = (ende - anlagedatum).days
        zinsen = anlagebetrag * (zinssatz / 100.0) * (tage / 360.0)
        return anlagebetrag + zinsen