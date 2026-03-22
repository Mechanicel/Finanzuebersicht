# Finanzuebersicht – Python Setup

Dieses Repository enthält zwei Python-Teile:

- `FrontendService` (Desktop-UI)
- `markedataservice` (Flask-API)

Das Dependency-Management ist zentral in `pyproject.toml` definiert.

## Voraussetzungen

- Python **3.10** (unterstützt: `>=3.10,<3.13`)
- [`uv`](https://docs.astral.sh/uv/)

## Lokales Setup in `.venv`

```bash
# im Repo-Root ausführen
uv venv .venv
source .venv/bin/activate

# alle Runtime-Abhängigkeiten (Frontend + Marktdatenservice) installieren
uv sync --group frontend --group markedataservice
```

## Reproduzierbares Versionsmanagement (Lockfile)

Das Projekt verwendet `pyproject.toml` als Source of Truth.

```bash
# Lockfile aktualisieren
uv lock

# Danach reproduzierbar synchronisieren
uv sync --frozen --group frontend --group markedataservice
```

## Kompatibilitätsdatei `requirements.txt`

`requirements.txt` ist eine **abgeleitete Kompatibilitätsdatei** (z. B. für Tools, die noch `pip install -r` erwarten).

```bash
# aus dem Lockfile neu exportieren
uv export --frozen --no-emit-project --group frontend --group markedataservice -o requirements.txt
```

## Abhängigkeits-Updates

```bash
# Constraints in pyproject.toml anpassen, dann:
uv lock
uv sync --frozen --group frontend --group markedataservice
uv export --frozen --no-emit-project --group frontend --group markedataservice -o requirements.txt
```
