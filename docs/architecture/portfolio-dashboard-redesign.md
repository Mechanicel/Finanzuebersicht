# Portfolio-/Depot-Dashboard Redesign (Zielarchitektur)

## 1) Ausgangslage

Das aktuelle Dashboard liefert bereits relevante Informationen, ist aber strukturell noch stark von generischen Analyse-Sektionen geprägt und nicht als konsistentes Portfolio-Cockpit modelliert.

Heute sind die Verantwortlichkeiten grundsätzlich vorhanden, aber für das neue Zielbild noch nicht ausreichend scharf getrennt:

- **Frontend Dashboard / Depot-Analyse**
  - UI-Komposition und Darstellung in Dashboard-Views und Analyse-Tabs.
- **analytics-service** als personen-/dashboardbezogener Aggregator
  - Führt portfolio- und nutzerbezogene Aussagen zusammen.
- **marketdata-service** als instrumentnaher Datendienst
  - Liefert instrumentzentrierte Marktdaten und Kennzahlen.
- **api-gateway** als öffentliche App-Schicht
  - Reicht Endpunkte für die App weiter und bündelt Servicezugriffe.

Ziel dieses Dokuments ist, die nächste Ausbaustufe als **klare Zielarchitektur** zu fixieren, bevor produktive Implementierungen beginnen.

## 2) Zielbild

Das zukünftige Dashboard ist ein professionelles Portfolio-Cockpit mit klaren, stabilen Bereichen:

1. **Executive Summary**
   - Kompakte Portfolio-Gesamtaussage (Wert, P&L-Tendenz, Risiko-/Coverage-Hinweise).
2. **Portfolio Performance**
   - Zeitliche Entwicklung inkl. vergleichbarer Referenz (Benchmark), soweit verfügbar.
3. **Exposures / Allocation**
   - Aufteilung nach Asset-Klassen, Regionen, Sektoren, Währungen (stufenweise ausbaubar).
4. **Holdings-Tabelle**
   - Vollständige Positionenliste mit sortier-/filterbaren Kernkennzahlen.
5. **Instrument-Detailansicht**
   - Fokus auf ausgewählte Position inkl. instrumentnaher Zeitreihen/Primitive.
6. **Data Coverage / Warnings**
   - Transparenz über Datenlücken, Stale-Daten, unbekannte Zuordnungen und daraus resultierende Einschränkungen.

## 3) Verantwortungsgrenzen pro Service

### Zentrale Regel (verbindlich)

- **`marketdata-service` liefert instrumentnahe Primitive.**
- **`analytics-service` aggregiert portfolio-/personenbezogene Aussagen.**

Diese Regel ist die zentrale Architekturgrenze und darf in den Folgephasen nicht verwässert werden.

### analytics-service

Gehört in den analytics-service:

- Portfolio-/personenbezogene Aggregation über mehrere Holdings/Instrumente.
- KPI-Bildung für Dashboard-Abschnitte (Summary, Performance, Exposures, Risk, Contributors).
- Konsistente businessnahe Response-Modelle für Dashboard-Use-Cases.
- Berechnung und Kennzeichnung von Coverage-/Warnzuständen auf Portfolioebene.

Nicht in den analytics-service:

- Rohnahe instrumentinterne Datenbeschaffung oder instrumentzentrierte Basis-Primitive, die im marketdata-service liegen.

### marketdata-service

Gehört in den marketdata-service:

- Instrumentnahe Datenprimitive (Preise, Timeseries, Financials-Metadaten, Risiko-Basiskennzahlen pro Instrument).
- Normalisierung/Validierung instrumentbezogener Datenquellen.
- Qualitätskennzeichnung auf Instrumentenebene.

Nicht in den marketdata-service:

- Keine Aggregation auf Portfolio-, Account- oder Personenebene.
- Keine dashboard-spezifischen zusammengesetzten Aussagen über mehrere Positionen.

### Frontend

Gehört ins Frontend:

- Präsentationslogik, visuelle Komposition, Interaktionssteuerung.
- UI-State (Selektion, Zeitraumwahl, Sortierung, Filter, Drilldown).
- Orchestrierung der Darstellung mehrerer analytics-Endpunkte.

Nicht ins Frontend:

- Keine Duplizierung zentraler Portfolio-Aggregationslogik, die im analytics-service liegen soll.

### api-gateway

Gehört ins api-gateway:

- Öffentliche Bereitstellung/Weiterleitung der vorgesehenen Analytics-Endpunkte.
- Auth-/Routing-/Transport-Aspekte.

Nicht ins api-gateway:

- Keine fachliche Neuaggregation oder Berechnungslogik für Dashboard-KPIs.

## 4) Geplante neue Analytics-Endpunkte

Folgende Endpunktmenge wird als Zielbild für den analytics-service festgelegt (Namen als Arbeitskontrakt, Feinheiten in der Implementierung konkretisieren):

### `portfolio-summary`

