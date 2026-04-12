# QA-Audit: Analytics-Dashboard Berechnungen

**Datum:** 2026-04-12  
**Scope:** Vollständiger Audit aller Berechnungen und Datentransformationen im Analytics-Dashboard  
**Geprüfte Schichten:** Analytics-Service, API-Gateway, Frontend (Dashboard-Modul)

---

## Zusammenfassung

Es wurden **25 Findings** identifiziert, davon:
- **4 hoch** (potenziell falsche Zahlen beim Nutzer)
- **11 mittel** (systematische Abweichungen oder Datenverlust)
- **10 niedrig** (Inkonsistenzen, tote Code-Stellen, UX-Details)

Die kritischsten Probleme betreffen:
1. Einheitenkonflikte zwischen Ratio (0.05) und Prozent (5.0) an mehreren Stellen
2. Falsche Volatilitätsberechnung (Population statt Sample Varianz)
3. Falsche Downside-Volatilität (Sortino-Ratio betroffen)
4. Fehlende Währungsumrechnung bei Multi-Currency-Portfolios

---

## Kritische Findings (HOCH)

### H-1: ~~Einheitenkonflikt bei Prozent-Werten (Ratio vs. Prozent)~~ — KEIN BUG (nach Code-Review verifiziert)

**Status:** Nach eingehender Prüfung des Backend-Codes **kein tatsächlicher Bug**.

Das Backend berechnet `unrealized_return_pct = unrealized_pnl / invested_value * 100` und `return_pct = absolute_change / start_value * 100` — beide Werte sind bereits Prozentzahlen (z.B. 5.0 für 5%). `formatPercentValue()` behandelt sie korrekt. Die Namenskonvention `_pct` bedeutet im Projekt durchgängig "bereits als Prozentzahl", `_ratio` für Dezimalbrüche.

**Empfehlung:** Konvention im Shared-Package als Kommentar dokumentieren, damit zukünftige Entwickler sie nicht in Frage stellen.

### H-2: ~~Residual-Berechnung mischt unterschiedliche Einheiten~~ — KEIN BUG (nach Code-Review verifiziert)

**Status:** Nach eingehender Prüfung des Backend-Codes **kein tatsächlicher Bug**.

Beide Werte (`return_pct` und `total_contribution_pct_points`) sind im Backend bereits als Prozentzahlen im ×100-Massstab: `return_pct = absolute_change / start_value * 100` und `total_contribution_pct_points = total_contribution_return * 100`. Die Subtraktion `5.0 - 4.5 = 0.5pp` ist rechnerisch korrekt.

### H-3: Fehlende Waehrungsumrechnung bei Multi-Currency-Portfolios

**Dateien:**
- `services/analytics-service/app/service.py:79, 600, 1173, 1289`
- `shared/src/finanzuebersicht_shared/models.py`

**Problem:** Alle Betraege werden hart als EUR behandelt (`currency: str = "EUR"`). Wenn ein Portfolio USD- oder GBP-denominierte Holdings enthaelt, werden deren `market_value` ohne Waehrungsumrechnung aufsummiert. Die Gesamtsumme, investierter Wert, unrealisierter P&L und alle daraus abgeleiteten Kennzahlen sind dann eine Mischung aus verschiedenen Waehrungen.

**Auswirkung:** Bei Portfolios mit Nicht-EUR-Positionen sind saemtliche aggregierten Betraege und Renditen falsch.

**Verbesserungsvorschlag:**
- Waehrungskurse vom Marketdata-Service abrufen und alle Betraege in eine Referenzwaehrung umrechnen
- Alternativ: Im UI deutlich kennzeichnen, dass Betraege ohne Waehrungsumrechnung aggregiert werden
- Langfristig: Waehrungsumrechnungs-Layer im Analytics-Service implementieren

### H-4: Volatilitaet systematisch zu niedrig (Population statt Sample Varianz)

**Datei:** `services/analytics-service/app/service.py:370`

**Problem:** Die `_volatility`-Methode berechnet die Populationsstandardabweichung (Division durch N) statt der Stichprobenstandardabweichung (Division durch N-1, Bessel-Korrektur). In der Finanzwelt ist die Stichprobenstandardabweichung Standard.

**Auswirkung:** Die Volatilitaet wird systematisch unterschaetzt. Bei 2 Datenpunkten betraegt der Fehler ~41%, bei 10 Datenpunkten ~5%. Dies beeinflusst direkt:
- Portfolio-Volatilitaet
- Annualisierte Volatilitaet
- Tracking Error
- Downside-Volatilitaet
- Sharpe Ratio (wird zu hoch angezeigt)
- Sortino Ratio (wird zu hoch angezeigt)
- Information Ratio (wird zu hoch angezeigt)

