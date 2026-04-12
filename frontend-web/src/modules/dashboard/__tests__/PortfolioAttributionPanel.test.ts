// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PortfolioAttributionPanel from '@/modules/dashboard/components/PortfolioAttributionPanel.vue'
import type { PortfolioAttributionReadModel } from '@/shared/model/types'

function buildAttribution(overrides: Partial<PortfolioAttributionReadModel> = {}): PortfolioAttributionReadModel {
  return {
    person_id: 'person-1',
    as_of: '2026-04-10',
    range: '3m',
    range_label: '3 Monate',
    benchmark_symbol: 'SPY',
    methodology: {
      key: 'holdings_based_static_return_contribution',
      label: 'Holdings-based static return contribution',
      description: 'Static holdings return contribution.',
      contribution_basis: 'return contribution over selected range',
      contribution_unit: 'percentage_points'
    },
    summary: {
      portfolio_return_pct: 3.2,
      total_contribution_pct_points: 2.7,
      residual_pct_points: 0.5,
      covered_positions: 3,
      total_positions: 3,
      unattributed_positions: 0
    },
    by_position: [
      { label: 'Apple', symbol: 'AAPL', contribution_pct_points: 2.4 },
      { label: 'Microsoft', symbol: 'MSFT', contribution_pct_points: 1.1 },
      { label: 'Tesla', symbol: 'TSLA', contribution_pct_points: -0.8 }
    ],
    by_sector: [
      { label: 'Technology', contribution_pct_points: 2.1 },
      { label: 'Utilities', contribution_pct_points: -0.4 }
    ],
    by_country: [
      { label: 'USA', contribution_pct_points: 2.9 },
      { label: 'Deutschland', contribution_pct_points: -0.3 }
    ],
    by_currency: [
      { label: 'USD', contribution_pct_points: 2.7 },
      { label: 'EUR', contribution_pct_points: -0.2 }
    ],
    warnings: [],
    meta: {},
    ...overrides
  }
}

describe('PortfolioAttributionPanel', () => {
  it('renders normal attribution across positions, sectors, countries and currencies', () => {
    const wrapper = mount(PortfolioAttributionPanel, {
      props: { attribution: buildAttribution() }
    })

    expect(wrapper.get('[data-testid="portfolio-attribution-panel"]').attributes('data-state')).toBe('ready')
    expect(wrapper.text()).toContain('Warum lief das Portfolio so?')
    expect(wrapper.get('[data-testid="attribution-meta"]').text()).toContain('3 Monate')
    expect(wrapper.get('[data-testid="attribution-meta"]').text()).toContain('SPY')
    expect(wrapper.get('[data-testid="attribution-meta"]').text()).toContain('Holdings-based static return contribution')
    expect(wrapper.get('[data-testid="attribution-section-position"]').text()).toContain('Apple')
    expect(wrapper.get('[data-testid="attribution-section-sector"]').text()).toContain('Technology')
    expect(wrapper.get('[data-testid="attribution-section-country"]').text()).toContain('USA')
    expect(wrapper.get('[data-testid="attribution-section-currency"]').text()).toContain('USD')
    expect(wrapper.get('[data-testid="attribution-positive-position"]').text()).toContain('+2,40 pp')
    expect(wrapper.get('[data-testid="attribution-negative-position"]').text()).toContain('-0,80 pp')
  })

  it('keeps one-sided positive attribution compact', () => {
    const wrapper = mount(PortfolioAttributionPanel, {
      props: {
        attribution: buildAttribution({
          by_position: [{ label: 'Apple', contribution_pct_points: 1.4 }],
          by_sector: [],
          by_country: [],
          by_currency: []
        })
      }
    })

    expect(wrapper.findAll('[data-testid="attribution-positive-position"]')).toHaveLength(1)
    expect(wrapper.get('[data-testid="attribution-empty-negative-position"]').text()).toContain('Keine negativen')
    expect(wrapper.text()).toContain('1/4 Bereiche')
  })

  it('keeps one-sided negative attribution compact', () => {
    const wrapper = mount(PortfolioAttributionPanel, {
      props: {
        attribution: buildAttribution({
          benchmark_symbol: null,
          by_position: [{ label: 'Tesla', contribution_pct_points: -1.2 }],
          by_sector: [],
          by_country: [],
          by_currency: []
        })
      }
    })

    expect(wrapper.findAll('[data-testid="attribution-negative-position"]')).toHaveLength(1)
    expect(wrapper.get('[data-testid="attribution-empty-positive-position"]').text()).toContain('Keine positiven')
    expect(wrapper.get('[data-testid="attribution-meta"]').text()).toContain('Keine Benchmark')
  })

  it('renders a stable empty attribution state', () => {
    const wrapper = mount(PortfolioAttributionPanel, {
      props: {
        attribution: buildAttribution({
          by_position: [],
          by_sector: [],
          by_country: [],
          by_currency: [],
          summary: {
            total_contribution_pct_points: 0,
            covered_positions: 0,
            total_positions: 0,
            unattributed_positions: 0
          }
        })
      }
    })

    expect(wrapper.get('[data-testid="portfolio-attribution-panel"]').attributes('data-state')).toBe('empty')
    expect(wrapper.text()).toContain('Keine Daten')
    expect(wrapper.findAll('[data-testid^="attribution-empty-positive-"]')).toHaveLength(4)
    expect(wrapper.findAll('[data-testid^="attribution-empty-negative-"]')).toHaveLength(4)
  })

  it('renders partial attribution without dropping missing sections', () => {
    const wrapper = mount(PortfolioAttributionPanel, {
      props: {
        attribution: buildAttribution({
          by_sector: [] as never,
          by_country: undefined as never,
          by_currency: {
            items: [
              { label: 'USD', contribution_pp: 0.9 },
              { label: 'CHF', contribution_pp: -0.2 }
            ]
          } as never,
          warnings: ['benchmark_data_missing']
        })
      }
    })

    expect(wrapper.get('[data-testid="attribution-section-sector"]').text()).toContain('Keine positiven')
    expect(wrapper.get('[data-testid="attribution-section-country"]').text()).toContain('Keine negativen')
    expect(wrapper.get('[data-testid="attribution-section-currency"]').text()).toContain('USD')
    expect(wrapper.get('[data-testid="attribution-section-currency"]').text()).toContain('CHF')
    expect(wrapper.get('[data-testid="attribution-warnings"]').text()).toContain('Benchmark-Daten fehlen')
  })
})
