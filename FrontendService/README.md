# FrontendService

## Zweck des Verzeichnisses
`FrontendService` enthält die Desktop-Anwendung der Finanzübersicht. Dieser Bereich stellt die Benutzeroberfläche bereit, verwaltet UI-Navigation und verarbeitet lokale Personen-/Kontodaten.

## Zentrale Dateien, Komponenten und Teilbereiche
- `src/FrontendSerivce.py`: App-Initialisierung, Fensterkonfiguration und Start der Hauptschleife.
- `src/main.py`: Startpunkt, der `run()` aufruft.
- `src/navigator.py`: Routing/Navigationslogik zwischen den Screens.
- `src/screens/`: einzelne UI-Ansichten (z. B. Übersicht, Bearbeitung, Anlage).
- `src/controllers/AccountController.py`: Konto-/Berechnungslogik und Orchestrierung.
- `src/data/DataManager.py`: Laden/Speichern lokaler JSON-Daten und Berechnungsfunktionen.
- `src/models/`: interne Datenmodelle (z. B. AppState, Account, Bank, Person).
- `src/data/banken.json`, `src/data/kontotypen.json`: statische Datenquellen.
- `personen.json`: lokale Personendaten im Verzeichnis-Root von `FrontendService`.

## Einbindung ins Gesamtsystem
- Das Frontend ist der interaktive Einstiegspunkt für Endanwender.
- Es nutzt interne Controller/DataManager-Komponenten für fachliche Verarbeitung.
- Für Wertpapier-bezogene Informationen (Preis/Unternehmensdaten) greift es auf den Marktdatenbereich (`markedataservice`) zurück.

## Erkennbare interne/externe Abhängigkeiten
**Intern:**
- Abhängigkeiten zwischen `navigator`, `screens`, `controllers`, `data`, `models`.

**Extern (laut Root-Dependency-Definition):**
- `customtkinter`, `matplotlib`, `numpy`, `python-dotenv`, `requests`, `tkcalendar`.

## Bekannte Besonderheiten, Risiken oder offene Punkte
- Der Dateiname `FrontendSerivce.py` enthält eine auffällige Schreibweise; dies ist Bestandteil des aktuellen Ist-Zustands.
- In der Navigation sind Routen auf tiefere Screen-Pfade referenziert, die nicht vollständig in der sichtbaren Struktur auf erster Ebene verifiziert werden können.
- Datenhaltung erfolgt dateibasiert (JSON), was bei Parallelzugriffen oder Mehrbenutzerbetrieb funktionale Grenzen haben kann.

## Lokaler Start (zentraler Startweg)
Aus dem Repository-Root:

```bash
uv run finanzuebersicht
```

Der zentrale Entry-Point liegt in `FrontendService.src.launcher:main`.
