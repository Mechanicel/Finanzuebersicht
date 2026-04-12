// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, computed } from 'vue'
import PortfolioDashboardContainer from '@/modules/dashboard/components/PortfolioDashboardContainer.vue'
import PortfolioSummaryBar from '@/modules/dashboard/components/PortfolioSummaryBar.vue'

const loadAllMock = vi.fn().mockResolvedValue([])

vi.mock('@/modules/dashboard/composables/usePortfolioDashboard', () => ({
  usePortfolioDashboard: vi.fn()
}))

import { usePortfolioDashboard } from '@/modules/dashboard/composables/usePortfolioDashboard'

function buildDashboardState(overrides: Record<string, unknown> = {}) {
  return {
    summary: ref(null),
    dashboardSummary: ref({
      person_id: 'person-1',
      as_of: '2026-04-10',
      currency: 'EUR',
      market_value: 360,
      invested_value: 350,
      unrealized_pnl: 10,
      unrealized_return_pct: 2.86,
      portfolios_count: 1,
      holdings_count: 2,
      top_position_weight: 0.61,
      top3_weight: 1,
      meta: {}
    }),
    performance: ref({
      person_id: 'person-1',
      range: '3m',
      benchmark_symbol: 'SPY',
      series: [
        { key: 'portfolio_value', label: 'Portfolio', points: [{ x: '2026-01-01', y: 340 }, { x: '2026-01-02', y: 365 }] },
        { key: 'benchmark_price', label: 'Benchmark SPY', points: [{ x: '2026-01-01', y: 200 }, { x: '2026-01-02', y: 210 }] }
      ],
      summary: { start_value: 340, end_value: 365, absolute_change: 25, return_pct: 7.35 },
      meta: {}
    }),
    exposures: ref({ person_id: 'person-1', by_position: [], by_sector: [], by_country: [], by_currency: [], meta: {} }),
    holdings: ref({ person_id: 'person-1', as_of: '2026-04-10', currency: 'EUR', summary: {
      person_id: 'person-1', as_of: '2026-04-10', currency: 'EUR', market_value: 360, invested_value: 350, unrealized_pnl: 10, portfolios_count: 1, holdings_count: 2, meta: {}
    }, items: [{ portfolio_id: 'p-1', symbol: 'AAPL', display_name: 'Apple', quantity: 1, invested_value: 100, market_value: 220, unrealized_pnl: 120, weight: 0.61, data_status: 'ok' }], meta: {} }),
    risk: ref({
      person_id: 'person-1',
      as_of: '2026-04-10',
      portfolio_volatility: 0.12,
      max_drawdown: -0.2,
      correlation: 0.88,
      beta: 1.05,
      tracking_error: 0.04,
      top_position_weight: 0.61,
      top3_weight: 1,
      concentration_note: 'high_top3_concentration',
      meta: {}
    }),
    contributors: ref({ person_id: 'person-1', top_contributors: [], top_detractors: [], meta: {} }),
    coverage: ref({
      person_id: 'person-1',
      as_of: '2026-04-10',
      total_holdings: 2,
      missing_prices: 0,
      missing_sectors: 0,
      missing_countries: 0,
      missing_currencies: 0,
      fallback_acquisition_prices: 1,
      holdings_with_marketdata_warnings: 1,
      warnings: ['fallback_acquisition_price_used'],
      meta: {}
    }),
    loading: ref(false),
    loadingStates: ref({ summary: false, performance: false, exposures: false, holdings: false, risk: false, contributors: false, coverage: false }),
    error: ref(''),
    errors: ref({ summary: '', performance: '', exposures: '', holdings: '', risk: '', contributors: '', coverage: '' }),
    loadAll: loadAllMock,
    loadSummary: vi.fn(),
    loadPerformance: vi.fn(),
    loadExposures: vi.fn(),
    loadHoldings: vi.fn(),
    loadRisk: vi.fn(),
    loadContributors: vi.fn(),
    loadCoverage: vi.fn(),
    hasData: computed(() => true),
    hasCoverageWarnings: computed(() => false),
    topHoldings: computed(() => []),
    isEmpty: computed(() => false),
    ...overrides
  }
}

