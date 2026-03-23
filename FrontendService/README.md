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
Zentral über Root-`.env` (`finanzuebersicht_shared`).
Wichtige Keys:
- `MONGO_URI` (optionaler Override)
- `MONGO_HOST`
- `MONGO_PORT`
- `MONGO_DB_NAME`
- `MONGO_USERNAME`
- `MONGO_PASSWORD`
- `MONGO_AUTH_SOURCE`
- `MONGO_PERSON_COLLECTION`
- `MONGO_BANK_COLLECTION`
- `MONGO_ACCOUNT_TYPE_COLLECTION`
- `MARKETDATA_BASE_URL`
