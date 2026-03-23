# FrontendService

Desktop-Frontend der Finanzübersicht.

## Persistenz
Die Persistenz läuft über MongoDB via `pymongo` (Repository-Schicht in `src/data/mongo_repository.py`).
Bei leeren Collections werden vorhandene JSON-Dateien einmalig als Seed/Migration verwendet.

## Start
Aus dem Repository-Root:

```bash
uv sync --project FrontendService
uv run --project FrontendService frontendservice
```

## Konfiguration
Wird zentral über Root-`.env` (`shared_config.py`) geladen.
Wichtige Keys:
- `MONGO_URI`
- `MONGO_DB_NAME`
- `MARKETDATA_BASE_URL`
