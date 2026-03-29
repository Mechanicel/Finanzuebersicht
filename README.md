# Finanzuebersicht Monorepo

Dieses Repository ist ein **Greenfield-Monorepo** für eine webbasierte Finanzübersicht.

## Zielarchitektur

- `frontend-web/` – zukünftiges Web-Frontend (nur UI)
- `services/api-gateway/` – BFF/Gateway für das Frontend
- `services/masterdata-service/` – Banken, Kontotypen, Referenzdaten
- `services/person-service/` – Personen, Bankzuordnungen, Freibeträge
- `services/account-service/` – Konten, manuelle Snapshots
- `services/portfolio-service/` – Depotkonten und Holdings
- `services/marketdata-service/` – Wertpapier- und Marktdaten
- `services/analytics-service/` – Aggregationen, Charts, Forecasts, Readmodels
- `shared/` – gemeinsame Pydantic-Modelle und Utilities
- `scripts/` – Entwicklungs- und Startskripte
- `.run/` – IntelliJ/PyCharm Run-Konfigurationen
- `docs/architecture/` – Architektur- und API-Dokumentation

## Technologie-Stack

- Python **>= 3.12**
- FastAPI als Basis aller Python-Services
- uv als bevorzugtes Python-Tooling

## Lokale Entwicklung

Die komplette Entwicklungs- und Startlogik ist in `scripts/dev.py` zentralisiert.

1. Setup: `make setup`
2. Alle Backends starten: `make dev-backend`
3. Full-Stack-Entwicklung (Backend + Frontend): `make dev`

Alle Details inkl. Portplan, IntelliJ-Run-Konfigurationen und Einzelstarts stehen in:

- `docs/architecture/development.md`
