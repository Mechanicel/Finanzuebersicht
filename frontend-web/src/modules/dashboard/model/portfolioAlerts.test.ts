import { describe, expect, it } from 'vitest'
import {
  buildPortfolioAlerts,
  DEFAULT_PORTFOLIO_ALERT_RULES,
  type PortfolioAlertSources
} from '@/modules/dashboard/model/portfolioAlerts'
import type {
  PortfolioContributorsReadModel,
  PortfolioDataCoverageReadModel,
  PortfolioRiskReadModel,
  PortfolioSummaryReadModel
} from '@/shared/model/types'

function summary(overrides: Partial<PortfolioSummaryReadModel> = {}): PortfolioSummaryReadModel {
  return {
    person_id: 'person-1',
    as_of: '2026-04-10',
    currency: 'EUR',
    market_value: 100_000,
    invested_value: 92_000,
    unrealized_pnl: 8_000,
    unrealized_return_pct: 8.7,
    portfolios_count: 1,
    holdings_count: 8,
    top_position_weight: 0.22,
    top3_weight: 0.54,
    meta: {},
    ...overrides
  }
}

function risk(overrides: Partial<PortfolioRiskReadModel> = {}): PortfolioRiskReadModel {
  return {
    person_id: 'person-1',
    as_of: '2026-04-10',
    range: '3m',
    range_label: '3 Monate',
    benchmark_symbol: 'SPY',
    annualized_volatility: 0.14,
    annualized_tracking_error: 0.04,
    max_drawdown: -0.06,
    top_position_weight: 0.22,
    top3_weight: 0.54,
    meta: {},
    ...overrides
  }
}

function coverage(overrides: Partial<PortfolioDataCoverageReadModel> = {}): PortfolioDataCoverageReadModel {
  return {
    person_id: 'person-1',
    as_of: '2026-04-10',
    total_holdings: 8,
    missing_prices: 0,
    missing_sectors: 0,
    missing_countries: 0,
    missing_currencies: 0,
    fallback_acquisition_prices: 0,
    holdings_with_marketdata_warnings: 0,
    warnings: [],
    meta: {},
    ...overrides
  }
}

function contributors(overrides: Partial<PortfolioContributorsReadModel> = {}): PortfolioContributorsReadModel {
  return {
    person_id: 'person-1',
    as_of: '2026-04-10',
    range: '3m',
    range_label: '3 Monate',
    total_contribution_pct_points: 4.2,
    warnings: [],
    top_contributors: [],
    top_detractors: [],
    meta: {},
    ...overrides
  }
}

function sources(overrides: PortfolioAlertSources = {}): PortfolioAlertSources {
  return {
    summary: summary(),
    risk: risk(),
    coverage: coverage(),
    contributors: contributors(),
    ...overrides
  }
}

function alertIds(alertSources: PortfolioAlertSources): string[] {
  return buildPortfolioAlerts(alertSources).map((alert) => alert.id)
}

describe('portfolio alert rules', () => {
  it('keeps one-holding portfolios out of concentration breaches', () => {
    const alerts = buildPortfolioAlerts(
      sources({
        summary: summary({ holdings_count: 1, top_position_weight: 1, top3_weight: 1 }),
        risk: risk({ top_position_weight: 1, top3_weight: 1 }),
        coverage: coverage({ total_holdings: 1 })
      })
    )

    expect(alerts.map((alert) => alert.id)).toEqual(['small-portfolio'])
    expect(alerts[0]).toMatchObject({
      severity: 'info',
      sourceKey: 'concentration',
      actionHint: 'Konzentration pruefen'
    })
  })

  it('derives concentration alerts for normal concentrated portfolios', () => {
    const alerts = buildPortfolioAlerts(
      sources({
        summary: summary({ holdings_count: 8, top_position_weight: 0.52, top3_weight: 0.82 }),
        risk: risk({ top_position_weight: 0.52, top3_weight: 0.82 })
      })
    )

    expect(alerts.map((alert) => alert.id)).toEqual(['top-position-concentration', 'top3-concentration'])
    expect(alerts.map((alert) => alert.severity)).toEqual(['kritisch', 'kritisch'])
    expect(alerts[0].detail).toContain('bei 8 Holdings')
  })

  it('uses configurable concentration thresholds', () => {
    const baseSources = sources({
      summary: summary({ holdings_count: 8, top_position_weight: 0.32, top3_weight: 0.54 }),
      risk: risk({ top_position_weight: 0.32, top3_weight: 0.54 })
    })

    expect(alertIds(baseSources)).toEqual([])
    expect(
      buildPortfolioAlerts(baseSources, {
        config: {
          concentration: {
            topPosition: { warning: 0.3, critical: 0.45 },
            top3: DEFAULT_PORTFOLIO_ALERT_RULES.concentration.top3
          }
        }
      }).map((alert) => alert.id)
    ).toEqual(['top-position-concentration'])
  })

  it('derives risk alerts for volatile portfolios', () => {
    const alerts = buildPortfolioAlerts(
      sources({
        risk: risk({
          annualized_volatility: 0.34,
          annualized_tracking_error: 0.13,
          max_drawdown: -0.28
        })
      })
    )

    expect(alerts.map((alert) => alert.id)).toEqual(['high-volatility', 'high-tracking-error', 'max-drawdown'])
    expect(alerts.map((alert) => alert.severity)).toEqual(['kritisch', 'kritisch', 'kritisch'])
    expect(alerts.find((alert) => alert.id === 'high-tracking-error')?.actionHint).toBe(
      'Benchmark-Abweichung pruefen'
    )
  })

  it('derives coverage alerts for price and classification gaps', () => {
    const alerts = buildPortfolioAlerts(
      sources({
        coverage: coverage({
          missing_prices: 2,
          missing_sectors: 1,
          missing_countries: 1,
          fallback_acquisition_prices: 1,
          warnings: ['missing_sector_data']
        })
      })
    )

    expect(alerts.map((alert) => alert.id)).toEqual(['missing-prices', 'coverage-quality-warnings'])
    expect(alerts[0]).toMatchObject({ severity: 'kritisch', sourceKey: 'coverage' })
    expect(alerts[1].detail).toBe('3 Datenluecken, 1 Hinweise')
  })

  it('surfaces missing benchmark data and suppresses tracking-error breaches', () => {
    const alerts = buildPortfolioAlerts(
      sources({
        risk: risk({
          benchmark_symbol: null,
          annualized_tracking_error: 0.2
        })
      })
    )

    expect(alerts.map((alert) => alert.id)).toEqual(['benchmark-missing'])
    expect(alerts[0]).toMatchObject({
      severity: 'info',
      sourceKey: 'risk',
      actionHint: 'Benchmark setzen'
    })
    expect(alerts.map((alert) => alert.id)).not.toContain('high-tracking-error')
  })
})
