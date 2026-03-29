# Service Map

## Frontend

- **frontend-web** (Vue 3 + TypeScript + Vite)
  - Verantwortlich für Routing, UI-State, Form-Validierung, Visualisierung.
  - Primäre Backend-Kommunikation: `api-gateway`.

## API Gateway

- **api-gateway** (FastAPI)
  - BFF für das Frontend.
  - Aggregiert Daten aus Backend-Services (insbesondere Analytics) und stellt read-model-orientierte Endpunkte bereit.

## Fachservices

- **person-service**: Personen, Bankzuordnungen, Freibeträge.
- **masterdata-service**: Banken und Kontotypen.
- **account-service**: Konten-Fachdaten (Service-Skeleton vorhanden).
- **portfolio-service**: Depot/Holdings/Snapshots.
- **marketdata-service**: Marktdaten.
- **analytics-service**: KPIs, Zeitreihen, Allokation, Forecast-nahe Daten.

## Kommunikation

- Frontend → API Gateway (primär)
- Gateway → Fachservices (HTTP)
- Keine Desktop-UI, kein Tk-Stack, keine Legacy-UI-Pfade.
