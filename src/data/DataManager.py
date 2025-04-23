# src/data/DataManager.py

import json
import logging
from datetime import datetime, timedelta
import requests

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DataManager:
    """
    DataManager zum Laden, Speichern und Berechnen von Kontodaten.
    Nutzt Yahoo-Finance-REST-APIs ohne API-Key und unterstützt historische Kurse.
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
        logger.debug(f"DataManager initialized with files: {personen_file}, {banken_file}, {kontotypen_file}")

    def load_personen(self):
        logger.debug(f"load_personen: Loading from {self.personen_file}")
        try:
            with open(self.personen_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            personen = data.get("personen", [])
            logger.debug(f"load_personen: Loaded {len(personen)} persons")
            return personen
        except Exception as e:
            logger.exception(f"load_personen: Fehler beim Laden von {self.personen_file}")
            return []

    def save_personen(self, personen):
        logger.debug(f"save_personen: Saving {len(personen)} persons to {self.personen_file}")
        try:
            with open(self.personen_file, "w", encoding="utf-8") as f:
                json.dump({"personen": personen}, f, indent=4)
            logger.debug("save_personen: Save erfolgreich")
        except Exception as e:
            logger.exception(f"save_personen: Fehler beim Speichern von {self.personen_file}")

    def get_person_data(self, selected_person):
        logger.debug(f"get_person_data: Suche nach {selected_person}")
        for p in self.load_personen():
            if (p.get("Name") == selected_person.get("Name") and
                p.get("Nachname") == selected_person.get("Nachname")):
                logger.debug("get_person_data: Person gefunden")
                return p
        logger.debug("get_person_data: Person nicht gefunden")
        return None

    def save_person_data(self, updated_person):
        logger.debug(f"save_person_data: Speichere Daten für {updated_person}")
        personen = self.load_personen()
        for i, p in enumerate(personen):
            if (p.get("Name") == updated_person.get("Name") and
                p.get("Nachname") == updated_person.get("Nachname")):
                personen[i] = updated_person
                self.save_personen(personen)
                logger.debug("save_person_data: Aktualisierung erfolgreich")
                return
        logger.warning(f"save_person_data: Person {updated_person.get('Name')} nicht gefunden")

    def update_account(self, selected_person, account_type, account_data):
        logger.debug(f"update_account: Hinzufügen {account_type} für {selected_person}, Daten: {account_data}")
        personen = self.load_personen()
        for person in personen:
            if (person.get("Name") == selected_person.get("Name") and
                person.get("Nachname") == selected_person.get("Nachname")):
                account = {"Kontotyp": account_type}
                account.update(account_data)
                person.setdefault("Konten", []).append(account)
                self.save_personen(personen)
                logger.debug("update_account: Konto erfolgreich hinzugefügt")
                return
        logger.warning(f"update_account: Person {selected_person.get('Name')} nicht gefunden")

    def duplicate_account(self, selected_person, account_type, account_data):
        logger.debug(f"duplicate_account: Prüfe Duplikat für {selected_person}, Typ {account_type}")
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
        logger.debug(f"update_kontostaende: {konto.get('Kontotyp')} am {datum_str} = {wert:.2f}")
        existing = {}
        for entry in konto.get("Kontostaende", []):
            parts = entry.split(": ")
            if len(parts) == 2:
                existing[parts[0]] = parts[1]
        existing[datum_str] = f"{wert:.2f}"
        konto["Kontostaende"] = [f"{d}: {existing[d]}" for d in sorted(existing)]
        logger.debug("update_kontostaende: Kontostände aktualisiert")

    def save_account_balance(self, selected_person, account, balance, date_value):
        logger.debug(f"save_account_balance: Speichere Saldo {balance:.2f} für {account} am {date_value}")
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
            logger.debug("save_account_balance: Saldo gespeichert")
        else:
            logger.warning(f"save_account_balance: Konto {account} nicht gefunden")

    def update_depot_details(self, selected_person, account, depot_details):
        logger.debug(f"update_depot_details: Aktualisiere DepotDetails für {account}")
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
                        logger.debug("update_depot_details: Details aktualisiert")
                        break
                personen[i] = person
                break
        if updated:
            self.save_personen(personen)
        else:
            logger.warning(f"update_depot_details: Depot {account} nicht gefunden")

    def load_bank_data(self):
        logger.debug(f"load_bank_data: Laden von {self.banken_file}")
        try:
            with open(self.banken_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.debug("load_bank_data: Erfolgreich geladen")
            return data
        except Exception as e:
            logger.exception(f"load_bank_data: Fehler beim Laden von {self.banken_file}")
            return {}

    def load_kontotypen(self):
        logger.debug(f"load_kontotypen: Laden von {self.kontotypen_file}")
        try:
            with open(self.kontotypen_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.debug("load_kontotypen: Erfolgreich geladen")
            return data
        except Exception as e:
            logger.exception(f"load_kontotypen: Fehler beim Laden von {self.kontotypen_file}")
            return {}

    def get_ticker_by_isin(self, isin: str) -> str:
        logger.debug(f"get_ticker_by_isin: Suche Ticker für ISIN {isin}")
        if isin in self._isin_to_ticker_cache:
            logger.debug("get_ticker_by_isin: Cache-Hit")
            return self._isin_to_ticker_cache[isin]
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={isin}"
        try:
            logger.debug(f"get_ticker_by_isin: Anfrage an {url}")
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            r.raise_for_status()
            for q in r.json().get("quotes", []):
                if q.get("symbol"):
                    ticker = q["symbol"]
                    self._isin_to_ticker_cache[isin] = ticker
                    logger.debug(f"get_ticker_by_isin: Gefunden {ticker}")
                    return ticker
        except Exception as e:
            logger.exception(f"get_ticker_by_isin: Fehler für {isin}")
        self._isin_to_ticker_cache[isin] = None
        return None

    def get_price_by_isin(self, isin: str, date: datetime) -> float:
        logger.debug(f"get_price_by_isin: Abruf Preis für {isin} am {date}")
        ticker = self.get_ticker_by_isin(isin)
        if not ticker:
            return 0.0
        key = (ticker, date.strftime("%Y-%m-%d"))
        if key in self._price_cache:
            logger.debug("get_price_by_isin: Preis aus Cache")
            return self._price_cache[key]
        period1 = int(datetime.combine(date.date(), datetime.min.time()).timestamp())
        period2 = int(datetime.combine(date.date() + timedelta(days=1), datetime.min.time()).timestamp())
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?period1={period1}&period2={period2}&interval=1d"
        )
        try:
            logger.debug(f"get_price_by_isin: Anfrage an {url}")
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            r.raise_for_status()
            result = r.json().get("chart", {}).get("result")
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
                    logger.debug(f"get_price_by_isin: Preis {price:.2f}")
                    return price
        except Exception as e:
            logger.exception(f"get_price_by_isin: Fehlgeschlagen für {isin} am {date}")
        self._price_cache[key] = 0.0
        return 0.0

    def get_depot_value(self, depot_account: dict, date: datetime) -> float:
        logger.debug(f"get_depot_value: Berechne Depotwert für Konto {depot_account}")
        total = 0.0
        for detail in depot_account.get("DepotDetails", []):
            try:
                menge = float(detail.get("Menge", 0))
            except:
                menge = 0.0
            price = self.get_price_by_isin(detail.get("ISIN", "").strip(), date)
            total += price * menge
        logger.debug(f"get_depot_value: Gesamtwert {total:.2f}")
        return total

    def calculate_festgeld_for_date(self, konto: dict, date) -> float:
        """
        Berechnet den Festgeldwert am gegebenen Datum.
        Unterstützt Datumsformate 'YYYY-MM-DD' und 'DD.MM.YYYY'.
        """
        # Datum in date-Objekt
        if isinstance(date, datetime):
            dt = date.date()
        else:
            dt = date
        # Anlagedatum parsen
        anlagedatum_str = konto.get("Anlagedatum", "")
        try:
            anlagedatum = datetime.strptime(anlagedatum_str, "%Y-%m-%d").date()
        except ValueError:
            try:
                anlagedatum = datetime.strptime(anlagedatum_str, "%d.%m.%Y").date()
            except Exception:
                anlagedatum = dt
        # Laufzeit und Zinssatz
        try:
            anlagebetrag = float(konto.get("Anlagebetrag", 0))
        except:
            anlagebetrag = 0.0
        try:
            zinssatz = float(konto.get("Zinssatz", 0))
        except:
            zinssatz = 0.0
        try:
            laufzeit = int(konto.get("Laufzeit_in_Tagen", 0))
        except:
            laufzeit = 0
        end_date = anlagedatum + timedelta(days=laufzeit)
        # Wenn Stichtag vor Anlagedatum: ursprünglicher Betrag
        if dt < anlagedatum:
            return anlagebetrag
        # Berechne Zinsen bis Stichtag (oder bis Laufzeitende)
        ende = min(dt, end_date)
        tage = (ende - anlagedatum).days
        zinsen = anlagebetrag * (zinssatz / 100.0) * (tage / 360.0)
        wert = anlagebetrag + zinsen
        logger.debug(
            f"calculate_festgeld_for_date: Konto={konto.get('Kontotyp')} Anlagedatum={anlagedatum}, Stichtag={dt}, Wert={wert:.2f}")
        return wert
