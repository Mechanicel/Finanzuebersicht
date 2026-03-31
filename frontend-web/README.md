# frontend-web

Vue-3-Frontend (TypeScript + Vite) für Finanzübersicht.

## Start

```bash
npm install
npm run dev
```

Per Default spricht das Frontend mit `http://127.0.0.1:8000/api/v1`.

Optional:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1 npm run dev
```

## Personen-Hub: Kontenstruktur

Im Personen-Hub ist die Kontenverwaltung in zwei getrennte Schritte aufgeteilt:

- `Konto hinzufügen` (`/accounts/new?personId=...`)
- `Konten ansehen & bearbeiten` (`/accounts/manage?personId=...`)

Ein Depot wird im UI als Kontotyp innerhalb der Kontenverwaltung behandelt (kein separater Hauptbereich im Personen-Hub).

## Depot-/Holding-Flow in der Kontenverwaltung

Die Depot-Add/Edit-Flows nutzen über den Gateway folgende Endpunkte:

- `GET /app/persons/{person_id}/portfolios`
- `POST /app/persons/{person_id}/portfolios`
- `GET /app/portfolios/{portfolio_id}`
- `POST /app/portfolios/{portfolio_id}/holdings`
- `GET /app/marketdata/instruments/search`

Die Instrumentsuche läuft interaktiv beim Tippen (debounced, ohne separaten Such-Button) und unterstützt ein gemeinsames Suchfeld für Name, Symbol, ISIN und WKN.

Hinweis: Depot-Positionen laufen jetzt in einem separaten Screen (`/accounts/depot-holdings`) statt inline unter dem Kontoformular. Im Schritt „Konten ansehen & bearbeiten“ gibt es zusätzlich eine Suche über Label/Typ/IBAN/Kontonummer/Depotnummer sowie einen Lösch-Button mit Bestätigungsdialog. Holdings speichern nur Kauf-/Bestandsdaten (symbol, optionale IDs, quantity, acquisition_price, currency, buy_date, notes). Laufende Marktpreise und Instrumentsuche bleiben im marketdata-service.
