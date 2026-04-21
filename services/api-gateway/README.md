
# api-gateway (BFF)

Das Gateway ist der zentrale Einstiegspunkt für das Frontend.

## Portfolio-/Holding-Endpoints für Depot-Erfassung

- `GET /api/v1/app/persons/{person_id}/portfolios`
- `POST /api/v1/app/persons/{person_id}/portfolios`
- `GET /api/v1/app/portfolios/{portfolio_id}`
- `POST /api/v1/app/portfolios/{portfolio_id}/holdings`
- `PATCH /api/v1/app/portfolios/{portfolio_id}/holdings/{holding_id}`
- `DELETE /api/v1/app/portfolios/{portfolio_id}/holdings/{holding_id}`

Die Endpunkte leiten als Proxy/BFF an den `portfolio-service` weiter (kein Stub, keine Bewertungslogik).

## Marketdata im Depot-Flow

Instrumentensuche und letzte Kurse kommen weiterhin aus:

- `GET /api/v1/app/marketdata/instruments/search`
- `GET /api/v1/app/marketdata/instruments/{symbol}/profile`

Das Gateway übernimmt hier nur Weiterleitung und Fehlerabbildung.

Der alte Endpoint `GET /api/v1/app/marketdata/instruments/{symbol}/selection` bleibt
vorübergehend als deprecated Alias auf `.../profile` verfügbar.

## Lokale Konfiguration

- `PORTFOLIO_SERVICE_URL` (Default: `http://localhost:8004`)
- `MARKETDATA_SERVICE_URL` (Default: `http://localhost:8005`)
- `REQUEST_TIMEOUT_SECONDS`
