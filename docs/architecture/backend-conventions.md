# Backend Conventions (verbindlich)

Diese Regeln gelten für **alle** Backend-Services im Monorepo.

## 1) Gemeinsames Shared-Paket

Alle Services nutzen `shared/src/finanzuebersicht_shared` für:

- Konfiguration und Umgebungsvariablen (`config.py`)
- App-Factory mit Standard-Endpunkten (`app.py`)
- Strukturierte Logs (`logging.py`)
- Gemeinsame Response-/Error-Modelle (`models.py`)
- Fehlerbehandlung (`errors.py`)
- Healthcheck-Helfer (`health.py`)
- Pydantic-Basismodelle (`base_models.py`)
- Datums-/Zeit-Helfer (`time_utils.py`)
- Request-/Correlation-ID Middleware (`request_context.py`)
- Test-Helfer (`testing.py`)

## 2) API-Konventionen

Jeder Service muss bereitstellen:

- `GET /health` – Liveness
- `GET /ready` – Readiness
- Versionierte API-Routen unter `/api/v1/...`

JSON-Antworten sind konsistent strukturiert:

- Erfolgsantworten über `ApiResponse[...]`
- Fehler über `ErrorResponse`
- Health-/Ready-Antworten über `HealthResponse`

## 3) Logging

- Logs sind strukturiert als JSON.
- Pflichtfelder: `timestamp`, `level`, `logger`, `message`
- Korrelation: `request_id` und `correlation_id` (wenn vorhanden)

## 4) Request IDs / Correlation IDs

- Middleware setzt automatisch:
  - `X-Request-ID`
  - `X-Correlation-ID`
- Werte werden in Request-State und Kontextvariablen abgelegt.
- Beide Header werden in Responses zurückgegeben.

## 5) Service-Struktur (Mindeststandard)

Jeder Service folgt dieser Struktur:

- `app/main.py` – App-Entrypoint
- `app/app_factory.py` – Aufbau der FastAPI-App
- `app/config.py` – Service-Settings
- `app/routers/api_v1.py` – versionierte API-Endpunkte
- `tests/test_conventions.py` – Standardtests

## 6) Test- und Qualitätsstandards

Repo-weit gelten:

- Ruff für Linting + Formatting
- Pytest als Test-Framework
- MyPy für Typprüfung
- Python 3.12+
- Pydantic v2

## 7) Kein Service-spezifisches Mini-Framework

Nicht erlaubt:

- Eigene konkurrierende Fehlerformate je Service
- Unterschiedliche Health-/Ready-Konventionen
- Unstrukturierte Logs in einzelnen Services
- Nicht-versionierte API-Basispfade

Alle neuen Backend-Features bauen auf den Shared-Bausteinen auf.
