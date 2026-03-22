# Finanzübersicht

## Projektüberblick
Dieses Repository enthält eine Python-basierte Finanzübersicht als Monorepo mit zwei Hauptbereichen:

- **`FrontendService`**: Desktop-Oberfläche auf Basis von `customtkinter` zur Pflege und Anzeige von Personen-, Konto- und Depotdaten.
- **`markedataservice`**: Flask-basierter Service für Kurs- und Unternehmensdaten (u. a. per ISIN), inklusive lokalem JSON-Caching.

Das zentrale Dependency-Management erfolgt im Repository-Root über `pyproject.toml` und `uv`.

## Ziel der Anwendung
Ziel ist es, Finanzdaten von Personen/Konten strukturiert zu erfassen und auszuwerten. Das Frontend verarbeitet lokale Stammdaten und ruft für Wertpapierdaten den Marktdatenservice auf.

## Wichtigste Hauptfunktionen (aus dem Ist-Zustand ableitbar)
- Verwaltung von Personen und Konten in der Desktop-Anwendung.
- Navigation über mehrere UI-Screens (z. B. Auswahl, Anlage, Übersicht, Bearbeitung).
- Berechnung und Aktualisierung von Depot- und Festgeldwerten im Frontend-Controller.
- Bereitstellung von API-Endpunkten für:
  - historische/ETF-bezogene Bestandsdaten (`/stock/<isin>`)
  - Preisabfragen (`/price/<isin>?date=YYYY-MM-DD`)
  - Unternehmensnamen (`/company/<isin>`)
- Dateibasiertes Caching von Marktdaten im `markedataservice`.

## Tech-Stack
- **Sprache:** Python 3.10+
- **UI:** `customtkinter`, `matplotlib`, `numpy`, `tkcalendar`
- **Backend/API:** `Flask`
- **Marktdaten:** `yfinance`, `pandas`
- **Umgebung/Dependencies:** `uv`, optional `pip` über exportierte `requirements.txt`

## Voraussetzungen
- Python `>=3.10,<3.13`
- `uv` (empfohlen)

## Installation
Aus dem Repository-Root:

```bash
uv venv .venv
uv sync
```

## One-Click-Start (empfohlen)
Es gibt genau einen zentralen Startweg für die Anwendung (GUI):

```bash
uv run finanzuebersicht
```

Der Befehl nutzt den zentralen Entry-Point aus `pyproject.toml` (`[project.gui-scripts]`) und startet intern den Launcher `FrontendService.src.launcher:main`.

### Optionale Komfort-Launcher (Root)
- macOS/Linux: `./start.sh`
- Windows: `start.bat`

Beide Dateien sind dünne Wrapper um denselben zentralen Python-Entry-Point.

### Typische Fehlerfälle
- **`.venv` fehlt**: führe `uv venv .venv && uv sync` aus.
- **Abhängigkeit fehlt** (`ModuleNotFoundError`): führe `uv sync` erneut aus.
- **Konfigurationsdateien fehlen**: prüfe, ob `FrontendService/personen.json` sowie die JSON-Dateien unter `FrontendService/src/data/` vorhanden sind.

## High-Level-Struktur des Repositories

```text
.
├── FrontendService/        # Desktop-UI und lokale Datenhaltung
├── markedataservice/       # Flask-API und Marktdatenlogik
├── pyproject.toml          # zentrale Projekt- und Dependency-Definition
├── requirements.txt        # abgeleitete Kompatibilitätsdatei für pip
└── README.md               # diese Übersicht
```

## Relevante Verzeichnisse auf erster Ebene
- [`FrontendService/`](FrontendService/README.md) – Desktop-Anwendung, Screen-Navigation, lokale Datenstrukturen.
- [`markedataservice/`](markedataservice/README.md) – API-Endpunkte, Datenbeschaffung, Caching.

## Verweise auf README-Dateien der ersten Ebene
- [`FrontendService/README.md`](FrontendService/README.md)
- [`markedataservice/README.md`](markedataservice/README.md)

## Bekannte Einschränkungen / offene Punkte (transparent)
- Die vorhandene Quellstruktur enthält Hinweise auf teilweise inkonsistente oder unvollständige Modulpfade/Signaturen; diese wurden in diesem Dokumentationsschritt **nicht** korrigiert.
- Für produktive Deployments (z. B. WSGI-Setup, Service-Orchestrierung, Monitoring) sind im aktuellen Repository keine belastbaren Vorgaben dokumentiert.
- Automatisierte Testsuites oder verbindliche Qualitätspipelines sind auf Root-Ebene nicht erkennbar dokumentiert.