**Verbesserungsvorschlag:**
- `len(values)` durch `len(values) - 1` ersetzen (mit Guard fuer `len < 2`)
- Alternativ `statistics.stdev()` aus der Python-Standardbibliothek verwenden

---

## Mittlere Findings

### M-1: Downside-Volatilitaet falsch berechnet

**Datei:** `services/analytics-service/app/service.py:1352-1353`

**Problem:** Die Downside-Volatilitaet wird nur ueber negative Returns berechnet (Standardabweichung der negativen Teilmenge). Die korrekte Definition ist: Quadratwurzel des Durchschnitts der quadrierten Abweichungen unter einem Schwellenwert (typisch 0), berechnet ueber ALLE Perioden.

**Auswirkung:** Die Downside-Volatilitaet ist systematisch zu hoch, der Sortino Ratio dadurch systematisch zu niedrig.

**Verbesserungsvorschlag:**
- Downside Deviation korrekt als `sqrt(sum(min(r, 0)^2) / N)` ueber alle Perioden berechnen, nicht nur ueber die negativen

### M-2: Active Return vergleicht unterschiedliche Zeitfenster

**Datei:** `services/analytics-service/app/service.py:1349-1350`

**Problem:** `mean_portfolio_return` wird ueber alle Portfolio-Returns berechnet, `mean_benchmark` nur ueber die aligned (datumsueberlappenden) Benchmark-Returns. Bei unterschiedlicher Datenabdeckung werden verschiedene Zeitfenster verglichen.

**Auswirkung:** Der Active Return kann irrefuehrend sein, wenn Portfolio und Benchmark unterschiedliche Datumsabdeckung haben.

**Verbesserungsvorschlag:**
- Beide Mittelwerte ueber denselben aligned Datensatz berechnen

### M-3: Return-Datenpunkte um einen Tag verschoben

**Datei:** `services/analytics-service/app/service.py:362`

**Problem:** In `_portfolio_return_points` wird die Return-Rate `(curr - prev) / prev` dem Datum `points[idx - 1].x` (Vortag) zugeordnet statt dem aktuellen Tag. Die Konvention ist, dass ein Tagesreturn dem Tag zugeordnet wird, an dem er realisiert wurde.

**Auswirkung:** Wenn Return-Serien mit externen Daten verglichen werden, sind die Daten um einen Tag verschoben. `best_day_return` und `worst_day_return` werden dem falschen Datum zugeordnet.

**Verbesserungsvorschlag:**
- Return dem aktuellen Datum `points[idx].x` zuordnen statt `points[idx - 1].x`

### M-4: Dashboard-Aggregation im Gateway verwirft Metadaten

**Datei:** `services/api-gateway/app/service.py:561-580`

**Problem:** Bei der Dashboard-Aggregation werden `generated_at`, `stale_at`, `refresh_in_progress` und `warnings` aus den Section-Responses komplett verworfen. Nur `state` wird als undokumentiertes `_state`-Feld injiziert.

**Auswirkung:** Das Frontend kann nicht anzeigen, wann Daten generiert wurden, ob sie veraltet sind, oder ob ein Refresh laeuft.

**Verbesserungsvorschlag:**
- Section-Metadaten in das `DashboardReadModel` aufnehmen (z.B. als `section_meta` pro Section)
- `_state`-Injection durch ein sauberes, dokumentiertes Feld ersetzen

### M-5: Dashboard-Modelle im Gateway komplett untypisiert

**Dateien:**
- `services/api-gateway/app/models.py:366-372`
- `services/api-gateway/app/routers/api_v1.py:197-222`

**Problem:** `DashboardReadModel` verwendet `dict` fuer alle Section-Felder. Die Dashboard-Section-Endpoints verwenden `response_model=ApiResponse[dict]`. Das Analytics-Service hat fuer diese Daten wohldefinierte Models, aber der Gateway validiert nichts.

**Auswirkung:** Schema-Aenderungen im Analytics-Service werden nicht erkannt; Fehler werden erst beim Nutzer sichtbar.

**Verbesserungsvorschlag:**
- Die Analytics-Models (`OverviewReadModel`, `AllocationReadModel`, etc.) in `shared/` verschieben und im Gateway verwenden
- Oder zumindest im Gateway eigene Response-Models definieren

### M-6: Inkonsistente `hasNumber`-Implementierungen im Frontend

**Dateien:**
- `frontend-web/src/modules/dashboard/model/portfolioFormatting.ts:4`
- `frontend-web/src/modules/dashboard/model/portfolioAlerts.ts:144`
- `frontend-web/src/modules/dashboard/model/portfolioAttribution.ts:32`

