# marketdata-service

Der Service wurde fachlich auf **FMP-only** umgestellt.

## Unterstützte Funktionen

- `GET /api/v1/marketdata/instruments/search?q=...&limit=...`
  - Nutzt FMP `GET /stable/search-name`.
- `GET /api/v1/marketdata/instruments/{symbol}/profile`
  - Nutzt FMP `GET /stable/profile`.
- `GET /api/v1/marketdata/instruments/{symbol}/financials?period=annual|quarterly`
  - Nutzt FMP `GET /stable/balance-sheet-statement`.
  - Income Statement und Cash Flow sind aktuell strukturell vorbereitet, aber noch ohne Upstream-Anbindung.

## Resilienz bei Mongo

- Profil-Cache kann in Mongo persistiert werden.
- Financials-Cache (symbol+period) kann in Mongo persistiert werden.
- Wenn Mongo deaktiviert oder nicht erreichbar ist, läuft der Service mit In-Memory-Fallback weiter.

## Health

- `GET /health`
- `GET /ready`

## Relevante Env-Variablen

- `FMP_BASE_URL` (default: `https://financialmodelingprep.com/stable`)
- `FMP_API_KEY`
- `FMP_REQUEST_TIMEOUT_SECONDS` (default: `8.0`)
- `FMP_REQUEST_RETRIES` (default: `2`)
- `FMP_REQUEST_BACKOFF_FACTOR` (default: `0.3`)
- `MARKETDATA_PROFILE_CACHE_COLLECTION` (default: `marketdata_profile_cache`)
- `MARKETDATA_FINANCIALS_CACHE_COLLECTION` (default: `marketdata_financials_cache`)
- `MARKETDATA_FINANCIALS_CACHE_TTL_SECONDS` (default: `3600`)
