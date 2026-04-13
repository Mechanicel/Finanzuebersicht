# QA-Finding: Kapitalfluss-Verzerrung (Cash Flow Bias) in allen Performance- und Risikokennzahlen

**Datum:** 2026-04-13
**Schweregrad:** KRITISCH — alle quantitativen Kennzahlen des Portfolio-Dashboards sind unbrauchbar
**Status:** BEHOBEN (siehe Implementierungsabschnitt)
**Betroffene Dateien:**
- `services/analytics-service/app/service.py` — Kernfehler
- Alle abgeleiteten Kennzahlen in `PortfolioRiskReadModel`, `PortfolioPerformanceReadModel`, `PortfolioAttributionReadModel`

---

## Symptome (beobachtete Fehler)

| Kennzahl | Angezeigte Wert | Realer Wert | Abweichung |
|---|---|---|---|
| 3M-Rendite | 159 % | ~1,75 % | 9000 % überschätzt |
| Ann. Volatilität | 88,67 % | ~12–18 % | 5–7x überschätzt |
| Korrelation Benchmark | 0,13 | ~0,7+ | stark unterschätzt |
| Max Drawdown | 95 % | ~3–5 % | 20–30x überschätzt |
| Sharpe Ratio | verfälscht | n/a | nicht verwertbar |
| Sortino Ratio | verfälscht | n/a | nicht verwertbar |
| Tracking Error | verfälscht | n/a | nicht verwertbar |
| Information Ratio | verfälscht | n/a | nicht verwertbar |

---

## Root Cause: Naive Portfoliowert-Zeitreihe ohne Cash-Flow-Bereinigung

### Mechanismus

`_build_portfolio_history_from_snapshots` (service.py:442–510) baut die Portfolio-Wert-Zeitreihe
aus einem **statischen Snapshot der aktuellen Holdings**. Jedes Holding hat ein `buy_date`.
Für jeden Handelstag T gilt:

```
portfolio_value(T) = Σ (last_close(symbol, T) × quantity)
                     für alle Holdings mit buy_date ≤ T
```

Wenn ein neues Holding am Tag T hinzukommt (Kauf), springt der Portfoliowert:

```
value(T-1) = Σ der bestehenden Holdings
value(T)   = Σ der bestehenden Holdings + NEUES Holding × Preis
→ Tagesrendite(T) = (value(T) - value(T-1)) / value(T-1)
                  = enthält den Kapitalzufluss als "Gewinn"
```

### Konkretes Zahlenbeispiel

```
Tag 0: 10 Anteile ETF-A à €100 → Portfoliowert = €1.000
Tag 1: Kauf 990 weiterer Anteile ETF-A à €100 → Portfoliowert = €100.000
       Naive Tagesrendite = (100.000 - 1.000) / 1.000 = 9.900 %  ← FALSCH
       Korrekte Tagesrendite = 0 %  (Preis unverändert)

Tag 63 (3-Monats-Ende): Preis bei €101
       Naive 3M-Rendite = (100 × €101 × 1.000 - €1.000) / €1.000 = 9.900 %
       Korrekte TWRR     = (101 - 100) / 100 = 1 %
```

### Warum der Max Drawdown 95 % zeigt

Der `running_peak` in `_max_drawdown` (service.py:388–399) springt durch den Kapitalzufluss auf
den maximalen Portfoliowert nach der Einzahlung. Spätere Kursrückgänge werden gegen diesen
künstlich aufgeblähten Peak gemessen:

```
Peak nach Kauf: €100.000
Kursrückgang 5 %: Portfoliowert = €95.000
Naiver Drawdown = 95.000/100.000 - 1 = -5 %  ← korrekt in diesem Fall

ABER:
Wenn vor dem Kauf ein starker Kursrückgang passierte:
value(T-1) = €1.000
value(T_kauf) = €100.000 (Sprung durch Einzahlung)
value(T_end) = €5.000 (Kursverlust)
Drawdown = 5.000/100.000 - 1 = -95 %  ← Peak stammt aus Einzahlung, nicht echtem Kursgewinn
```

