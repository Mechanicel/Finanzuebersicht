# FrontendService

## Zweck
`FrontendService` ist die eigenständige Desktop-Anwendung der Finanzübersicht.

## Eigenständiges Projekt
- Projektdefinition: `FrontendService/pyproject.toml`
- Eigenes Script: `frontendservice`
- Eigene Dependencies (UI/Visualisierung/HTTP):
  - `customtkinter`
  - `matplotlib`
  - `numpy`
  - `python-dotenv`
  - `requests`
  - `tkcalendar`

## Start
Aus dem Repository-Root:

```bash
uv sync --project FrontendService
uv run --project FrontendService frontendservice
```

## Hinweise zur Kopplung
Das Frontend importiert **nicht** intern den `markedataservice`.
Die Kommunikation erfolgt ausschließlich über externe Schnittstellen (HTTP-API).

## Logging
Frontend-Logs werden nach `logs/frontend.log` geschrieben.
