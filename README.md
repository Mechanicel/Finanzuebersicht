# Finanzübersicht Monorepo (Vue + FastAPI + Microservices)

Dieses Repository enthält ausschließlich die Zielarchitektur mit **Vue-Frontend**, **FastAPI-API-Gateway** und fachlichen Microservices.

## Stack

- Frontend: **Vue 3 + TypeScript + Vite** (`frontend-web/`)
- API Edge/BFF: **api-gateway** (`services/api-gateway`)
- Backend Services (FastAPI):
  - `masterdata-service`
  - `person-service`
  - `account-service`
  - `portfolio-service`
  - `marketdata-service`
  - `analytics-service`
- Shared Python Package: `shared/`

## Repository-Struktur

- `frontend-web/` – Web-Frontend inkl. Router, API-Client, Views, Components
- `services/` – FastAPI-Microservices
- `docs/architecture/` – finale Architektur- und Betriebsdokumentation
- `scripts/dev.py` – zentraler Dev-Entrypoint (CLI)
- `.run/` – IntelliJ/PyCharm Run-Konfigurationen (einzeln + Compound)

## Lokaler Start

### 1) Setup

```bash
make setup
```

### 2) Full-Stack starten (zentral)

```bash
make dev
```

### 3) Einzelstarts

```bash
make dev-backend
make dev-frontend
uv run python scripts/dev.py run-service api-gateway
```

Weitere Details: `docs/architecture/local-development.md`.

## Hinweis für Windows/PowerShell

`scripts/dev.py` startet das Frontend auf Windows automatisch mit:

```powershell
cmd /c "npm install && npm run dev"
```

Auf macOS/Linux bleibt der Start:

```bash
bash -lc "npm install && npm run dev"
```