- **Zweck:** Executive Summary für den oberen Dashboard-Bereich.
- **Wichtigste Felder:** `portfolioValue`, `dayChangeAbs`, `dayChangePct`, `totalReturnAbs`, `totalReturnPct`, `currency`, `asOf`, `warnings[]`.
- **Warum analytics-service:** Werte sind portfolioübergreifende Aggregationen, nicht instrumentnahe Einzelprimitive.

### `portfolio-performance`

- **Zweck:** Performance-Verlauf über Zeiträume inkl. optionalem Benchmark-Vergleich.
- **Wichtigste Felder:** `timeseries[]` (Datum/Wert/Return), `periods` (1M/3M/YTD/1Y/ALL), `benchmarkSeries[]`, `drawdown`, `asOf`.
- **Warum analytics-service:** Konsolidiert Holdings, Cashflows/Positionsgewichtung und Referenzvergleich auf Portfolioebene.

### `portfolio-exposures`

- **Zweck:** Allokations-/Exposuresicht nach Dimensionen.
- **Wichtigste Felder:** `byAssetClass[]`, `byRegion[]`, `bySector[]`, `byCurrency[]`, `unknownShare`, `asOf`.
- **Warum analytics-service:** Erfordert portfolioweite Zusammenführung und Gewichtung vieler Instrumente.

### `portfolio-holdings`

- **Zweck:** Tabellarische Holdings-Sicht als primäre Datenquelle für die Positionsliste.
- **Wichtigste Felder:** `items[]` mit `instrumentId`, `name`, `quantity`, `avgCost`, `lastPrice`, `marketValue`, `weightPct`, `unrealizedPnLAbs`, `unrealizedPnLPct`, `dataQualityFlags[]`.
- **Warum analytics-service:** Tabelle ist bereits eine portfoliozentrierte Projektion mit berechneten Portfolioanteilen.

### `portfolio-risk`

- **Zweck:** Kompakte Risikoperspektive für Dashboard-Kacheln und Detailansicht.
- **Wichtigste Felder:** `volatility`, `maxDrawdown`, `concentrationTopN`, `valueAtRiskProxy`, `asOf`, `method`.
- **Warum analytics-service:** Risikoaussagen beziehen sich auf das Gesamtportfolio und die Gewichtung.

### `portfolio-contributors`

- **Zweck:** Top/Bottom-Treiber der Portfolio-Performance.
- **Wichtigste Felder:** `topPositive[]`, `topNegative[]` mit `instrumentId`, `contributionAbs`, `contributionPct`, `period`, `asOf`.
- **Warum analytics-service:** Contributions entstehen aus portfolioweiter Attribution, nicht aus Einzelinstrumentdaten.

### `portfolio-data-coverage`

- **Zweck:** Transparente Datenabdeckung und Warnhinweise.
- **Wichtigste Felder:** `coverageScore`, `missingPricesCount`, `stalePricesCount`, `missingClassificationsCount`, `issues[]`, `asOf`.
- **Warum analytics-service:** Coverage wird für das konkrete Portfolio und seine Zusammensetzung bewertet.

## 5) Geplante Erweiterungen im marketdata-service

Geplante Erweiterungen betreffen ausschließlich instrumentnahe Primitive:

- Bereitstellung echter **Timeseries-Serien** (nicht nur punktuelle Close-Weitergabe).
- Erweiterung instrumentbezogener **Risiko-Basiskennzahlen** (z. B. historische Volatilität auf Instrumentebene).
- Verbesserte **Financials-Coverage** und Konsistenzfelder je Instrument.
- Saubere **Benchmark-Primitive** (z. B. definierte Referenzreihen auf Instrument-/Indexebene).

Verbindliche Grenze:

- Auch nach Ausbau verbleibt der marketdata-service bei instrumentnahen Daten.
- **Es wird keine Portfolio-/Personenaggregation in den marketdata-service verschoben.**

## 6) Frontend-Migrationsziel

Zielstruktur des neuen Screens:

1. **Header / Kontextleiste**
   - Portfolio-Kontext, Stichtag, aktive Filter/Zeiträume.
2. **KPI-Bar**
   - Value, Return, Tagesänderung, zentrale Warnindikatoren.
3. **Performance & Risk Row**
   - Performance-Chart + kompakte Risikokennzahlen.
4. **Exposures / Allocation**
   - Mehrdimensionale Allokationswidgets.
5. **Holdings-Tabelle**
   - Primäre Arbeitsfläche für Positionen.
6. **Instrument-Detailpanel**
   - Kontextpanel für selektiertes Instrument mit Drilldown.

Zusätzliche Migrationsleitplanken:

- Bestehende generische Legacy-Sections werden schrittweise zurückgebaut oder klar de-priorisiert.
- JSON-/Rohdatenansichten sind nicht länger Hauptfokus der produktiven Hauptansicht.

## 7) Umsetzungsreihenfolge (Phasen)

