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

Hinweis: Im Schritt „Konten ansehen & bearbeiten“ ist die gesamte Kontenzeile klickbar und öffnet einen dedizierten Konto-Detailscreen (`/accounts/manage/:accountId?personId=...`) mit klarem Zurück-Button zur Kontenliste. Depot-Holdings werden dort im Depot-Kontext gepflegt (kein separates Depot-Auswahlfeld in der Holding-Maske). Nach Instrumentwahl aus Market-Data werden alle verfügbaren Felder (u. a. symbol, company_name, display_name, isin, wkn, currency, exchange, quote_type, asset_type, last_price→acquisition_price) automatisch ins Formular vorbelegt. Holdings speichern weiterhin nur Kauf-/Bestandsdaten; laufende Marktpreise bleiben im marketdata-service.
