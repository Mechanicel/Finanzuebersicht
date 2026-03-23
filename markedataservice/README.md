# markedataservice

Eigenständiger Flask-Service für Kurs- und Unternehmensdaten.

## Persistenz
Der Service nutzt MongoDB als zentralen Cache (`src/repositories/mongo_repository.py`) und verwendet keine Datei-/JSON-Persistenz mehr.

## Start
Aus dem Repository-Root:

```bash
uv sync --project markedataservice
uv run --project markedataservice markedataservice
```

## Konfiguration
Der Service nutzt die zentrale Root-Konfiguration (`shared_config.py` / `.env`), insbesondere:
- `MONGO_URI`
- `MONGO_DB_NAME`
- `MONGO_MARKETDATA_COLLECTION`
- `MARKETDATA_HOST`
- `MARKETDATA_PORT`

## Smoke-Test
```bash
uv run --project markedataservice python tests/smoke_marketdata_mongo.py
```
