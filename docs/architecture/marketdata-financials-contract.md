# Markt­daten Financials Contract (v1)

## Zweck und Scope
Diese Spezifikation definiert den **verbindlichen Response-Vertrag** für
`GET /api/v1/marketdata/instruments/{symbol}/financials?period=annual|quarterly`.

Scope dieses Schritts:
- Implementierungsziel im `marketdata-service`.
- `api-gateway` bleibt reiner Pass-through für den Endpunkt.
- Frontend-Shape bleibt kompatibel mit `statements / derived / meta`.
- Erstintegration: **FMP Balance Sheet**.

Nicht-Scope:
- Keine Verlagerung in andere Services.
- Kein Frontend-Redesign.
- Keine Antwortstruktur-Änderung, die bestehende Frontend-Zugriffe bricht.

## Bestehender Call-Flow (Ist)
1. Frontend ruft `fetchInstrumentFinancials(symbol, period)` auf und sendet `period` als Query-Parameter (`annual|quarterly`).
2. `InstrumentAnalysisTabs.vue` liest ausschließlich die Anzahl von `statements.income_statement`, `statements.balance_sheet`, `statements.cash_flow`.
3. API-Gateway reicht den Call an den marketdata-service durch (`/app/... -> /api/v1/...`).
4. marketdata-service liefert aktuell Platzhalter: leere Statements + Warning `financials_provider_not_connected`.

## Finales Response-Format (Soll)
```json
{
  "symbol": "AAPL",
  "period": "annual",
  "currency": "USD",
  "statements": {
    "income_statement": [],
    "balance_sheet": [
      {
        "date": "2025-09-27",
        "fiscal_year": 2025,
        "fiscal_period": "FY",
        "reported_currency": "USD",
        "source": "fmp",
        "assets_total": 0,
        "assets_current": 0,
        "cash_and_equivalents": 0,
        "short_term_investments": 0,
        "net_receivables": 0,
        "inventory": 0,
        "other_current_assets": 0,
        "pp_and_e_net": 0,
        "goodwill": 0,
        "intangible_assets": 0,
        "other_non_current_assets": 0,
        "liabilities_total": 0,
        "liabilities_current": 0,
        "accounts_payable": 0,
        "short_term_debt": 0,
        "tax_payables": 0,
        "deferred_revenue": 0,
        "other_current_liabilities": 0,
        "long_term_debt": 0,
        "other_non_current_liabilities": 0,
        "equity_total": 0,
        "retained_earnings": 0,
        "accumulated_other_comprehensive_income": 0,
        "minority_interest": 0,
        "metadata": {
          "provider_statement_date": "2025-09-27",
          "accepted_date": "2025-10-30 06:00:00",
          "filling_date": "2025-10-30",
          "cik": "0000320193",
          "link": "https://...",
          "final_link": "https://..."
        }
      }
    ],
    "cash_flow": []
  },
  "derived": {
    "latest_balance_sheet_date": "2025-09-27",
    "latest_assets_total": 0,
    "latest_liabilities_total": 0,
    "latest_equity_total": 0,
    "latest_net_debt": 0,
    "latest_current_ratio": 0,
    "latest_debt_to_equity": 0,
    "latest_equity_ratio": 0,
    "series_count_balance_sheet": 1,
    "series_count_income_statement": 0,
    "series_count_cash_flow": 0
  },
  "meta": {
    "warnings": [],
    "cache": {
      "hit": true,
      "key": "financials:AAPL:annual:v1",
      "fetched_at": "2026-04-08T12:00:00Z",
      "stale_at": "2026-04-09T12:00:00Z",
      "provider": "fmp",
      "provider_latency_ms": 120
    }
  }
}
```

## Period-Mapping (verbindlich)
- API akzeptiert ausschließlich `annual` oder `quarterly`.
- Mapping auf FMP:
  - `annual` -> `period=annual`
  - `quarterly` -> `period=quarter`
- Response-Feld `period` bleibt exakt der API-Wert (`annual|quarterly`).
- Ungültige Werte -> `400 Bad Request` mit bestehendem Fehlerverhalten.

## Mapping: FMP `balance-sheet-statement` -> `statements.balance_sheet[]`
Jeder FMP-Datensatz wird in ein normalisiertes Objekt gemappt (neueste zuerst):

- `date` <- `date`
- `fiscal_year` <- `calendarYear` (int)
- `fiscal_period` <- `period` (`FY|Q1|Q2|Q3|Q4`)
- `reported_currency` <- `reportedCurrency`
- `source` <- fix `fmp`

