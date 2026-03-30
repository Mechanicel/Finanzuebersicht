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

Dabei nutzt `scripts/dev.py` plattformspezifisch:
- **Windows/PowerShell**: `cmd /c "npm install && npm run dev"`
- **macOS/Linux**: `bash -lc "npm install && npm run dev"`

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
