# Architektur-Analyse: Finanzuebersicht

> Stand: 2026-04-12, Branch `Microservice_umbau`

---

## 1. Systemuebersicht

Monorepo mit **Vue 3 SPA** (TypeScript/Vite), einem **FastAPI API-Gateway** (BFF-Pattern) und **6 fachlichen Microservices**. Alle Python-Services teilen ein internes `finanzuebersicht-shared`-Paket. Persistenz ueber **MongoDB** (Docker), Marktdaten via **FMP API** + **yfinance**.

```
Browser (Vue SPA, :5173)
    |
    v
API-Gateway (:8000)        <-- einziger oeffentlicher Endpunkt
    |
    +---> masterdata-service  (:8001)   Banken, Kontotypen
    +---> person-service      (:8002)   Personen, Bank-Zuordnungen, Steuer-Freibetraege  [MongoDB]
    +---> account-service     (:8003)   Konten (Giro, Tagesgeld, Festgeld, Depot)
    +---> portfolio-service   (:8004)   Portfolios, Holdings  [MongoDB / InMemory]
    +---> marketdata-service  (:8005)   Kurse, Profile, Historien  [FMP + yfinance, MongoDB-Cache]
    +---> analytics-service   (:8006)   Aggregation, Dashboard, Risiko-Metriken
```

---

## 2. Zentrale Architekturentscheidungen

### 2.1 BFF-Gateway als einziger Zugangspunkt
- Das Frontend spricht ausschliesslich mit dem API-Gateway (`/api/v1`).
- Das Gateway proxyt jeden Request an den zustaendigen Downstream-Service und extrahiert `response.json()["data"]`.
- Kein Service Discovery, kein Message-Broker — reine synchrone HTTP-Kommunikation (httpx).

### 2.2 Shared-Paket als Querschnittsbibliothek
- `finanzuebersicht_shared` liefert: App-Factory, `ServiceSettings`-Basisklasse (pydantic-settings), Error-Handler, Request-Context-Middleware (X-Request-ID, X-Correlation-ID), Health-Endpoint, JSON-Logging, Test-Utilities.
- Jeder Service erbt seine Settings von `ServiceSettings` und laedt `.env` aus dem CWD bzw. dem Repo-Root als Fallback.
- Konvention: Kein `os.getenv()` — immer ueber `get_settings()`.

### 2.3 Repository-Pattern mit Backend-Switch
- person-service, portfolio-service und marketdata-service nutzen abstrakte Repository-Klassen mit konkreten Mongo- und InMemory-Implementierungen.
- portfolio-service waehlt das Backend via `PORTFOLIO_REPOSITORY_BACKEND` (default: `mongo`, Fallback: `inmemory`).
- marketdata-service prueft beim Start die Mongo-Erreichbarkeit und faellt automatisch auf InMemory zurueck.

### 2.4 Analytics-Service als Aggregator
- Der analytics-service hat **keine eigene Datenhaltung**, sondern ruft zur Laufzeit person-service, account-service, portfolio-service und marketdata-service auf.
- Ergebnisse werden in mehreren **TTL-LRU-Caches** zwischengespeichert (Personen: 3600s, Portfolio-Snapshot: 10s, Dashboard-Sektionen: 45s).
- Hintergrund-Refresh ueber `ThreadPoolExecutor` (8 Worker).
- Verwendet **synchrones** `httpx.Client` (anders als das Gateway, das async arbeitet).

### 2.5 Mehrstufiges Marktdaten-Caching
- marketdata-service hat 4 getrennte Cache-Repositories: Profile, aktuelle Kurse, Kurshistorien, Financials.
- Jeder Cache hat eigene TTLs (Profile: 300s, Financials: 3600s).
- Externe Provider: FMP (primaer, via requests mit Retry-Adapter) und yfinance (Fallback/Ergaenzung).
- `CacheStatus`-Literal kommuniziert dem Aufrufer den Frischegrad: `fresh_cache | stale_cache | cache_miss_seeded | cache_miss_pending | provider_error_fallback`.

