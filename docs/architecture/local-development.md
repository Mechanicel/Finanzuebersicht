# Local Development

## Voraussetzungen

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+

## Zentrales CLI

Alle Dev-Kommandos laufen über `scripts/dev.py`.

```bash
uv run python scripts/dev.py --help
```

## Standard-Workflow

```bash
make setup
make dev
```

`make dev` startet:
- alle FastAPI-Services (inkl. Gateway)
- `frontend-web` via `npm install && npm run dev`

## Frontend/Backend-Integration (lokal)

- Das Vite-Frontend läuft lokal typischerweise auf `http://127.0.0.1:5173` (alternativ `http://localhost:5173`).
- Das Frontend spricht standardmäßig das API-Gateway unter `http://127.0.0.1:8000/api/v1` an (`frontend-web/src/api/http.ts`).
- Damit Browser-Requests zwischen Frontend-Origin und Gateway funktionieren, ist CORS zentral im Shared-App-Builder aktiviert.
- Standardmäßig erlaubte Origins:
  - `http://127.0.0.1:5173`
  - `http://localhost:5173`
- Überschreiben per Umgebungsvariable:

```bash
export CORS_ALLOW_ORIGINS="http://127.0.0.1:5173,http://localhost:5173,https://example.local"
```

- Die Service-Ports aus `scripts/dev.py` sind maßgeblich; insbesondere läuft der `person-service` lokal auf Port `8002`.

Dabei nutzt `scripts/dev.py` plattformspezifisch:
- **Windows/PowerShell**: `cmd /c "npm install && npm run dev"`
- **macOS/Linux**: `bash -lc "npm install && npm run dev"`


## Konfiguration per `.env`

Die Shared-`ServiceSettings` laden Konfiguration mit folgender Priorität:

1. **Prozess-Umgebungsvariablen** (z. B. `export APP_ENV=...`)
2. **Service-lokale `.env`** im aktuellen Working Directory
3. **Repo-Root `.env`**

Damit funktioniert sowohl der zentrale Start über `scripts/dev.py` (Service läuft mit `cwd=services/<name>`) als auch der direkte Start aus einem Service-Ordner.

## Alternativen

```bash
make dev-backend
make dev-frontend
uv run python scripts/dev.py run-service analytics-service
```

## IntelliJ/PyCharm

`.run/` enthält:
- Einzelkonfigurationen für alle Services
- `frontend-web`
- Compound `All Backend Services`
- Compound `Full Stack Dev`

Diese können direkt im Services-Fenster gestartet werden.


## MongoDB für person-service

Für den Personen-CRUD wird lokal eine laufende MongoDB-Instanz benötigt (Standard: `localhost:27017`).

Beispiel-Umgebungsvariablen:

```bash
export MONGO_DATABASE="finanzuebersicht"
export MONGO_PERSON_COLLECTION="persons"
export MONGO_ASSIGNMENT_COLLECTION="person_bank_assignments"
export MONGO_ALLOWANCE_COLLECTION="tax_allowances"
```

Alternativ kann `MONGO_URI` direkt gesetzt werden.

