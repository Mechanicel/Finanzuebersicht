# Portfolio Attribution V1

## Contract

`PortfolioAttributionReadModel` is an additive analytics contract for a selected portfolio range. It is served additively via:

- analytics-service: `GET /api/v1/analytics/persons/{person_id}/portfolio-attribution?range=...`
- api-gateway: `GET /api/v1/app/persons/{person_id}/portfolio-attribution?range=...`

The payload includes `person_id`, `as_of`, `range`, `range_label`, `benchmark_symbol`, explicit `methodology`, a `summary`, and attribution arrays for:

- `by_position`
- `by_sector`
- `by_country`
- `by_currency`

The same read model is also included as the optional `attribution` section in `PortfolioDashboardReadModel` so the dashboard bootstrap can consume it without an additional request. The standalone endpoint remains the stable contract boundary for clients that want to load or refresh attribution independently.

Each attribution item contains at minimum `label` and `contribution_pct_points`. Where available it also includes `return_pct`, `weight`, `market_value`, `direction`, and for positions `symbol`.

## Implemented Methodology

V1 implements `holdings_based_static_return_contribution`.

The calculation uses the current portfolio holdings snapshot, keeps quantities static, and applies instrument price history over the selected range. For each adjacent history date pair, the service calculates:

`previous_position_value / previous_portfolio_value * period_asset_return`

The result is accumulated in percentage points. Position-level contributions are then summed into sector, country, and currency attribution buckets.

The methodology is intentionally visible in the API:

- label: `Holdings-based static return contribution`
- contribution basis: `return contribution over selected range`
- unit: additive percentage points

## Approximation Boundaries

This is not transaction-level attribution. It does not model buys, sells, dividends, cash flows, fees, taxes, FX conversion effects, or intra-period weight drift beyond daily price movements against static quantities.

Position contributions are additive within the implemented calculation. Sector, country, and currency buckets are sums of the same position contributions and therefore add up to the same total when classifications are present. `UNKNOWN` buckets keep missing classification visible instead of silently dropping it.

The attribution total can differ from the geometric portfolio range return shown by the performance panel. The contract exposes this as `summary.residual_pct_points`:

- `portfolio_return_pct`: range return from portfolio start and end values
- `total_contribution_pct_points`: sum of additive attribution items
- `residual_pct_points`: difference between both measures

This residual is expected for multi-period arithmetic contribution and for missing or incomplete history. Missing history is reported through `warnings` and reflected in `covered_positions` / `unattributed_positions`.
