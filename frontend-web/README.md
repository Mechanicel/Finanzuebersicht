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

## Depot-/Holding-Flow (HoldingsView)

Die View nutzt über den Gateway folgende Endpunkte:

- `GET /app/persons/{person_id}/portfolios`
- `POST /app/persons/{person_id}/portfolios`
- `GET /app/portfolios/{portfolio_id}`
- `POST /app/portfolios/{portfolio_id}/holdings`
- `GET /app/marketdata/instruments/search`

Hinweis: Holdings speichern nur Kauf-/Bestandsdaten. Laufende Marktpreise werden nicht im Portfolio gespeichert, sondern bei Bedarf aus Marketdata geladen.