**Problem:** Drei verschiedene Implementierungen: Eine akzeptiert `Infinity`, zwei nicht. Die Formatting-Funktionen (die dem Nutzer Werte anzeigen) sind am permissivsten -- `Infinity` koennte als "Infinity %" angezeigt werden.

**Auswirkung:** Bei Division-by-Zero-Faellen (z.B. invested_value = 0) koennte "Infinity %" im UI erscheinen.

**Verbesserungsvorschlag:**
- Eine einzige `hasNumber`-Funktion in `shared/` definieren, die `Number.isFinite()` verwendet
- In allen Modulen dieselbe Funktion importieren

### M-7: Sort-Vergleiche koennen NaN produzieren

**Dateien:**
- `frontend-web/src/modules/dashboard/composables/usePortfolioDashboard.ts:376`
- `frontend-web/src/modules/dashboard/components/PortfolioHoldingsTable.vue:124`

**Problem:** Sortierung nach `market_value` und `weight` ohne Null-Guards. Bei `undefined` oder `null` erzeugt JavaScript-Subtraktion `NaN`, was zu unvorhersehbarer Sortierreihenfolge fuehrt.

**Verbesserungsvorschlag:**
- Fallback-Wert verwenden: `(right.market_value ?? 0) - (left.market_value ?? 0)`

### M-8: `formatSignedRatioPercentPoints` -- moegliche 100x-Abweichung

**Datei:** `frontend-web/src/modules/dashboard/components/PortfolioRiskPanel.vue:203-205`

**Problem:** Multipliziert `active_return` mit 100 fuer die Anzeige als Prozentpunkte. Korrekt nur wenn `active_return` als Ratio vom Backend kommt. Wenn es bereits in Prozentpunkten vorliegt, ist der angezeigte Wert 100x zu hoch.

**Verbesserungsvorschlag:**
- Backend-Kontrakt klarlegen (siehe H-1)

### M-9: Dashboard-Timeseries nutzt keine History-Sanitization

**Datei:** `services/analytics-service/app/service.py`

**Problem:** `_build_timeseries` verwendet `_load_history_points` ohne Sanitization (Filterung von `close <= 0`), waehrend der Performance-Pfad `_sanitize_history_points` nutzt. Null- oder Negativ-Preise koennten in die Dashboard-Timeseries gelangen.

**Verbesserungsvorschlag:**
- `_sanitize_history_points` konsistent auf allen Pfaden anwenden

### M-10: Testabdeckung hat signifikante Luecken

**Dateien:**
- `services/analytics-service/tests/test_analytics_api.py`
- `services/api-gateway/tests/test_gateway_api.py`

**Problem:** Die meisten Berechnungen (Sharpe, Sortino, Information Ratio, Forecast, Monthly Comparison, Heatmap, Metrics) werden nur auf Existenz geprueft (`is not None`, Status 200), nicht auf korrekte Werte. Der Gateway-Test-Stub umgeht die reale Aggregationslogik. Keine Feldwert-Assertions fuer Dashboard-Daten.

**Verbesserungsvorschlag:**
- Parametrisierte Tests mit bekannten Input/Output-Paaren fuer alle Finanzkennzahlen
- Gateway-Integration-Tests, die die reale Aggregationslogik testen
- Mindestens Golden-File-Tests fuer die wichtigsten Berechnungspfade

### M-11: Contributors-Bereich versteckt wenn Attribution vorhanden

**Datei:** `frontend-web/src/modules/dashboard/components/PortfolioDashboardContainer.vue:270`

**Problem:** `hasContributorsArea` ist `false` wenn Attribution-Daten existieren. Dadurch gehen moeglicherweise Contributor-spezifische Informationen (z.B. `total_contribution_return`, Warnungen) verloren.

**Verbesserungsvorschlag:**
- Contributors-Daten in die Attribution-Ansicht integrieren oder als ergaenzende Information erhalten

---

## Niedrige Findings

### N-1: Sharpe Ratio ohne Risk-Free Rate

**Datei:** `services/analytics-service/app/service.py:1358`

Die Berechnung setzt `R_f = 0`. Dies ist eine gaengige Vereinfachung, sollte aber im UI dokumentiert oder als Annahme gekennzeichnet werden.

### N-2: Naiver Forecast mit willkuerlichem Konfidenzband

**Datei:** `services/analytics-service/app/service.py:1117-1118`

Additive lineare Extrapolation statt multiplikativer. Das 3%-Konfidenzband ist nicht statistisch fundiert.

### N-3: Erster Monat in Monthly Comparison zeigt immer Delta = 0

