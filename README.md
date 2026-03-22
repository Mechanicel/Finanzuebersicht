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
source .venv/bin/activate
uv sync --group frontend --group markedataservice
```

Optional für pip-basierte Workflows:

```bash
pip install -r requirements.txt
```

## Startanleitung
> Hinweis: Die folgenden Befehle bilden den im Code sichtbaren Startpunkt ab. Zusätzliche Laufzeitvoraussetzungen (z. B. Umgebungsvariablen) sind nur dort dokumentiert, wo sie im Repository explizit erkennbar sind.

### Marktdatenservice starten
```bash
python markedataservice/src/main.py
```

### Frontend starten
```bash
python -m FrontendService.src.main
```

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
