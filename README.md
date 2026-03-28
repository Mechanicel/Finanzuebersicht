# Finanzübersicht

## Projektüberblick
Monorepo mit zwei Services:

- **`FrontendService/`**: Desktop-UI (customtkinter) für Personen, Banken, Konten, Kontostände und Depotdaten.
- **`markedataservice/`**: Flask-API für Kurs- und Unternehmensdaten.

Zusätzlich orchestriert `orchestrator.py` den lokalen Start von MongoDB (Docker), markedataservice und Frontend.

## Persistenz & Konfiguration
- **Produktive Persistenz läuft vollständig über MongoDB.**
- JSON-Dateien werden nur noch als einmalige **Seed-/Migrationsartefakte** genutzt (bei leeren Collections).
- Alle Konfigurationen laufen zentral über Root-`.env` und `finanzuebersicht_shared`.

Wichtige MongoDB-Parameter:
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
- `MONGO_MARKETDATA_COLLECTION`

## MongoDB-Authentifizierung
- MongoDB wird lokal mit aktivierter Authentifizierung gestartet (Docker Compose).
- `MONGO_URI` bleibt als optionaler Override unterstützt.
- Ist `MONGO_URI` nicht gesetzt, wird die Verbindungs-URI zentral in `finanzuebersicht_shared` aus `MONGO_HOST`, `MONGO_PORT`, `MONGO_DB_NAME`, `MONGO_USERNAME`, `MONGO_PASSWORD` und `MONGO_AUTH_SOURCE` aufgebaut.

## Lokales Setup (Neu-Developer-Flow)
1. Env-Datei anlegen:
   ```bash
   cp .env.example .env
   ```
2. MongoDB via Docker starten:
   ```bash
   docker compose up -d mongodb
   ```
3. Dependencies installieren:
   ```bash
   uv sync
   uv sync --project FrontendService
   uv sync --project markedataservice
   ```
4. Gesamtsystem starten:
   ```bash
   uv run finanzuebersicht
   ```

Alternativ per Script:
```bash
./start.sh
```

## Einzelstart der Services
### Frontend
```bash
uv run --project FrontendService frontendservice
```

### markedataservice
```bash
uv run --project markedataservice markedataservice
```

## Seed-Artefakte (nur Migration)
- `FrontendService/seeds/personen.json`
- `FrontendService/seeds/banken.json`
- `FrontendService/seeds/kontotypen.json`

Diese Dateien sind keine produktive Laufzeit-Persistenz.

## Logging
- Frontend: `logs/frontend.log`
- Marktdatenservice: `logs/markedataservice.log`
- Orchestrator: `logs/orchestrator.log`

## Smoke-Test (MongoDB)
Minimaler Persistenztest für Markt-Cache-Collection:
```bash
uv run --project markedataservice python tests/smoke_marketdata_mongo.py
```

## PyCharm Run-Konfigurationen (versioniert)
Im Repo sind projektweite Run-Konfigurationen unter `.run/` abgelegt.
Sie erscheinen in PyCharm als teilbare Konfigurationen und können im **Services**-Tab ausgeführt werden.

- `FrontendService`: `uv run --project FrontendService frontendservice`
- `markedataservice`: `uv run --project markedataservice markedataservice`
- `Orchestrator`: `uv run python orchestrator.py`
- `All Services`: Compound-Start von `FrontendService` + `markedataservice` (ohne `Orchestrator`, damit keine Doppelstarts entstehen)
