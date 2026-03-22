# markedataservice

## Zweck des Verzeichnisses
`markedataservice` enthält den API-Teil der Finanzübersicht. Der Service liefert Kurs-, Historien- und Unternehmensdaten zu Wertpapieren (ISIN-basiert) und persistiert Ergebnisse in einem lokalen JSON-Cache.

## Zentrale Dateien, Komponenten und Teilbereiche
- `src/main.py`: Flask-App-Factory und lokaler Serverstart.
- `src/api/stock.py`: HTTP-Endpunkte (`/stock/<isin>`, `/price/<isin>`, `/company/<isin>`).
- `src/services/stock_service.py`: Service-Orchestrierung für Basis-, Historien- und ETF-Modus.
- `src/builders/stock_builder.py`: Aufbau/Anreicherung der Datenmodelle.
- `src/repositories/file_repository.py`: dateibasiertes Lesen/Schreiben des Caches.
- `src/utils/config.py`: Konfigurationswerte (u. a. `STOCK_DATA_DIR`).
- `src/models/`: Datenmodelle für Aktien-/ETF-Strukturen.
- `requirements.txt`: lokale Abhängigkeitsliste für diesen Teilbereich.

## Einbindung ins Gesamtsystem
- Dieser Service stellt Marktdaten als API bereit.
- Das Frontend greift für Depot-Berechnungen und Unternehmensinformationen auf diese Endpunkte zu.
- Der Service kann unabhängig vom Frontend gestartet werden, ist aber fachlich eng mit dessen Depotlogik verbunden.

## Erkennbare interne/externe Abhängigkeiten
**Intern:**
- `api -> services -> builders/repositories/models`

**Extern (laut Root-Dependency-Definition):**
- `Flask` (API)
- `yfinance` (Marktdatenquelle)
- `pandas` (Datenverarbeitung)

## Bekannte Besonderheiten, Risiken oder offene Punkte
- Caching erfolgt dateibasiert im konfigurierbaren Verzeichnis `STOCK_DATA_DIR` (Default unter `src/data/stocks`).
- Fehlerbehandlung in den Endpunkten ist vorhanden, aber es ist keine umfassende Betriebs-/Deployment-Dokumentation im Repository sichtbar.
- Es liegen keine explizit dokumentierten Last-/Skalierungsannahmen für den Service vor.

## Lokaler Start (sichtbarer Ist-Stand)
Aus dem Repository-Root:

```bash
python markedataservice/src/main.py
```
