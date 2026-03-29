# Development Setup

Diese Dokumentation beschreibt die **verbindliche** lokale Startlogik für das Monorepo.

## Voraussetzungen

- Python 3.12+
- `uv`
- optional für das Frontend: `node` + `npm`

## Einheitlicher Portplan

| Service              | Port |
|----------------------|------|
| api-gateway          | 8000 |
| masterdata-service   | 8001 |
| person-service       | 8002 |
| account-service      | 8003 |
| portfolio-service    | 8004 |
| marketdata-service   | 8005 |
| analytics-service    | 8006 |
| frontend-web (üblich)| 5173 |

## Zentraler CLI-Startweg

Der zentrale Einstieg ist `scripts/dev.py`.

### Standardbefehle

```bash
make setup
make lint
make format
make test
make dev
make dev-backend
make dev-frontend
```

Äquivalent direkt via Python:

```bash
uv run python scripts/dev.py <command>
```

Unterstützte Commands:

- `setup`: `uv sync --all-packages --dev`
- `lint`: `ruff check .`
- `format`: `ruff format .` + `ruff check . --fix`
- `test`: `pytest`
- `dev`: startet alle Backend-Services und das Frontend (falls `frontend-web/package.json` vorhanden ist)
- `dev-backend`: startet alle Backend-Services
- `dev-frontend`: startet nur Frontend (`npm install && npm run dev`) oder `FRONTEND_DEV_CMD`
- `run-service <service>`: startet exakt einen Backend-Service

## Services einzeln starten

Einzelstart via zentralem Skript:

```bash
uv run python scripts/dev.py run-service api-gateway
uv run python scripts/dev.py run-service masterdata-service
uv run python scripts/dev.py run-service person-service
uv run python scripts/dev.py run-service account-service
uv run python scripts/dev.py run-service portfolio-service
uv run python scripts/dev.py run-service marketdata-service
uv run python scripts/dev.py run-service analytics-service
```

Jeder Python-Service besitzt zusätzlich einen direkten Entrypoint:

```bash
cd services/<service-name>
PORT=800x uv run python -m app
```

## IntelliJ / PyCharm Services-Fenster

Versionierte Run-Konfigurationen liegen in `.run/`:

- `api-gateway.run.xml`
- `masterdata-service.run.xml`
- `person-service.run.xml`
- `account-service.run.xml`
- `portfolio-service.run.xml`
- `marketdata-service.run.xml`
- `analytics-service.run.xml`
- `frontend-web.run.xml`
- `All Backend Services.run.xml` (Compound)
- `Full Stack Dev.run.xml` (Compound)

Empfehlung im Services-Fenster:

1. Für Backend-only: **All Backend Services** starten.
2. Für Full Stack: **Full Stack Dev** starten.

## Keine Legacy-Startlogik

Nicht mehr verwenden (entfernt):

- alte Orchestrator-/Shell-Startskripte
- alte Legacy-Run-Konfigurationen
- Legacy-Docker-Compose (falls vorhanden)

Es gilt ausschließlich die oben dokumentierte Startlogik über `scripts/dev.py`, `make` und `.run/`.