1. **Architektur & Zielmodelle**
   - Zielkontrakte, Zuständigkeiten und Datenmodelle finalisieren.
2. **Neue Analytics-Modelle / Endpunkte**
   - Response-Modelle und Endpunkt-Skelette im analytics-service einführen.
3. **Portfolio-Aggregationslogik**
   - Fachlogik für Summary, Performance, Exposures, Holdings, Risk, Contributors.
4. **Gezielte marketdata-Erweiterungen**
   - Nur notwendige instrumentnahe Primitive für Analytics-Lücken ergänzen.
5. **Gateway-Verdrahtung**
   - Endpunkte im api-gateway veröffentlichen/weiterreichen.
6. **Frontend-Datenschicht**
   - Neue API-Clients, Mappings und ViewModel-Schicht einziehen.
7. **Neues Dashboard-Rendering**
   - Zielscreen-Struktur implementieren und legacy-lastige Bereiche zurückfahren.
8. **Cleanup / Tests**
   - Aufräumen, Regressionstests, Kontrakt-/Integrationsabsicherung.

## 8) Non-Goals / Grenzen (erste Ausbaustufe)

Folgende Themen sind zunächst bewusst nicht oder nur eingeschränkt enthalten:

- Vollständige **realized P&L**-Historisierung inklusive steuer-/transaktionsgenauer Aufbereitung.
- Echte **Long/Short-/Derivate-Exposures** mit institutioneller Tiefe.
- Komplexe **Faktor-Modelle** (Multi-Factor, Style-Factor Attribution).
- Tiefe **Event-/Earnings-Integration** als durchgängiger Workflow.
- Institutionelles Full-Stack-**Risikomodell** (z. B. szenariobasierte Monte-Carlo-Engine).

## 9) Referenzen auf bestehende Dateien (Ist-Zustand)

Diese bestehenden Orte sind zentrale Anknüpfungspunkte für die Folgearbeit:

- Frontend
  - `frontend-web/src/modules/dashboard/pages/DashboardPage.vue`
  - `frontend-web/src/modules/dashboard/components/DepotAnalysisWorkspace.vue`
  - `frontend-web/src/modules/dashboard/components/InstrumentAnalysisTabs.vue`
- analytics-service
  - `services/analytics-service/app/service.py`
  - `services/analytics-service/app/models.py`
  - `services/analytics-service/app/routers/api_v1.py`
- marketdata-service
  - `services/marketdata-service/app/service.py`
  - `services/marketdata-service/app/routers/api_v1.py`
- api-gateway
  - `services/api-gateway/app/routers/api_v1.py`

---

## 10) Implementierungsstand (April 2026)

Der initiale Umbau ist inzwischen umgesetzt und lauffähig:

- **Frontend-Primärpfad**: `PortfolioDashboardContainer` ist im Dashboard die primäre Arbeitsfläche.
- **Legacy-Pfad**: Alte generische Analytics-Sektionen bleiben verfügbar, sind aber als sekundäre Legacy-Sektion gekapselt.
- **analytics-service**: Portfolio-Endpunkte sind implementiert:
  - `portfolio-summary`
  - `portfolio-performance`
  - `portfolio-exposures`
  - `portfolio-holdings`
  - `portfolio-risk`
  - `portfolio-contributors`
  - `portfolio-data-coverage`
- **marketdata-service**: Instrumentnahe Primitive für erweiterte Reihen und Risiko sind verfügbar (u. a. `price`, `benchmark_price`, `returns`, `drawdown`, `benchmark_relative` inkl. additiver Risk-Felder).
- **api-gateway**: Die Portfolio-Endpunkte werden ohne Verlagerung fachlicher Aggregation durchgereicht.

Damit entspricht die aktuelle Verteilung weiterhin dem beabsichtigten Schnitt:
instrumentnahe Primitive im `marketdata-service`, Portfolio-/Personenaggregation im `analytics-service`, UI-Orchestrierung im Frontend.

## 11) Bewusst verbleibende Grenzen

Folgende Punkte sind aktuell bekannt und bewusst noch nicht voll ausgebaut:

- Keine vollständige **realized P&L**-Historisierung (transaktions-/steuerlogisch).
- Keine institutionelle Endausbaustufe einer **Risk-Engine** (z. B. vollständige Szenario-/VaR-Modellierung).
- Benchmark-/Statement-Tiefe ist funktionsfähig, aber noch nicht in allen Fällen auf institutionellem Detailniveau.
- Legacy-Bereiche bleiben vorerst vorhanden (sekundär), bis der Übergang final abgeschlossen ist.
- Lokale Testausführung kann in eingeschränkten Umgebungen unvollständig sein (fehlende Tooling-/Dependency-Binaries).

## 12) Reviewer-Hinweis

Für eine schnelle manuelle Prüfung siehe zusätzlich:

- `docs/qa/portfolio-dashboard-review-checklist.md`
