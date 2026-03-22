# markedataservice

## Zweck
`markedataservice` ist der eigenständige Flask-Service für Kurs- und Unternehmensdaten.

## Eigenständiges Projekt
- Projektdefinition: `markedataservice/pyproject.toml`
- Eigenes Script: `markedataservice`
- Eigene Dependencies:
  - `flask`
  - `yfinance`
  - `pandas`

## Start
Aus dem Repository-Root:

```bash
uv sync --project markedataservice
uv run --project markedataservice markedataservice
```

## Hinweise zur Kopplung
Der Service importiert **nicht** intern den `FrontendService`.

## Logging
Service-Logs werden nach `logs/markedataservice.log` geschrieben.
