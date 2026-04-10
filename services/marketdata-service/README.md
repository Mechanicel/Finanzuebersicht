# marketdata-service

## Fokus dieses Services

Der Service aggregiert Marktdaten aus externen Providern und stellt sie über stabile API-Endpunkte bereit.

- **FMP**: Instrumentensuche, Profile, Financials (Balance Sheet)
- **yfinance**: aktuelle Preise und Historien
- **Cache-Layer**: MongoDB (wenn verfügbar) mit In-Memory-Fallback

## Financials-Flow (Frontend -> Gateway -> marketdata-service)

- Frontend ruft auf:  
  `GET /api/v1/app/marketdata/instruments/{symbol}/financials?period=annual|quarterly`
- api-gateway reicht den Call transparent an marketdata-service durch.
- marketdata-service ruft FMP auf:  
  `GET /stable/balance-sheet-statement?symbol=...&period=annual|quarter`
- Antwortshape bleibt stabil:
  - `symbol`, `period`, `currency`
  - `statements.income_statement` (aktuell `[]`)
  - `statements.balance_sheet` (FMP-Balance-Sheet + normalisierte Hilfsfelder)
  - `statements.cash_flow` (aktuell `[]`)
  - `derived.market_cap`, `derived.beta`
  - `meta.warnings`, `meta.source`, `meta.fetched_at`

### Period-Handling

- Erlaubt: `annual`, `quarterly`
- Mapping zu FMP:
  - `annual` -> `annual`
  - `quarterly` -> `quarter`
- Ungültige Werte führen zu `400 Bad Request`.

### Warnings im Financials-Endpoint

- `income_statement_not_integrated`
- `cash_flow_not_integrated`
- `balance_sheet_empty` (Provider liefert keine Datensätze)
- `provider_error_fallback` (stale Cache wird bei Upstream-Fehler geliefert)

## Cache-Verhalten

- **Profile**: TTL-gesteuert (Default `300s`)
- **Financials**: TTL-gesteuert pro `(symbol, period)` (Default `3600s`)
- **Current Price** und **History**: SWR-Verhalten mit Seed/Enrich-Strategie
- Wenn Mongo deaktiviert oder nicht erreichbar ist:
  - automatische Degradierung auf In-Memory-Repositories
  - API bleibt verfügbar, Cache ist dann pro Prozess flüchtig

## Relevante Env-Variablen

- `FMP_BASE_URL` (Default: `https://financialmodelingprep.com/stable`)
- `FMP_API_KEY`
- `FMP_REQUEST_TIMEOUT_SECONDS` (Default: `8.0`)
- `FMP_REQUEST_RETRIES` (Default: `2`)
- `FMP_REQUEST_BACKOFF_FACTOR` (Default: `0.3`)
- `MARKETDATA_MONGO_ENABLED` (Default: `true`)
- `MARKETDATA_MONGO_SERVER_SELECTION_TIMEOUT_MS` (Default: `1000`)
- `MARKETDATA_PROFILE_CACHE_COLLECTION` (Default: `marketdata_profile_cache`)
- `MARKETDATA_CURRENT_PRICE_CACHE_COLLECTION` (Default: `marketdata_current_price_cache`)
- `MARKETDATA_PRICE_HISTORY_CACHE_COLLECTION` (Default: `marketdata_price_history_cache`)
- `MARKETDATA_FINANCIALS_CACHE_COLLECTION` (Default: `marketdata_financials_cache`)
- `MARKETDATA_FINANCIALS_CACHE_TTL_SECONDS` (Default: `3600`)

## Health

- `GET /health`
- `GET /ready`