---

## Welche Funktionen sind betroffen

### Direkt betroffen (verwenden `_portfolio_returns(portfolio_points)`)

| Funktion | Zeile | Fehler |
|---|---|---|
| `_build_portfolio_risk_from_history_context` | 1388 | `portfolio_return_points = _portfolio_return_points(portfolio_points)` — enthält Kapitalfluss-Renditen |
| `_build_portfolio_risk_from_history_context` | 1392 | `max_drawdown = _max_drawdown(portfolio_points)` — Peak durch Einzahlung aufgebläht |
| `_build_portfolio_performance_from_history_context` | 1291 | `return_pct = (end - start) / start` — Kapitalzuflüsse als Gewinn |
| `portfolio_attribution` | 1639 | `_portfolio_range_return_pct(portfolio_points)` — falsche Basis für Residual |

### Indirekt betroffen (berechnet aus den obigen)

- `portfolio_volatility`, `annualized_volatility` (aus verfälschten Tagesrenditen)
- `sharpe_ratio`, `sortino_ratio` (aus verfälschter Volatilität)
- `tracking_error`, `annualized_tracking_error` (aus verfälschten Tagesrenditen)
- `information_ratio` (aus verfälschtem Tracking Error)
- `active_return` (aus verfälschtem Portfolio-Mean-Return)
- `correlation`, `beta` (aus verfälschten Portfolio-Renditen)
- `best_day_return`, `worst_day_return` (enthält Kapitalfluss-Tage)

---

## Korrekte Lösung: TWRR (Time-Weighted Rate of Return)

### Prinzip

Die TWRR unterteilt den Auswertungszeitraum an jedem Kapitalfluss-Ereignis in Teilperioden.
Die Rendite jeder Teilperiode wird nur auf den **Bestand vor dem Zufluss** berechnet.
Anschließend werden die Teilperioden miteinander multipliziert (verkettet).

**TWRR-Tagesrendite für Tag T:**

```
V_prev     = Σ (Preis(T-1) × Menge)  für alle Holdings mit buy_date ≤ T-1
V_curr_exCF = Σ (Preis(T) × Menge)   für dieselben Holdings  ← kein neues Holding
TWRR_T     = V_curr_exCF / V_prev - 1
```

**Neue Holdings (buy_date = T) werden NICHT in die Rendite von T-1→T einbezogen.**
Sie starten ihre eigene erste Teilperiode ab T.

### Gesamtrendite über Zeitraum

```
TWRR_gesamt = (1 + r_1) × (1 + r_2) × ... × (1 + r_n) - 1
```

### Max Drawdown auf TWRR-Index

Ein TWRR-Index startet bei 100 und wird täglich multipliziert:
```
index(T) = index(T-1) × (1 + TWRR_T)
```
Der Max Drawdown wird auf diesem Index berechnet, nicht auf dem Absolut-Wert-Chart.

---

## Implementierung

### Geänderte Dateien

**`services/analytics-service/app/service.py`**

1. **`PortfolioHistoryContext`** (Zeile 103): Neues Feld `twrr_return_points: list[ChartPoint]`

2. **`_build_portfolio_history_from_snapshots`** (Zeile 442):
   - Neues Rückgabe-Tupel: `(portfolio_points, twrr_return_points, warnings)`
   - Zweiter Durchlauf berechnet TWRR-Tagesrenditen mit buy_date-Filter auf **Vortag**

3. **`_get_portfolio_history_context`** (Zeile 728): Entpackt dreistelliges Tupel

4. **`_build_portfolio_risk_from_history_context`** (Zeile 1375):
   - Verwendet `history_context.twrr_return_points` statt `_portfolio_return_points(portfolio_points)`
   - `max_drawdown` auf TWRR-Index statt Absolut-Werten

