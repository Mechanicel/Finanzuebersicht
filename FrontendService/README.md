# FrontendService

Desktop-Frontend der Finanzübersicht.

## Persistenz
Produktive Persistenz läuft über MongoDB via `pymongo` (`src/data/mongo_repository.py`).
Bei leeren Collections werden Seed-Artefakte aus `FrontendService/seeds/*.json` einmalig eingespielt.

## Start
Aus dem Repository-Root:

```bash
uv sync --project FrontendService
uv run --project FrontendService frontendservice
```

## Konfiguration
Zentral über Root-`.env` (`shared_config.py`).
Wichtige Keys:
- `MONGO_URI`
- `MONGO_DB_NAME`
- `MONGO_PERSON_COLLECTION`
- `MONGO_BANK_COLLECTION`
- `MONGO_ACCOUNT_TYPE_COLLECTION`
- `MARKETDATA_BASE_URL`
