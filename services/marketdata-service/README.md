# marketdata-service (FastAPI)

Neu aufgesetzter Market-Data-Service für die Zielarchitektur mit **api-gateway** und **Vue-Frontend**.

## Status

- Flask-Legacy ist vollständig ersetzt durch FastAPI-Struktur unter `services/marketdata-service/app`.
- Einheitliche Versionierung unter `/api/v1/marketdata/...`.
- Provider-Abstraktion ist vorbereitet (`MarketDataProvider`), aktuell mit In-Memory-Provider.
- Service-Layer (`MarketDataService`) kapselt Fachlogik.
- Caching ist vorbereitet (TTL-In-Memory-Cache, konfigurierbar).
- Strukturierte Fehlerantworten (`not_found`, `bad_request`, `validation_error`).

## Neue Endpunkte (gültig)

Alle Endpunkte liegen unter ` /api/v1/marketdata `.

### Instrumente

- `GET /instruments/{symbol}/summary`
  - Liefert instrument summary (company + trading metadata).
- `GET /instruments/{symbol}/prices?range=1M|3M|6M|1Y|3Y|5Y&interval=1d|1wk|1mo`
  - Liefert price series.
- `GET /instruments/{symbol}/blocks`
  - Liefert Snapshot + Fundamentals + Metrics + Risk in einem Block.
- `GET /instruments/{symbol}/full`
  - Liefert vollständige instrument data (summary + alle Blöcke).

### Benchmarks

- `GET /benchmarks/options`
  - Liefert benchmark options (Katalog für UI-Selects).
- `GET /benchmarks/search?q=...`
  - Liefert Trefferliste (benchmark search).

### Vergleichszeitreihen

- `POST /comparisons/series`
  - Request:
    - `symbols: string[]`
    - `benchmark_id?: string`
    - `range`, `interval`
  - Response: konsolidierte comparison series.

## Response-Modelle (gateway- & vue-freundlich)

Alle Responses folgen einem einheitlichen Wrapper:

```json
{
  "data": { "...": "..." },
  "request_id": "...",
  "correlation_id": "..."
}
```

### 1) instrument summary

`GET /instruments/{symbol}/summary`

```json
{
  "data": {
    "symbol": "AAPL",
    "isin": "US0378331005",
    "company_name": "Apple Inc.",
    "exchange": "NASDAQ",
    "currency": "USD",
    "country": "US",
    "sector": "Technology",
    "industry": "Consumer Electronics"
  }
}
```

### 2) price series

`GET /instruments/{symbol}/prices`

```json
{
  "data": {
    "symbol": "AAPL",
    "currency": "USD",
    "range": "1Y",
    "interval": "1d",
    "points": [
      { "date": "2026-03-01", "close": 188.2 }
    ]
  }
}
```

### 3) benchmark options

`GET /benchmarks/options`

```json
{
  "data": {
    "items": [
      {
        "benchmark_id": "sp500",
        "symbol": "^GSPC",
        "label": "S&P 500",
        "region": "US",
        "asset_class": "equity"
      }
    ],
    "total": 1
  }
}
```

### 4) comparison series

`POST /comparisons/series`

```json
{
  "data": {
    "range": "1M",
    "interval": "1d",
    "series": [
      {
        "series_id": "AAPL",
        "label": "Apple Inc.",
        "kind": "instrument",
        "currency": "USD",
        "points": [{ "date": "2026-03-01", "value": 188.2 }]
      },
      {
        "series_id": "sp500",
        "label": "S&P 500",
        "kind": "benchmark",
        "currency": "USD",
        "points": [{ "date": "2026-03-01", "value": 5070.1 }]
      }
    ]
  }
}
```

### 5) fundamentals/risk blocks

`GET /instruments/{symbol}/blocks`

```json
{
  "data": {
    "symbol": "AAPL",
    "snapshot": { "last_price": 189.32, "change_1d_pct": 1.21, "volume": 52310200 },
    "fundamentals": {
      "market_cap": 2900000000000,
      "pe_ratio": 29.1,
      "dividend_yield": 0.45,
      "revenue_growth_yoy": 0.071
    },
    "metrics": { "sma_50": 186.11, "sma_200": 178.44, "rsi_14": 56.2 },
    "risk": {
      "beta": 1.08,
      "volatility_30d": 0.22,
      "max_drawdown_1y": -0.17,
      "value_at_risk_95_1d": -0.026
    }
  }
}
```

## Bewusst entfernte Altpfade / Legacy-Endpunkte

Die folgenden Legacy-Muster gelten als **entfallen** und sollen nicht mehr durch das Gateway genutzt werden:

- Nicht-versionierte Flask-ähnliche Pfade wie:
  - `/price`
  - `/company`
  - `/snapshot`
  - `/full`
  - `/fundamentals`
  - `/metrics`
  - `/risk`
  - `/benchmarks`
  - `/benchmark-search`
  - `/comparison`
- Übergangs-/Platzhalterpfad:
  - `/api/v1/marketdata_service`

> Nutzung ab sofort ausschließlich über `/api/v1/marketdata/...`.

## Konfiguration

Umgebungsvariablen:

- `CACHE_ENABLED` (default `true`)
- `CACHE_TTL_SECONDS` (default `120`)

## Start

```bash
uv run uvicorn app.main:app --reload --port 8005
```

## Tests

```bash
uv run pytest services/marketdata-service/tests -q
```
