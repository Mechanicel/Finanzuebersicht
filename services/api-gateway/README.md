# api-gateway (BFF)

Das Gateway ist der **einheitliche Einstiegspunkt** für das Vue-Frontend.

## Ziel

- Frontend spricht primär mit dem Gateway
- Gateway kapselt Servicegrenzen und Aggregation
- Frontend erhält stabile, seitenorientierte API-Verträge

## API (Vue-seitenorientiert)

- `GET /api/v1/app/persons`
- `GET /api/v1/app/persons/{person_id}/dashboard`
- `GET /api/v1/app/persons/{person_id}/accounts`
- `GET /api/v1/app/persons/{person_id}/portfolios`
- `GET /api/v1/app/persons/{person_id}/analytics/overview`
- `GET /api/v1/app/persons/{person_id}/health`

## BFF-Regel

Das Gateway implementiert nur Frontend-Use-Cases und wird nicht als generischer Daten-Dump verwendet.