**Datei:** `services/analytics-service/app/service.py:1061-1069`

Der erste Monat hat keinen Vormonat zum Vergleich und zeigt daher immer 0.

### N-4: Doppelte Warnungen bei fehlender History

**Datei:** `services/analytics-service/app/service.py:440, 448`

Bei fehlender History werden zwei verschiedene Warnungen erzeugt (`missing_history` und `history_fallback_to_market_value`), was die Diagnostik erschwert.

### N-5: DepotAllocationPanel zeigt Positions-Anzahl statt Wert-Gewichtung

**Datei:** `frontend-web/src/modules/dashboard/components/DepotAllocationPanel.vue:103`

Die "Share"-Anzeige basiert auf der Anzahl der Positionen, nicht auf dem Marktwert. Dies kann Nutzer irrefuehren.

### N-6: Instrument-Risikowerte ohne Formatierung angezeigt

**Datei:** `frontend-web/src/modules/dashboard/components/InstrumentAnalysisTabs.vue:68-70`

Volatilitaetswerte werden als Rohzahlen ohne Prozent-Formatierung dargestellt (z.B. `0.15432` statt `15,43 %`).

### N-7: Inkonsistenter Currency-Fallback (`||` vs `??`)

**Dateien:** Mehrere Komponenten verwenden unterschiedlich `||` (faengt leeren String) vs `??` (nur null/undefined) fuer den EUR-Fallback. Bei `currency: ""` verhalten sich die Komponenten unterschiedlich.

### N-8: Negative Gewichte in Exposures-Bars werden auf 0% geklemmt

**Datei:** `frontend-web/src/modules/dashboard/components/PortfolioExposuresPanel.vue:156-162`

Short-Positionen zeigen keinen Balken, obwohl sie in der Liste mit negativem Wert erscheinen.

### N-9: Toter Code im Dashboard-Composable

**Dateien:**
- `frontend-web/src/modules/dashboard/composables/usePortfolioDashboard.ts:280-296` (`loadInOrder` -- nie aufgerufen)
- `frontend-web/src/modules/dashboard/composables/usePortfolioDashboard.ts:302-304` (`loadSecondary` -- leerer Stub)

### N-10: KPIs redundant auf zwei Ebenen im Dashboard-Response

**Datei:** `services/api-gateway/app/service.py:579`

`kpis` existiert sowohl in `overview.kpis` als auch auf Top-Level in `DashboardReadModel`.

---

## Priorisierte Handlungsempfehlungen

### Sofort (vor naechstem Release)

1. ~~**Einheiten-Konvention definieren**~~ (H-1, H-2) — Nach Code-Review: kein Bug. `_pct` = Prozentzahl (×100), `_ratio` = Dezimalbruch. Konvention bereits konsistent im gesamten Backend.

2. **[BEHOBEN] Volatilitaetsberechnung korrigiert** (H-4)
   - `services/analytics-service/app/service.py:370` — Bessel-Korrektur (N-1) implementiert
   - Betrifft: portfolio_volatility, annualized_volatility, tracking_error, downside_vol, Sharpe, Sortino, Information Ratio

3. **[BEHOBEN] Multi-Currency-Warnung implementiert** (H-3)
   - `shared/src/finanzuebersicht_shared/models.py` — `warnings` Feld in `PortfolioSummaryReadModel`
   - `services/analytics-service/app/service.py` — Erkennung von Non-EUR-Holdings, Warning `mixed_currency_no_conversion:<currencies>`
   - `frontend-web/src/shared/model/types.ts` — TypeScript-Typ aktualisiert
   - `frontend-web/src/modules/dashboard/model/portfolioAlerts.ts` — Alert-Regel `deriveSummaryAlerts` implementiert
   - Vollstaendige Waehrungsumrechnung bleibt offenes Folge-Ticket (siehe Mittelfristig)

4. **Downside-Volatilitaet korrigieren** (M-1)
   - Standard-Downside-Deviation-Formel implementieren (`sqrt(sum(min(r,0)^2) / N)` ueber alle Perioden)

### Kurzfristig

1. **Active Return auf aligned Daten beschraenken** (M-2)
2. **Return-Datumszuordnung korrigieren** (M-3)
3. **`hasNumber` vereinheitlichen** (M-6)
4. **Berechnungs-Tests mit bekannten Werten schreiben** (M-10)

### Mittelfristig

1. **Waehrungsumrechnung vollstaendig implementieren** (H-3 — Warnung bereits implementiert)
2. **Dashboard-Models typisieren** (M-5)
3. **Section-Metadaten durchreichen** (M-4)
4. **History-Sanitization vereinheitlichen** (M-9)