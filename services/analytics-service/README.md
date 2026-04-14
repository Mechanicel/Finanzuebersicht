# analytics-service

Der `analytics-service` liefert **Read-Models** für Dashboard- und Chart-Use-Cases.

## API (für Gateway und Vue-Dashboards)

- `GET /api/v1/analytics/persons/{person_id}/overview`
- `GET /api/v1/analytics/persons/{person_id}/allocation`
- `GET /api/v1/analytics/persons/{person_id}/timeseries`
- `GET /api/v1/analytics/persons/{person_id}/monthly-comparison`
- `GET /api/v1/analytics/persons/{person_id}/metrics`
- `GET /api/v1/analytics/persons/{person_id}/heatmap`
- `GET /api/v1/analytics/persons/{person_id}/forecast`

## Response-Design (chartfreundlich)

Alle Endpunkte liefern strukturierte Daten mit:

- `labels` für Achsen/Legenden
- `series` oder `slices` mit serialisierten Datenpunkten
- `summary` / `summaries`
- `kpis`
- `meta.loading` und `meta.error` für UI-States

Die Responses sind direkt für Vue-Chart-Komponenten konsumierbar.
