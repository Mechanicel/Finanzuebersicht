# Marktdaten Financials Contract (Stand: April 2026)

## Ziel

Dieser Contract beschreibt den aktuell produktiv vorgesehenen Flow für:

- `GET /api/v1/app/marketdata/instruments/{symbol}/financials?period=annual|quarterly` (api-gateway)
- `GET /api/v1/marketdata/instruments/{symbol}/financials?period=annual|quarterly` (marketdata-service)

Der gateway bleibt für diesen Endpoint ein pass-through ohne Transformation des Payloads.

## End-to-End-Flow

1. Frontend übergibt `symbol` und `period` (`annual|quarterly`).
2. api-gateway reicht Request und Query-Parameter unverändert weiter.
3. marketdata-service validiert `period`.
4. marketdata-service lädt Cache-Eintrag `(symbol, period)`:
   - fresh: direkte Antwort aus Cache
   - stale/miss: FMP-Aufruf
5. FMP-Quelle:
   - `GET /stable/balance-sheet-statement`
   - period mapping:
     - `annual` -> `annual`
     - `quarterly` -> `quarter`
6. Response geht unverändert über gateway zurück zum Frontend.

## Response-Format

Top-Level:

- `symbol: string`
- `period: "annual" | "quarterly"`
- `currency: string | null`
- `statements`
  - `income_statement: []` (derzeit bewusst leer)
  - `balance_sheet: BalanceSheetRow[]`
  - `cash_flow: []` (derzeit bewusst leer)
- `derived`
  - `market_cap: number | null`
  - `beta: number | null`
- `meta`
  - `warnings: { code: string, message: string }[]`
  - `source: string`
  - `fetched_at: ISO-8601 string`

### BalanceSheetRow

Der Service liefert FMP-Felder und ergänzt normalisierte Felder für Frontend-Konsistenz:

- Originale FMP-Felder bleiben erhalten (z. B. `calendarYear`, `reportedCurrency`, `totalAssets`, `totalStockholdersEquity`).
- Ergänzte Felder:
  - `fiscalYear` (aus `calendarYear`)
  - `reportedCurrency` (sicher gestellt, inkl. snake_case fallback)
  - `totalEquity` (aus `totalStockholdersEquity`)
  - `totalDebt` (`shortTermDebt + longTermDebt`, falls verfügbar)
  - `netDebt` (`totalDebt - cashAndCashEquivalents`, falls verfügbar)

## Warnings

Aktuell relevante `meta.warnings`:

- `income_statement_not_integrated`
- `cash_flow_not_integrated`
- `balance_sheet_empty`
- `provider_error_fallback`

Damit wird offen kommuniziert, dass Income Statement/Cash Flow aktuell noch nicht angebunden sind.

## Cache-Verhalten

- Cache-Key: `(symbol, period)`
- Financials-TTL: `MARKETDATA_FINANCIALS_CACHE_TTL_SECONDS` (Default 3600)
- Bei Upstream-Fehler:
  - falls Cache vorhanden: stale Cache + Warning `provider_error_fallback`
  - sonst Fehlerantwort
- Repository-Auswahl:
  - MongoDB bei erfolgreicher Verbindung
  - In-Memory-Fallback bei deaktivierter oder nicht erreichbarer Mongo-Instanz

## Nicht-Scope (bewusst offen)

- Keine Integration von Income Statement und Cash Flow
- Keine neue Financials-Architektur oder Service-Aufteilung
- Keine Änderung am Endpoint-Pfad oder an der Grundstruktur des Payloads