### 2.6 Frontend-Architektur
- Feature-Module-Struktur: `modules/{feature}/api/`, `components/`, `pages/`, `model/`, `__tests__/`.
- Zentraler `apiClient`-Fassaden-Export in `shared/api/client.ts`, darunter ein einzelner Axios-Instance auf den Gateway.
- Portfolio-Dashboard via `usePortfolioDashboard`-Composable: laedt kombiniert ueber `/portfolio-dashboard` und verteilt Sektionen (Summary, Performance, Exposures, Holdings, Risk, Contributors, Coverage).
- Formatierung durchgaengig de-DE (EUR, Komma als Dezimal, deutsche Labels).

---

## 3. Service-Abhaengigkeiten (Aufruf-Graph)

```
Frontend
  └─> API-Gateway
        ├─> person-service          (direkt)
        ├─> masterdata-service      (direkt)
        ├─> account-service         (direkt)
        ├─> portfolio-service       (direkt)
        ├─> marketdata-service      (direkt)
        └─> analytics-service       (direkt)
              ├─> person-service     (Existenzpruefung, gecacht)
              ├─> account-service    (Kontenliste)
              ├─> portfolio-service  (Portfolios + Holdings)
              └─> marketdata-service (Profile, Kurse, Historien)
```

**Kritischer Pfad:** Analytics-Service hat transitive Abhaengigkeiten auf 4 andere Services. Ein Ausfall von marketdata-service oder portfolio-service fuehrt zu Fehlern im gesamten Dashboard.

---

## 4. Datenmodell-Ueberblick

| Domaene | Service | Entitaeten |
|---|---|---|
| Stammdaten | masterdata | Bank (BIC, BLZ), AccountType (Schema-Felder) |
| Personen | person | Person, TaxProfile, PersonBankAssignment, TaxAllowance |
| Konten | account | PersonAccount (Giro/Tages/Festgeld/Depot) |
| Portfolio | portfolio | Portfolio, Holding (Symbol, ISIN, Kaufdaten) |
| Marktdaten | marketdata | InstrumentProfile, Kurshistorien, Financials, BatchPrices |
| Analytik | analytics | Berechnete Modelle: Summary, Performance, Exposures, Risk, Contributors, Coverage |

---

## 5. Potenzielle Problembereiche

### 5.1 Kein Connection-Pooling im Gateway
Das Gateway oeffnet pro Request einen neuen `httpx.AsyncClient` und schliesst ihn danach. Bei hoher Last fuehrt das zu TCP-Connection-Churn und potenziellen Socket-Erschoepfungen. **Empfehlung:** Einen langlebigen `AsyncClient` pro Upstream-Service verwenden (z.B. als Singleton im DI-Container).

### 5.2 Synchrone Aufrufe im Analytics-Service
Der analytics-service nutzt synchrones `httpx.Client`, waehrend er auf einem async FastAPI-Server laeuft. Das blockiert den Event-Loop-Thread bei jedem Downstream-Call. Bei gleichzeitigen Requests kann das zum Bottleneck werden. **Empfehlung:** Auf `httpx.AsyncClient` umstellen oder die sync-Calls konsequent in den ThreadPoolExecutor auslagern.

### 5.3 Kaskadierender Ausfall (kein Circuit Breaker)
Wenn ein Downstream-Service nicht erreichbar ist, wartet das Gateway bis zum Timeout (30s default). Es gibt keinen Circuit-Breaker oder Fallback-Mechanismus. Bei Ketten-Calls (Gateway → Analytics → 4 Services) multipliziert sich die Latenz. **Empfehlung:** Timeouts verkuerzen, Health-Check-basierte Circuit-Breaker einfuehren, Dashboard-Sektionen parallel statt sequentiell laden.

### 5.4 Dashboard: Sequentielle Sektion-Abfragen
Der Gateway-Endpoint `/dashboard` ruft die 4 Analytics-Sektionen (overview, allocation, timeseries, metrics) **sequentiell** ab. Jede Sektion macht intern wiederum mehrere synchrone Downstream-Calls. **Empfehlung:** `asyncio.gather()` fuer parallele Sektion-Abfragen nutzen.