**Assets**
- `assets_total` <- `totalAssets`
- `assets_current` <- `totalCurrentAssets`
- `cash_and_equivalents` <- `cashAndCashEquivalents`
- `short_term_investments` <- `shortTermInvestments`
- `net_receivables` <- `netReceivables`
- `inventory` <- `inventory`
- `other_current_assets` <- `otherCurrentAssets`
- `pp_and_e_net` <- `propertyPlantEquipmentNet`
- `goodwill` <- `goodwill`
- `intangible_assets` <- `intangibleAssets`
- `other_non_current_assets` <- `otherNonCurrentAssets`

**Liabilities**
- `liabilities_total` <- `totalLiabilities`
- `liabilities_current` <- `totalCurrentLiabilities`
- `accounts_payable` <- `accountPayables`
- `short_term_debt` <- `shortTermDebt`
- `tax_payables` <- `taxPayables`
- `deferred_revenue` <- `deferredRevenue`
- `other_current_liabilities` <- `otherCurrentLiabilities`
- `long_term_debt` <- `longTermDebt`
- `other_non_current_liabilities` <- `otherNonCurrentLiabilities`

**Equity**
- `equity_total` <- `totalStockholdersEquity`
- `retained_earnings` <- `retainedEarnings`
- `accumulated_other_comprehensive_income` <- `accumulatedOtherComprehensiveIncomeLoss`
- `minority_interest` <- `minorityInterest`

**Metadata pro Statement**
- `metadata.provider_statement_date` <- `date`
- `metadata.accepted_date` <- `acceptedDate`
- `metadata.filling_date` <- `fillingDate`
- `metadata.cik` <- `cik`
- `metadata.link` <- `link`
- `metadata.final_link` <- `finalLink`

Mapping-Regeln:
- Numerische Felder als `number | null` liefern.
- Nicht vorhandene Provider-Felder -> `null`.
- Sortierung absteigend nach `date` (neuester Eintrag zuerst).

## Behandlung nicht integrierter Statements (verbindlich)
- `statements.income_statement`: bis zur Implementierung immer `[]`.
- `statements.cash_flow`: bis zur Implementierung immer `[]`.
- Keine Fake-Daten, keine strukturell abweichenden Objekte.

## Erlaubte `meta.warnings`
Zulässig (Whitelist):
- `financials_balance_sheet_partial` (einzelne Felder fehlen, aber verwertbare Daten vorhanden)
- `financials_income_statement_not_integrated`
- `financials_cash_flow_not_integrated`
- `financials_provider_unavailable` (temporärer Upstream-Fehler)
- `financials_data_not_found` (Symbol vorhanden, aber keine Financials beim Provider)
- `financials_cache_stale` (stale-while-revalidate geliefert)

Nicht mehr zulässig, sobald Balance Sheet live ist:
- `financials_provider_not_connected`

## Derived-Felder (Backend liefert)
Pflichtfelder in `derived`:
- `latest_balance_sheet_date`
- `latest_assets_total`
- `latest_liabilities_total`
- `latest_equity_total`
- `latest_net_debt` = `long_term_debt + short_term_debt - cash_and_equivalents`
- `latest_current_ratio` = `assets_current / liabilities_current` (nur falls Nenner > 0, sonst `null`)
- `latest_debt_to_equity` = `(long_term_debt + short_term_debt) / equity_total` (falls möglich)
- `latest_equity_ratio` = `equity_total / assets_total` (falls möglich)
- `series_count_balance_sheet`
- `series_count_income_statement`
- `series_count_cash_flow`

Regel: Derived-Werte werden ausschließlich aus dem jeweils **neuesten** Balance-Sheet-Eintrag berechnet.

## Cache-Metadaten in `meta.cache`
Pflichtfelder:
- `hit` (`boolean`)
- `key` (`string`)
- `fetched_at` (ISO-8601 UTC)
- `stale_at` (ISO-8601 UTC)
- `provider` (aktuell `fmp`)
- `provider_latency_ms` (`number | null`)

Empfohlene TTL:
- `annual`: 24h
- `quarterly`: 12h

## Kompatibilitäts- und Rollout-Regeln
- Top-Level-Struktur bleibt: `symbol`, `period`, `currency`, `statements`, `derived`, `meta`.
- `statements.*` bleiben Arrays (auch wenn leer).
- Keine Breaking Changes am Endpoint-Pfad oder Query-Schema.
- Income/Cash-Flow werden später im selben Contract ergänzt (gleiche Strukturphilosophie, keine Sonderwege).
