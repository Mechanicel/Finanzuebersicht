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

## Lokale Entwicklung (Skeleton)

1. uv installieren
2. Gewünschten Service betreten, z. B. `services/api-gateway/`
3. Abhängigkeiten synchronisieren: `uv sync`
4. Service starten: `uv run uvicorn app.main:app --reload --port 8000`

Der aktuelle Stand ist ein struktureller Ausgangspunkt. Fachliche Implementierungen folgen in weiteren Schritten.