### 5.5 InMemory-Fallback ohne Warnung an den Client
Wenn marketdata-service oder portfolio-service auf InMemory zurueckfallen (Mongo nicht erreichbar), gehen Daten bei Neustart verloren. Der Client erhaelt keine Information darueber, ob persistente oder fluechtige Speicherung aktiv ist. **Empfehlung:** Health-Endpoint oder Response-Header, der den aktiven Backend-Typ kommuniziert.

### 5.6 Fehlende Authentifizierung / Autorisierung
Kein Service implementiert Auth. Alle Endpunkte sind unauthentifiziert erreichbar. Fuer ein persoenliches Finanz-Tool mag das akzeptabel sein, aber bei Multi-User-Betrieb waere ein Auth-Layer (z.B. JWT via Gateway) noetig.

### 5.7 Daten-Konsistenz zwischen Services
Es gibt keine Transaktionen ueber Service-Grenzen hinweg. Beispiel: Wenn ein Konto als "Depot" angelegt wird, muss separat ein Portfolio im portfolio-service erstellt werden. Diese Kopplung passiert im Frontend (`DepotHoldingsManager` ruft `resolvePortfolio` auf), nicht im Backend. Bei Fehlern kann ein verwaistes Konto ohne Portfolio entstehen.

### 5.8 Duplizierte Modelle
Die API-Gateway `models.py` enthaelt **alle** Read-Models aller Downstream-Services nochmal als eigene Pydantic-Klassen. Aenderungen an einem Service-Modell muessen manuell im Gateway nachgezogen werden. **Empfehlung:** Shared-Models aus `finanzuebersicht_shared` verwenden oder die Gateway-Schicht so gestalten, dass sie die JSON-Antworten transparent durchreicht.

### 5.9 Test-Isolation
Alle Backend-Tests manipulieren `sys.path` zur Laufzeit, um `shared/src` einzubinden. Das ist fragil und kann bei paralleler Testausfuehrung zu Import-Konflikten fuehren. Die `uv`-Workspace-Konfiguration sollte das eigentlich ueber die Package-Installation loesen.

### 5.10 Marketdata-Service Komplexitaet
Der marketdata-service ist der komplexeste Service: 2 externe Provider, 4 Cache-Repositories, mehrstufige Fallback-Logik, Hintergrund-Seeding von Historien. Die Verantwortlichkeiten (Suche, Profile, aktuelle Kurse, Historien, Financials, Batch-Operationen, Benchmarks) koennten langfristig in Sub-Services aufgeteilt werden.

---

## 6. Tech-Debt und Verbesserungspotenzial

| Bereich | Status | Prioritaet |
|---|---|---|
| Connection-Pooling (Gateway) | Fehlt | Hoch |
| Async Downstream-Calls (Analytics) | Sync blockiert Event-Loop | Hoch |
| Parallele Dashboard-Sektionen | Sequentiell | Mittel |
| Circuit Breaker / Retry-Strategie | Nur FMP-Client hat Retries | Mittel |
| Auth-Layer | Komplett fehlend | Mittel (je nach Deployment) |
| Modell-Duplizierung (Gateway) | Manueller Sync | Niedrig |
| sys.path-Manipulation in Tests | Fragil | Niedrig |
| InMemory-Fallback-Transparenz | Nicht kommuniziert | Niedrig |

---

## 7. Staerken der Architektur

- **Klare Service-Grenzen:** Jeder Service hat eine klar definierte Domaene mit einheitlicher interner Struktur.
- **Shared-Paket:** Cross-Cutting-Concerns (Logging, Error-Handling, Health, Request-Context) sind sauber zentralisiert.
- **Gute Testabdeckung:** Jeder Service hat API-Level-Tests, das Frontend hat umfangreiche Component- und Composable-Tests.
- **Flexible Persistenz:** Repository-Pattern erlaubt einfachen Wechsel zwischen Mongo und InMemory.
- **Durchdachtes Caching:** Mehrstufiges Caching im marketdata-service mit transparentem Cache-Status.
- **Frontend-Modularitaet:** Feature-Module-Architektur mit sauberer Trennung von API, Model, Components und Pages.