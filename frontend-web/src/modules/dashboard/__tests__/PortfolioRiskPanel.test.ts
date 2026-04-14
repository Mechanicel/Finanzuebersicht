// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import PortfolioRiskPanel from '@/modules/dashboard/components/PortfolioRiskPanel.vue'
import type { PortfolioRiskReadModel } from '@/shared/model/types'

function buildRisk(overrides: Partial<PortfolioRiskReadModel> = {}): PortfolioRiskReadModel {
  return {
    person_id: 'person-1',
    as_of: '2026-04-10',
    range: '3m',
    range_label: '3 Monate',
    methodology: 'daily_returns_on_range',
    benchmark_relation: 'relative_to_benchmark',
    benchmark_symbol: 'SPY',
    meta: {},
    ...overrides
  }
}

function mountPanel(risk: PortfolioRiskReadModel) {
  return mount(PortfolioRiskPanel, {
    props: { risk }
  })
}

function normalizedText(value: string): string {
  return value.replace(/\u00a0/g, ' ')
}

describe('PortfolioRiskPanel', () => {
  it('renders a fully populated model as a four-block metric board', () => {
    const wrapper = mountPanel(
      buildRisk({
        portfolio_volatility: 0.015,
        max_drawdown: -0.16,
        correlation: 0.88,
        beta: 1.05,
        tracking_error: 0.005,
        annualized_volatility: 0.24,
        annualized_tracking_error: 0.08,
        sharpe_ratio: 1.24,
        sortino_ratio: 1.78,
        information_ratio: 0.71,
        active_return: 0.052,
        best_day_return: 0.024,
        worst_day_return: -0.031,
        aligned_points: 42,
        top_position_weight: 0.61,
        top3_weight: 0.87,
        concentration_note: 'high_top3_concentration'
      })
    )

    expect(wrapper.find('[data-testid="risk-metric-board"]').exists()).toBe(true)
    expect(wrapper.findAll('[data-testid^="risk-block-"]')).toHaveLength(4)
    expect(wrapper.findAll('.metric-card--primary')).toHaveLength(4)

    expect(normalizedText(wrapper.get('[data-testid="risk-primary-annualized-volatility"]').text())).toContain('24,00 %')
    expect(normalizedText(wrapper.get('[data-testid="risk-primary-max-drawdown"]').text())).toContain('-16,00 %')
    expect(wrapper.get('[data-testid="risk-primary-max-drawdown"] .metric-value').classes()).toContain('negative')
    expect(wrapper.get('[data-testid="risk-primary-sharpe-ratio"] .metric-value').classes()).toContain('positive')
    expect(wrapper.get('[data-testid="risk-primary-sortino-ratio"]').text()).toContain('1,78')

    expect(normalizedText(wrapper.get('[data-testid="risk-metric-annualized-tracking-error"]').text())).toContain('8,00 %')
    expect(wrapper.get('[data-testid="risk-metric-information-ratio"]').text()).toContain('0,71')
    expect(wrapper.get('[data-testid="risk-metric-active-return"]').text()).toContain('+5,20 pp')
    expect(wrapper.get('[data-testid="risk-metric-active-return"] .metric-value').classes()).toContain('positive')
    expect(wrapper.get('[data-testid="risk-metric-aligned-points"]').text()).toContain('42')

    expect(normalizedText(wrapper.get('[data-testid="risk-metric-best-day-return"]').text())).toContain('+2,40 %')
    expect(normalizedText(wrapper.get('[data-testid="risk-metric-worst-day-return"]').text())).toContain('-3,10 %')
    expect(wrapper.get('[data-testid="risk-metric-worst-day-return"] .metric-value').classes()).toContain('negative')
    expect(normalizedText(wrapper.get('[data-testid="risk-metric-top-position-weight"]').text())).toContain('61,00 %')
    expect(wrapper.get('[data-testid="risk-metric-concentration-note"]').text()).toContain('Top-3')
  })

  it('keeps the grid stable when values are partially missing', () => {
    const wrapper = mountPanel(
      buildRisk({
        annualized_volatility: null,
        max_drawdown: null,
        sharpe_ratio: null,
        sortino_ratio: null,
        portfolio_volatility: 0.02,
        top_position_weight: 0,
        top3_weight: 0.8,
        benchmark_symbol: null,
        concentration_note: null
      })
    )

    const text = normalizedText(wrapper.text())
    expect(wrapper.findAll('.metric-card--primary')).toHaveLength(4)
    expect(wrapper.findAll('.metric-card--primary.is-missing')).toHaveLength(4)
    expect(normalizedText(wrapper.get('[data-testid="risk-primary-annualized-volatility"]').text())).toContain('n/a')
    expect(wrapper.get('[data-testid="risk-primary-sharpe-ratio"]').text()).toContain('n/a')
    expect(normalizedText(wrapper.get('[data-testid="risk-metric-portfolio-volatility"]').text())).toContain('2,00 %')
    expect(normalizedText(wrapper.get('[data-testid="risk-metric-top-position-weight"]').text())).toContain('0,00 %')
    expect(normalizedText(wrapper.get('[data-testid="risk-metric-top3-weight"]').text())).toContain('80,00 %')

    expect(wrapper.get('[data-testid="risk-benchmark-empty"]').text()).toContain('Keine Benchmark-Daten')
    expect(wrapper.find('[data-testid="risk-metric-information-ratio"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="risk-metric-active-return"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="risk-block-performance"]').exists()).toBe(false)
    expect(text).not.toContain('Performance-Verhalten')
  })

  it('marks critical concentration without changing the reported metrics', () => {
    const wrapper = mountPanel(
      buildRisk({
        annualized_volatility: 0.18,
        max_drawdown: -0.22,
        sharpe_ratio: -0.15,
        sortino_ratio: -0.2,
        top_position_weight: 0.64,
        top3_weight: 0.91,
        concentration_note: 'single_position_dominates'
      })
    )

    expect(wrapper.get('[data-testid="risk-block-concentration"]').classes()).toContain('metric-block--critical')
    expect(wrapper.get('[data-testid="risk-metric-concentration-note"]').classes()).toContain('negative')
    expect(wrapper.get('[data-testid="risk-metric-concentration-note"] .metric-value').classes()).toContain('negative')
    expect(wrapper.get('[data-testid="risk-metric-concentration-note"]').text()).toContain('Einzeltitel dominiert')
    expect(normalizedText(wrapper.get('[data-testid="risk-metric-top-position-weight"]').text())).toContain('64,00 %')
    expect(normalizedText(wrapper.get('[data-testid="risk-metric-top3-weight"]').text())).toContain('91,00 %')
  })

  it('renders defensively for very small risk models', () => {
    const wrapper = mountPanel({
      person_id: 'person-1',
      as_of: '',
      meta: {}
    })

    const text = normalizedText(wrapper.text())
    expect(text).toContain('Stand: n/a')
    expect(text).toContain('Zeitraum: n/a')
    expect(text).toContain('Benchmark: n/a')
    expect(wrapper.findAll('.metric-card--primary')).toHaveLength(4)
    expect(wrapper.findAll('.metric-card--primary.is-missing')).toHaveLength(4)
    expect(wrapper.get('[data-testid="risk-benchmark-empty"]').text()).toContain('Keine Benchmark-Daten')
    expect(wrapper.get('[data-testid="risk-metric-concentration-note"]').text()).toContain('n/a')
    expect(wrapper.find('[data-testid="risk-block-performance"]').exists()).toBe(false)
  })
})
