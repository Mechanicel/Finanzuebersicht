# Finanzübersicht

## Projektüberblick
Dieses Repository ist als Monorepo organisiert, enthält aber **zwei unabhängig installierbare Python-Projekte**:

- **`FrontendService/`**: Desktop-UI (customtkinter)
- **`markedataservice/`**: Flask-API für Marktdaten

Zusätzlich gibt es im Root eine optionale **Orchestrierung** (`orchestrator.py`), die beide Prozesse gemeinsam startet, ohne dass sich die Pakete direkt gegenseitig importieren.

## Architektur nach Entkopplung
- `FrontendService` hat eine eigene Projektdefinition: `FrontendService/pyproject.toml`
- `markedataservice` hat eine eigene Projektdefinition: `markedataservice/pyproject.toml`
- Root-`pyproject.toml` enthält nur den optionalen Komfort-Start (`finanzuebersicht`)
- Keine direkte Python-Importkopplung zwischen den beiden Paketen

## Installation und Start

### 1) FrontendService separat
```bash
uv sync --project FrontendService
uv run --project FrontendService frontendservice
```

### 2) markedataservice separat
```bash
uv sync --project markedataservice
uv run --project markedataservice markedataservice
```

### 3) Optional: gemeinsamer Start (Root-Orchestrierung)
Der gemeinsame Start bleibt als Komfortfunktion erhalten, aber nur auf Root-Level:

```bash
uv run finanzuebersicht
```

Alternativ:
- macOS/Linux: `./start.sh`
- Windows: `start.bat`

## Logging
- Frontend schreibt nach `logs/frontend.log`
- Marktdatenservice schreibt nach `logs/markedataservice.log`
- Root-Orchestrator schreibt nach `logs/orchestrator.log`

Damit bleiben beide Komponenten getrennt beobachtbar.
