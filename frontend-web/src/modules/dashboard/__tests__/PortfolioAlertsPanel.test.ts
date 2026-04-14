// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PortfolioAlertsPanel from '@/modules/dashboard/components/PortfolioAlertsPanel.vue'
import type {
  PortfolioContributorsReadModel,
  PortfolioDataCoverageReadModel,
  PortfolioRiskReadModel,
  PortfolioSummaryReadModel
} from '@/shared/model/types'

function buildSummary(overrides: Partial<PortfolioSummaryReadModel> = {}): PortfolioSummaryReadModel {
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

function buildRisk(overrides: Partial<PortfolioRiskReadModel> = {}): PortfolioRiskReadModel {
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

function buildCoverage(overrides: Partial<PortfolioDataCoverageReadModel> = {}): PortfolioDataCoverageReadModel {
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

function buildContributors(overrides: Partial<PortfolioContributorsReadModel> = {}): PortfolioContributorsReadModel {
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

function mountPanel(overrides: {
  summary?: PortfolioSummaryReadModel | null
  risk?: PortfolioRiskReadModel | null
  coverage?: PortfolioDataCoverageReadModel | null
  contributors?: PortfolioContributorsReadModel | null
  maxAlerts?: number
} = {}) {
  return mount(PortfolioAlertsPanel, {
    props: {
      summary: buildSummary(),
      risk: buildRisk(),
      coverage: buildCoverage(),
      contributors: buildContributors(),
      ...overrides
    }
  })
}

function alertIds(wrapper: ReturnType<typeof mountPanel>): string[] {
  return wrapper.findAll('[data-test="portfolio-alert"]').map((alert) => alert.attributes('data-alert-id') ?? '')
}

describe('PortfolioAlertsPanel', () => {
  it('renders a compact empty state when no alerts are derived', () => {
    const wrapper = mountPanel()

    expect(wrapper.get('[data-test="portfolio-alert-count"]').text()).toBe('0 Alerts')
    expect(wrapper.find('[data-test="portfolio-alert-list"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="portfolio-alert-source-board"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="portfolio-alert-more"]').exists()).toBe(false)
    expect(wrapper.findAll('[data-test="portfolio-alert"]')).toHaveLength(0)
    expect(wrapper.get('[data-test="portfolio-alert-empty"]').text()).toContain('Keine Alerts')
  })

  it('renders concentration alerts with source and action hints', () => {
    const wrapper = mountPanel({
      summary: buildSummary({ holdings_count: 8, top_position_weight: 0.42, top3_weight: 0.7 }),
      risk: buildRisk({ top_position_weight: 0.42, top3_weight: 0.7 })
    })

    expect(alertIds(wrapper)).toEqual(['top-position-concentration', 'top3-concentration'])
    expect(wrapper.findAll('[data-test="portfolio-alert"]')).toHaveLength(2)
    expect(wrapper.get('[data-alert-id="top-position-concentration"]').attributes('data-source')).toBe('concentration')
    expect(wrapper.get('[data-source="concentration"]').text()).toContain('Konzentration 2')
    expect(wrapper.text()).toContain('Konzentration pruefen')
    expect(wrapper.find('[data-test="portfolio-alert-more"]').exists()).toBe(false)
  })

  it('combines coverage and risk alerts and summarizes secondary hints', () => {
    const wrapper = mountPanel({
      summary: buildSummary({ top_position_weight: 0.2, top3_weight: 0.48 }),
      risk: buildRisk({
        annualized_volatility: 0.34,
        annualized_tracking_error: 0.13,
        max_drawdown: -0.28,
        top_position_weight: 0.2,
        top3_weight: 0.48
      }),
      coverage: buildCoverage({
        missing_prices: 2,
        missing_sectors: 1,
        fallback_acquisition_prices: 1,
        warnings: ['missing_sector_data']
      })
    })

    expect(alertIds(wrapper)).toEqual([
      'missing-prices',
      'high-volatility',
      'high-tracking-error'
    ])
    expect(wrapper.findAll('[data-test="portfolio-alert"]')).toHaveLength(3)
    expect(wrapper.get('[data-test="portfolio-alert-count"]').text()).toBe('3 von 5 sichtbar')
    expect(wrapper.get('[data-alert-id="missing-prices"]').attributes('data-severity')).toBe('kritisch')
    expect(wrapper.get('[data-alert-id="missing-prices"]').attributes('data-source')).toBe('coverage')
    expect(wrapper.get('[data-alert-id="high-tracking-error"]').text()).toContain('Benchmark-Abweichung pruefen')
    expect(wrapper.get('[data-source="coverage"]').text()).toContain('Coverage 2')
    expect(wrapper.get('[data-source="risk"]').text()).toContain('Risk 3')
    expect(wrapper.get('[data-test="portfolio-alert-more"]').text()).toContain('weitere Hinweise')
    expect(wrapper.get('[data-test="portfolio-alert-more"]').text()).toContain('2')
    expect(wrapper.get('[data-test="portfolio-alert-more"]').text()).toContain('1 kritisch')
    expect(wrapper.get('[data-test="portfolio-alert-more"]').text()).toContain('1 warnung')
  })

  it('does not turn mathematically concentrated small portfolios into concentration breaches', () => {
    const wrapper = mountPanel({
      summary: buildSummary({ holdings_count: 2, top_position_weight: 0.76, top3_weight: 1 }),
      risk: buildRisk({ top_position_weight: 0.76, top3_weight: 1 }),
      coverage: buildCoverage({ total_holdings: 2 })
    })

    expect(alertIds(wrapper)).toEqual(['small-portfolio'])
    expect(wrapper.get('[data-alert-id="small-portfolio"]').attributes('data-severity')).toBe('info')
    expect(wrapper.get('[data-alert-id="small-portfolio"]').attributes('data-source')).toBe('concentration')
    expect(wrapper.text()).toContain('Kleines Portfolio')
    expect(wrapper.text()).toContain('1 Alert')
    expect(wrapper.find('[data-test="portfolio-alert-more"]').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Top-Position kritisch')
    expect(wrapper.text()).not.toContain('Top-3-Konzentration kritisch')
  })

  it('respects the alert limit while keeping only three primary alerts visible', () => {
    const wrapper = mountPanel({
      maxAlerts: 4,
      summary: buildSummary({ top_position_weight: 0.2, top3_weight: 0.48 }),
      risk: buildRisk({
        annualized_volatility: 0.34,
        annualized_tracking_error: 0.13,
        max_drawdown: -0.28,
        top_position_weight: 0.2,
        top3_weight: 0.48
      }),
      coverage: buildCoverage({
        missing_prices: 2,
        missing_sectors: 1,
        fallback_acquisition_prices: 1,
        warnings: ['missing_sector_data']
      }),
      contributors: buildContributors({
        total_contribution_pct_points: -12,
        warnings: ['partial_period']
      })
    })

    expect(alertIds(wrapper)).toEqual(['missing-prices', 'high-volatility', 'high-tracking-error'])
    expect(wrapper.get('[data-test="portfolio-alert-count"]').text()).toBe('3 von 4 sichtbar')
    expect(wrapper.get('[data-test="portfolio-alert-more"]').text()).toContain('1 kritisch')
    expect(wrapper.text()).not.toContain('Datenqualitaet pruefen')
    expect(wrapper.text()).not.toContain('Contributor-Hinweise vorhanden')
  })
})
