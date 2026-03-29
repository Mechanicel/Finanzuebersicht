# API-Gateway / BFF Rolle

## Verantwortung

Das `api-gateway` stellt eine **frontend-zentrierte API** für das Vue-Web-Frontend bereit.
Es kapselt interne Servicegrenzen und bündelt Daten aus Domänenservices in seitenfähige Antworten.

## Prinzipien

1. **Vue spricht primär mit dem Gateway**, nicht mit allen Services direkt.
2. **BFF statt Dumpingplatz**: nur UI-Use-Cases, keine unkontrollierte 1:1-Spiegelung aller Service-APIs.
3. **Konsistente Responses** über `ApiResponse[...]`.
4. **Abhängigkeits-Healthchecks** werden über das Gateway sichtbar.

## Gateway-Endpunkte für Vue-Seiten

- `GET /api/v1/app/persons`
  - Datenquelle für Personenlisten-/Selektor-Seiten.
- `GET /api/v1/app/persons/{person_id}/dashboard`
  - Aggregiert Analytics-Readmodels (`overview`, `allocation`, `metrics`, `timeseries`) für die Dashboard-Seite.
- `GET /api/v1/app/persons/{person_id}/accounts`
  - Kontenliste für Konto-Übersichtskomponenten.
- `GET /api/v1/app/persons/{person_id}/portfolios`
  - Portfolio-Liste für Portfolio-Seiten.
- `GET /api/v1/app/persons/{person_id}/analytics/overview`
  - Direkter Zugriff auf das wichtigste Analytics-Widget.
- `GET /api/v1/app/persons/{person_id}/health`
  - Technischer Status abhängiger Services.

## Analytics-Responses für Vue-Charts

Der `analytics-service` liefert Readmodels mit chartfreundlicher Form:

- `labels`
- `series` / `slices`
- `summary` / `summaries`
- `kpis`
- `meta` (`loading`, `error`)

Diese Strukturen können direkt an Vue-Chart-Komponenten (Line, Bar, Pie, Heatmap, KPI-Cards) gebunden werden.
