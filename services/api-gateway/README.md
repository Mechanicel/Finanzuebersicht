# api-gateway (BFF)

Das Gateway ist der **einheitliche Einstiegspunkt** für das Vue-Frontend.

## Ziel

- Frontend spricht primär mit dem Gateway
- Gateway kapselt Servicegrenzen und Aggregation
- Frontend erhält stabile, seitenorientierte API-Verträge

## API (Vue-seitenorientiert)

- `GET /api/v1/app/persons`
- `POST /api/v1/app/persons`
- `GET /api/v1/app/persons/{person_id}`
- `PATCH /api/v1/app/persons/{person_id}`
- `DELETE /api/v1/app/persons/{person_id}`
- `GET /api/v1/app/banks`
- `POST /api/v1/app/banks`
- `GET /api/v1/app/persons/{person_id}/dashboard`
- `GET /api/v1/app/persons/{person_id}/accounts`
- `GET /api/v1/app/persons/{person_id}/portfolios`
- `GET /api/v1/app/persons/{person_id}/analytics/overview`
- `GET /api/v1/app/persons/{person_id}/health`
- `GET /api/v1/app/marketdata/instruments/search?q=...&limit=...`
- `GET /api/v1/app/marketdata/instruments/{symbol}/summary`
- `GET /api/v1/app/marketdata/instruments/{symbol}/blocks`
- `GET /api/v1/app/marketdata/instruments/{symbol}/prices?range=...&interval=...`
- `GET /api/v1/app/marketdata/instruments/{symbol}/full`

## Lokale Konfiguration

- `MARKETDATA_SERVICE_URL` (Default: `http://localhost:8005`)
- `REQUEST_TIMEOUT_SECONDS` gilt unverändert für alle Downstream-Requests inkl. Marketdata-Proxy.

## BFF-Regel

Das Gateway implementiert nur Frontend-Use-Cases und wird nicht als generischer Daten-Dump verwendet.
Für Marketdata-Endpunkte bedeutet das in diesem Schritt: reine Proxy-Weiterleitung ohne Aggregation oder Provider-Fachlogik.
