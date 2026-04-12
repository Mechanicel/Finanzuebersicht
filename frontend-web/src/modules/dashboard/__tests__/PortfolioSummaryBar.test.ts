// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import PortfolioSummaryBar from '@/modules/dashboard/components/PortfolioSummaryBar.vue'
import type { PortfolioSummaryReadModel } from '@/shared/model/types'

const componentSource = readFileSync(join(process.cwd(), 'src/modules/dashboard/components/PortfolioSummaryBar.vue'), 'utf8')

function makeSummary(overrides: Partial<PortfolioSummaryReadModel> = {}): PortfolioSummaryReadModel {
  return {
    person_id: 'person-1',
    as_of: '2026-04-10',
    currency: 'EUR',
    market_value: 125000,
    invested_value: 100000,
    unrealized_pnl: 25000,
    unrealized_return_pct: 25,
    portfolios_count: 3,
    holdings_count: 18,
    top_position_weight: 0.22,
    top3_weight: 0.48,
    meta: {},
    ...overrides
  }
}

describe('PortfolioSummaryBar', () => {
  it('renders management KPIs in the intended hierarchy for normal data', () => {
    const wrapper = mount(PortfolioSummaryBar, {
      props: { summary: makeSummary() }
    })

    const labels = wrapper.findAll('[data-test="summary-kpi"]').map((card) => card.find('.label span').text())

    expect(labels).toEqual([
      'Marktwert',
      'Investierter Wert',
      'Unreal. P&L',
      'Unreal. Rendite',
      'Holdings',
      'Portfolios',
      'Top Position',
      'Top 3 Konzentration'
    ])
    expect(wrapper.findAll('[data-test="summary-kpi"]').map((card) => card.attributes('data-layout-priority'))).toEqual([
      '1',
      '2',
      '3',
      '4',
      '5',
      '6',
      '7',
      '8'
    ])
    expect(wrapper.get('[data-kpi="portfolios"]').text()).toContain('3')
    expect(wrapper.get('[data-test="summary-concentration-health"]').text()).toContain('Konzentration ok')
  })

  it('highlights concentration warnings when top weights are problematic', () => {
    const wrapper = mount(PortfolioSummaryBar, {
      props: {
        summary: makeSummary({
          top_position_weight: 0.55,
          top3_weight: 0.84
        })
      }
    })

    expect(wrapper.get('[data-test="summary-concentration-health"]').text()).toContain('Konzentration kritisch')
    expect(wrapper.get('[data-kpi="top-position"]').classes()).toContain('summary-card--critical')
    expect(wrapper.get('[data-kpi="top3-concentration"]').classes()).toContain('summary-card--critical')
    expect(wrapper.get('[data-kpi="top-position"]').classes()).toContain('summary-card--concentration')
    expect(wrapper.get('[data-kpi="top3-concentration"]').classes()).toContain('summary-card--concentration')
    expect(wrapper.get('[data-kpi="top-position"] .signal').classes()).toContain('signal--critical')
    expect(wrapper.get('[data-kpi="top3-concentration"] .signal').text()).toBe('kritisch')
  })

  it('keeps a one-holding portfolio readable while showing concentration risk', () => {
    const wrapper = mount(PortfolioSummaryBar, {
      props: {
        summary: makeSummary({
          market_value: 1500,
          invested_value: 1500,
          unrealized_pnl: 0,
          unrealized_return_pct: 0,
          portfolios_count: 1,
          holdings_count: 1,
          top_position_weight: 1,
          top3_weight: 1
        })
      }
    })

    expect(wrapper.get('[data-kpi="holdings"]').text()).toContain('1')
    expect(wrapper.get('[data-kpi="portfolios"]').text()).toContain('1')
    expect(wrapper.get('[data-kpi="top-position"]').classes()).toContain('summary-card--critical')
    expect(wrapper.get('[data-kpi="top3-concentration"]').classes()).toContain('summary-card--critical')
    expect(wrapper.findAll('[data-test="summary-kpi"]')).toHaveLength(8)
  })

  it('keeps optional concentration fields nullable without raising a warning', () => {
    const summaryWithoutOptionalFields: PortfolioSummaryReadModel = {
      person_id: 'person-1',
      as_of: '2026-04-10',
      currency: 'EUR',
      market_value: 125000,
      invested_value: 100000,
      unrealized_pnl: 25000,
      portfolios_count: 3,
      holdings_count: 18,
      meta: {}
    }
    const wrapper = mount(PortfolioSummaryBar, {
      props: { summary: summaryWithoutOptionalFields }
    })

    expect(wrapper.get('[data-test="summary-concentration-health"]').text()).toContain('Konzentration n/a')
    expect(wrapper.get('[data-kpi="top-position"]').text()).toContain('n/a')
    expect(wrapper.get('[data-kpi="top-position"]').classes()).not.toContain('summary-card--warning')
    expect(wrapper.get('[data-kpi="top-position"]').classes()).not.toContain('summary-card--critical')
  })

  it('defines responsive grid breakpoints instead of auto-fit wrapping', () => {
    const normalizedSource = componentSource.replace(/\s+/g, ' ')

    expect(componentSource).not.toContain('auto-fit')
    expect(normalizedSource).toContain('grid-template-columns: repeat(8, minmax(0, 1fr));')
    expect(normalizedSource).toContain('@media (min-width: 1180px)')
    expect(normalizedSource).toContain('grid-template-columns: repeat(12, minmax(0, 1fr));')
    expect(normalizedSource).toContain('@media (max-width: 820px)')
    expect(normalizedSource).toContain('grid-template-columns: repeat(4, minmax(0, 1fr));')
    expect(normalizedSource).toContain('@media (max-width: 540px)')
    expect(normalizedSource).toContain('.summary-card--concentration { grid-column: span 6; }')
  })
})
