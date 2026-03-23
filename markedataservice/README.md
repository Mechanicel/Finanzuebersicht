# markedataservice

Eigenständiger Flask-Service für Kurs- und Unternehmensdaten.

## Start
Aus dem Repository-Root:

```bash
uv sync --project markedataservice
uv run --project markedataservice markedataservice
```

## Konfiguration
Der Service nutzt die zentrale Root-Konfiguration (`shared_config.py` / `.env`), insbesondere:
- `MARKETDATA_HOST`
- `MARKETDATA_PORT`