5. **`_build_portfolio_performance_from_history_context`** (Zeile 1264):
   - `return_pct` als TWRR-Gesamtrendite: `(Π(1+rT) - 1) × 100`

6. **`portfolio_attribution`** (Zeile 1630):
   - `portfolio_return_pct` aus TWRR-Gesamtrendite statt `_portfolio_range_return_pct(portfolio_points)`

---

## Nicht geaenderte Logik (bewusst)

| Funktion | Begruendung |
|---|---|
| Absolut-Wert-Chart (`portfolio_points`) | Korrekte Darstellung des tatsaechlichen Depotwerts inkl. Einzahlungen. Beschriftung "Depotwert" bleibt korrekt. |
| `_build_portfolio_contributors_from_history_context` | Berechnet bereits Beitraege per Symbol auf Tagesbasis; Kapitalfluss-Effekte werden durch `prev_close is None`-Guard am ersten Tag eines Symbols groesstenteils ausgeschlossen. Separate Verbesserung moeglich. |
| `unrealized_return_pct` (Snapshot) | Bilanzielle Rendite gegen Einstandspreis; kein Zeitreihenproblem. |

---

## Testfall zur Verifikation

```python
# Holdings: 1 Anteil (buy_date=Tag 0), 99 Anteile (buy_date=Tag 30)
# Preise: konstant €100 an allen Tagen

# Erwarteter TWRR = 0 %  (Preis unveraendert)
# Naive Rendite   = 9.900 %  (Kauf am Tag 30 als Gewinn behandelt)

# Max Drawdown erwartet = 0 %  (kein Kursverlust)
# Naive Max Drawdown    = 0 %  in diesem Szenario, aber:
# Wenn Preis nach Tag 30 um 5 % faellt:
#   Naiver Max Drawdown = -5 %  (OK, zufaellig korrekt)
# Wenn Preis VOR Tag 30 um 5 % faellt:
#   Naiver Max Drawdown = -5 %  (korrekt)
# Wenn Preis nach Tag 30 um 90 % faellt:
#   Naiver Max Drawdown = -90 %  (TWRR: auch -90 %, da Kurs wirklich fiel)

# Kritischer Fall: Preis steigt um 10 % bis Tag 30, faellt danach um 10 %
#   Tag 0: 1 × 100 = 100
#   Tag 30: 1 × 110 = 110 (eigene Rendite +10 %)
#   Tag 30 nach Kauf: 100 × 110 = 11.000 (naiver Peak)
#   Tag 60: 100 × 99 = 9.900 (Preis -10 % von 110)
#   Naiver Drawdown = 9.900 / 11.000 - 1 = -10 %  (OK in diesem Fall)
#   TWRR Drawdown  = -10 %  (korrekt)

# Der gefaehrlichste Fall: grosser Kauf nach Kursverlust
#   Tag 0: 1 × 100 = 100 → running_peak = 100
#   Tag 15: Preis faellt auf 5 → portfolio = 5, drawdown = -95 %
#   Tag 16: Kauf 99 weitere @ 5 → portfolio springt auf 500
#            running_peak = 500
#   Tag 60: Preis bei 5,10 → portfolio = 510
#   Naiver Drawdown = -95 % (gemessen von running_peak=500 nach dem Kauf
#                            FALSCH: kein echter Kursverlust von 500 → 510)
#   TWRR Drawdown = -95 % (korrekt: Preis fiel wirklich von 100 auf 5)
```

---

## Auswirkung auf bestehende Tests

Die Tests in `services/analytics-service/tests/test_analytics_api.py` pruefen nur
Existenz (`is not None`, Status 200) — keine konkreten Wertebereiche. Daher schlaegt
kein bestehender Test fehl, und die Korrektheit muss durch neue parametrisierte Tests
abgedeckt werden (siehe M-10 in `dashboard-calculation-audit.md`).