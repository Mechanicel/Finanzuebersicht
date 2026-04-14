# Portfolio Dashboard Kennzahlen-Semantik

Diese Notiz dokumentiert die fachliche Trennung der Kennzahlen für Portfolio-Dashboard-Endpunkte.

## Kategorien

### 1) Snapshot / As-of Kennzahlen
- Endpunkte: `portfolio-summary`, `portfolio-holdings.summary`.
- Zeitbezug: `as_of` (Stichtag).
- Kennzeichnung: `summary_kind = "snapshot"`.
- Werte:
  - `market_value`
  - `invested_value`
  - `portfolios_count`
  - `holdings_count`
  - Konzentrationswerte wie `top_position_weight`, `top3_weight`.

### 2) Since-cost-basis / unrealized Kennzahlen
- Endpunkte: `portfolio-summary`, `portfolio-holdings.items`.
- Kennzeichnung: `return_basis = "since_cost_basis"` auf Summary-Ebene.
- Werte:
  - `unrealized_pnl`
  - `unrealized_return_pct`
- Bedeutung: Nicht Zeitraum-Performance, sondern Bewertung relativ zum Einstand (Kostenbasis).

### 3) Zeitraum-Kennzahlen (gewählter Range)
- Endpunkte: `portfolio-performance`, `portfolio-contributors`, `portfolio-risk`.
- Zeitbezug: `range` plus lesbares `range_label`.
- `portfolio-performance.summary`:
  - `summary_kind = "range"`
  - `return_basis = "range_start_value"`
  - `start_value`, `end_value`, `absolute_change`, `return_pct`
- `portfolio-contributors`:
  - `summary_kind = "range"`
  - `return_basis = "range_contribution"`
  - `methodology` beschreibt Berechnungsansatz.

### 4) Benchmark-relative Kennzahlen
- Endpunkt: `portfolio-risk` (und Benchmark-Referenz in `portfolio-performance`).
- Kennzeichnung in Risk:
  - `benchmark_symbol`
  - `benchmark_relation = "relative_to_benchmark"`
  - `methodology = "daily_returns_on_range"`
- Beispielwerte mit Benchmark-Bezug:
  - `beta`, `correlation`, `tracking_error`, `annualized_tracking_error`, `information_ratio`, `active_return`.

## Prozent vs. Prozentpunkte
- **Prozent (%)**: Verhältnis zur jeweiligen Basis, z. B. `return_pct`, `unrealized_return_pct`, `contribution_return`.
- **Prozentpunkte (pp)**: additive Beitragsdarstellung, z. B. `contribution_pct_points`, `total_contribution_pct_points`.

## Migrationsprinzip
Die bestehenden Felder bleiben erhalten; neue Metadatenfelder machen die Semantik explizit (additive, rückwärtskompatible Erweiterung).