describe('PortfolioDashboardContainer', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    loadAllMock.mockResolvedValue([])
    vi.mocked(usePortfolioDashboard).mockReturnValue(buildDashboardState())
  })

  it('renders cockpit sections and triggers loadAll on mount', async () => {
    const wrapper = mount(PortfolioDashboardContainer, {
      props: { personId: 'person-1' }
    })

    expect(wrapper.text()).toContain('Portfolio Dashboard')
    expect(wrapper.text()).toContain('Portfolio Performance')
    expect(wrapper.text()).toContain('Portfolio Risk')
    expect(wrapper.text()).toContain('Benchmark: SPY')
    expect(wrapper.text()).toContain('Tracking Error')
    expect(wrapper.text()).toContain('Exposures / Allocation')
    expect(wrapper.text()).toContain('Holdings')
    expect(wrapper.text()).toContain('Aktiv: AAPL')
    expect(loadAllMock).toHaveBeenCalledTimes(1)
  })

  it('renders loaded sections while later sections are still loading', () => {
    vi.mocked(usePortfolioDashboard).mockReturnValue(
      buildDashboardState({
        performance: ref(null),
        exposures: ref(null),
        risk: ref(null),
        coverage: ref(null),
        contributors: ref(null),
        loadingStates: ref({ summary: false, performance: true, exposures: true, holdings: false, risk: true, contributors: true, coverage: true })
      })
    )

    const wrapper = mount(PortfolioDashboardContainer, {
      props: { personId: 'person-1' }
    })

    expect(wrapper.text()).toContain('Marktwert')
    expect(wrapper.text()).toContain('Holdings')
    expect(wrapper.text()).toContain('Performance wird geladen…')
    expect(wrapper.text()).toContain('Risk wird geladen…')
    expect(wrapper.text()).not.toContain('Portfolio-Dashboard-Daten konnten nicht geladen werden.')
  })

  it('shows local section errors without blocking already loaded cockpit content', () => {
    vi.mocked(usePortfolioDashboard).mockReturnValue(
      buildDashboardState({
        performance: ref(null),
        errors: ref({ summary: '', performance: 'Performance temporär nicht verfügbar.', exposures: '', holdings: '', risk: '', contributors: '', coverage: '' }),
        loadingStates: ref({ summary: false, performance: false, exposures: false, holdings: false, risk: false, contributors: false, coverage: false })
      })
    )

    const wrapper = mount(PortfolioDashboardContainer, {
      props: { personId: 'person-1' }
    })

    expect(wrapper.text()).toContain('Marktwert')
    expect(wrapper.text()).toContain('Performance temporär nicht verfügbar.')
    expect(wrapper.text()).not.toContain('Portfolio-Dashboard-Daten konnten nicht geladen werden.')
  })

  it('shows global error only when no renderable data exists', () => {
    vi.mocked(usePortfolioDashboard).mockReturnValue(
      buildDashboardState({
        dashboardSummary: ref(null),
        performance: ref(null),
        exposures: ref(null),
        holdings: ref(null),
        risk: ref(null),
        contributors: ref(null),
        coverage: ref(null),
        error: ref('Alles fehlgeschlagen'),
        errors: ref({ summary: 'x', performance: 'x', exposures: 'x', holdings: 'x', risk: 'x', contributors: 'x', coverage: 'x' })
      })
    )

    const wrapper = mount(PortfolioDashboardContainer, {
      props: { personId: 'person-1' }
    })

    expect(wrapper.text()).toContain('Alles fehlgeschlagen')
  })

  it('shows stable empty detail state when no holdings are available', () => {
    vi.mocked(usePortfolioDashboard).mockReturnValue(
      buildDashboardState({
        dashboardSummary: ref({
          person_id: 'person-1',
          as_of: '2026-04-10',
          currency: 'EUR',
          market_value: 0,
          invested_value: 0,
          unrealized_pnl: 0,
          unrealized_return_pct: 0,
          portfolios_count: 0,
          holdings_count: 0,
          top_position_weight: null,
          top3_weight: null,
          meta: {}
        }),
        holdings: ref({
          person_id: 'person-1',
          as_of: '2026-04-10',
          currency: 'EUR',
          items: [],
          summary: {
            person_id: 'person-1',
            as_of: '2026-04-10',
            currency: 'EUR',
            market_value: 0,
            invested_value: 0,
            unrealized_pnl: 0,
            portfolios_count: 0,
            holdings_count: 0,
            meta: {}
          },
          meta: {}
        })
      })
    )

    const wrapper = mount(PortfolioDashboardContainer, {
      props: { personId: 'person-1' }
    })

    expect(wrapper.text()).toContain('Bitte eine Holding auswählen.')
  })
})

describe('PortfolioSummaryBar', () => {
  it('formats key portfolio numbers', () => {
    const wrapper = mount(PortfolioSummaryBar, {
      props: {
        summary: {
          person_id: 'person-1',
          as_of: '2026-04-10',
          currency: 'EUR',
          market_value: 360,
          invested_value: 350,
          unrealized_pnl: 10,
          unrealized_return_pct: 2.86,
          portfolios_count: 1,
          holdings_count: 2,
          top_position_weight: 0.61,
          top3_weight: 1,
          meta: {}
        }
      }
    })

    expect(wrapper.text()).toContain('Marktwert')
    expect(wrapper.text()).toContain('360,00')
    expect(wrapper.text()).toContain('Holdings')
  })
})
