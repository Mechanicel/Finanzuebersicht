# Finanzübersicht

## Projektüberblick
Monorepo mit zwei Services:

- **`FrontendService/`**: Desktop-UI (customtkinter)
- **`markedataservice/`**: Flask-API für Marktdaten

Zusätzlich gibt es im Root eine **Orchestrierung** (`orchestrator.py`), die MongoDB (Docker), markedataservice und Frontend gemeinsam startet.

## Konfiguration (zentral über `.env`)
Alle zentralen Werte liegen in `.env` und werden über `shared_config.py` geladen.

1. Beispiel konfigurieren:
   ```bash
   cp .env.example .env
   ```
2. Optional Werte anpassen (z. B. Ports, MongoDB-URI).

> Falls `.env` fehlt, erzeugt der Orchestrator sie automatisch aus `.env.example`.

## Lokaler Start (empfohlen)
```bash
uv sync
uv sync --project FrontendService
uv sync --project markedataservice
uv run finanzuebersicht
```

Was passiert dabei:
1. MongoDB Community wird über Docker Compose gestartet (`docker-compose.yml`).
2. Der `markedataservice` startet.
3. Das Frontend startet.
4. Frontend-Persistenz läuft über MongoDB (`pymongo`) mit Seed/Migration aus den bisherigen JSON-Dateien, falls die Collections leer sind.

## Einzelstart der Services
### Frontend
```bash
uv sync --project FrontendService
uv run --project FrontendService frontendservice
```

### markedataservice
```bash
uv sync --project markedataservice
uv run --project markedataservice markedataservice
```

## Datenhaltung
- **Neu:** MongoDB Collections für Personen, Banken, Kontotypen.
- **Alt:** JSON-Dateien bleiben als Seed-Quelle erhalten (`FrontendService/personen.json`, `FrontendService/src/data/*.json`).

## Logging
- Frontend: `logs/frontend.log`
- Marktdatenservice: `logs/markedataservice.log`
- Orchestrator: `logs/orchestrator.log`
