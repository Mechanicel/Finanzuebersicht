# Finanzübersicht — Claude Code Context (Branch: Microservice_umbau)

## Projekt auf einen Blick
Web-basiertes Finanz-Monorepo. Vollständige Zielarchitektur mit Vue-Frontend, FastAPI-API-Gateway und fachlichen Microservices.
Paketmanager: **uv** (Python), **npm** (Frontend). Persistenz: **MongoDB** (Docker, nur person-service zwingend).

## Repo-Struktur

```
Finanzuebersicht/
├── frontend-web/           # Vue 3 + TypeScript + Vite
│   └── src/
│       ├── app/            # App.vue, main.ts, router/
│       ├── modules/        # Feature-Module (je Modul: api/, components/, pages/, model/, __tests__/)
│       │   ├── accounts/
│       │   ├── allowances/
│       │   ├── banks/
│       │   ├── dashboard/  # Portfolio-Dashboard, Depot-Analyse, Instrument-Analyse
│       │   └── persons/
│       └── shared/         # Wiederverwendbare UI-Komponenten, Composables
├── services/               # FastAPI-Microservices (je Service: app/, tests/)
│   ├── api-gateway/        # BFF/Edge — Port 8000, proxyt alle Requests
│   ├── masterdata-service/ # Port 8001 — Stammdaten
│   ├── person-service/     # Port 8002 — Personen, Banken, Steuer-Allowances (MongoDB zwingend)
│   ├── account-service/    # Port 8003 — Konten
│   ├── portfolio-service/  # Port 8004 — Portfolio, Holdings
│   ├── marketdata-service/ # Port 8005 — Kurse, ETF/Stock-Daten (FMP + yfinance, Mongo optional)
│   └── analytics-service/  # Port 8006 — Berechnungen, Dashboard-Aggregation
├── shared/                 # finanzuebersicht-shared Python-Paket
│   └── src/finanzuebersicht_shared/
│       ├── config.py       # ServiceSettings (pydantic-settings), get_settings()
│       ├── app.py          # FastAPI-App-Factory-Utilities
│       ├── base_models.py  # Pydantic-Basismodelle
│       ├── errors.py       # Fehlerbehandlung
│       ├── health.py       # Health-Check-Endpoint
│       ├── logging.py      # Logging-Setup
│       ├── models.py       # Shared Pydantic-Modelle
│       ├── request_context.py  # Request-ID / Correlation-ID Middleware
│       ├── testing.py      # Test-Utilities
│       └── time_utils.py
├── docs/architecture/      # Architektur-Dokumentation
├── scripts/dev.py          # Zentraler Dev-Entrypoint (CLI)
├── Makefile                # Shortcuts für setup/lint/test/dev
├── pyproject.toml          # uv workspace root (Python ≥3.12, ruff, mypy, pytest)
└── .env.example            # Alle Umgebungsvariablen mit Defaults
```

## Tech-Stack
- **Python 3.12**, uv als Paketmanager
- **FastAPI + pydantic-settings** — alle Backend-Services
- **Vue 3 + TypeScript + Vite** — Web-Frontend (Port 5173)
- **MongoDB 7** via Docker — person-service zwingend, marketdata-service optional
- **FMP (Financial Modeling Prep)** + **yfinance** — Marktdaten-Provider
- **pytest + mongomock** — Backend-Tests
- **ruff** — Linter/Formatter, **mypy** — Type-Checking

## Service-Ports (lokal)
| Service | Port |
|---|---|
| Frontend (Vite) | 5173 |
| api-gateway | 8000 |
| masterdata-service | 8001 |
| person-service | 8002 |
| account-service | 8003 |
| portfolio-service | 8004 |
| marketdata-service | 8005 |
| analytics-service | 8006 |

Frontend kommuniziert ausschließlich mit `api-gateway` (`http://127.0.0.1:8000/api/v1`).

## Konfiguration & Umgebung
- Alle Settings über Root-`.env` (Vorlage: `.env.example`)
- Jeder Service erbt von `ServiceSettings` (pydantic-settings) aus `finanzuebersicht_shared`
- Kein direktes `os.getenv()` — immer über `get_settings()` und Settings-Klasse
- MongoDB-URI optional über `MONGO_URI`, sonst aus `MONGO_HOST`/`MONGO_PORT`/etc. gebaut
- FMP-API-Key: `FMP_API_KEY` in `.env` (für marketdata-service)

## Konventionen
- Jeder Service hat dieselbe interne Struktur: `app/` mit `main.py`, `app_factory.py`, `config.py`, `dependencies.py`, `models.py`, `routers/`, optional `service.py` und `repositories.py`
- Shared-Logik gehört immer in `shared/src/finanzuebersicht_shared/`
- Request-IDs (`X-Request-ID`) und Correlation-IDs werden automatisch gesetzt (Middleware in shared)
- CORS-Origins über `CORS_ALLOW_ORIGINS` (CSV in `.env`)
- Type Hints überall, mypy-kompatibel

## Lokaler Start
```bash
# Setup (einmalig)
make setup

# Alles starten (Backend + Frontend)
make dev

# Nur Backend
make dev-backend

# Nur Frontend
make dev-frontend

# Einzelner Service
uv run python scripts/dev.py run-service api-gateway
```

## Tests
```bash
make test
# oder direkt:
uv run pytest services/
```

## Häufige Aufgaben
- **Neues Frontend-Modul** → `frontend-web/src/modules/<name>/` mit `api/`, `pages/`, `components/`, `model/`, `__tests__/`
- **Neuen API-Endpoint** → Router in `services/<service>/app/routers/api_v1.py`, Proxy-Route im `api-gateway`
- **Neue Config-Variable** → `.env.example` + Settings-Klasse des jeweiligen Services
- **Neues Shared-Utility** → `shared/src/finanzuebersicht_shared/`
- **Neuer Marktdaten-Provider** → `services/marketdata-service/app/clients/`
