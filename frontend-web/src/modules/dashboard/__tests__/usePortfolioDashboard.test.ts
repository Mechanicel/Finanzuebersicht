import { beforeEach, describe, expect, it, vi } from 'vitest'
import { usePortfolioDashboard } from '@/modules/dashboard/composables/usePortfolioDashboard'

vi.mock('@/modules/dashboard/api/portfolioDashboardApi', () => ({
  fetchPortfolioDashboard: vi.fn(),
  fetchPortfolioSummary: vi.fn(),
  fetchPortfolioPerformance: vi.fn(),
  fetchPortfolioExposures: vi.fn(),
  fetchPortfolioHoldings: vi.fn(),
  fetchPortfolioRisk: vi.fn(),
  fetchPortfolioContributors: vi.fn(),
  fetchPortfolioDataCoverage: vi.fn()
}))

import {
  fetchPortfolioDashboard,
  fetchPortfolioSummary,
  fetchPortfolioPerformance,
  fetchPortfolioExposures,
  fetchPortfolioHoldings,
  fetchPortfolioRisk,
  fetchPortfolioContributors,
  fetchPortfolioDataCoverage
} from '@/modules/dashboard/api/portfolioDashboardApi'
import type {
  PortfolioDashboardReadModel,
  PortfolioSummaryReadModel
} from '@/shared/model/types'

describe('usePortfolioDashboard', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('loads dashboard data with one bootstrap request', async () => {
    const bootstrapPayload: PortfolioDashboardReadModel = {
      person_id: 'person-1',
      as_of: '2026-04-10',
      range: '3m',
      benchmark_symbol: 'SPY',
      summary: {
        person_id: 'person-1',
        as_of: '2026-04-10',
        currency: 'EUR',
        market_value: 100,
        invested_value: 90,
        unrealized_pnl: 10,
        portfolios_count: 1,
        holdings_count: 1,
        meta: {}
      },
      performance: { person_id: 'person-1', range: '3m', series: [], summary: {}, meta: {} },
      exposures: { person_id: 'person-1', by_position: [], by_sector: [], by_country: [], by_currency: [], meta: {} },
      holdings: {
        person_id: 'person-1',
        as_of: '2026-04-10',
        currency: 'EUR',
        items: [],
        summary: {
          person_id: 'person-1',
          as_of: '2026-04-10',
          currency: 'EUR',
          market_value: 100,
          invested_value: 90,
          unrealized_pnl: 10,
          portfolios_count: 1,
          holdings_count: 1,
          meta: {}
        },
        meta: {}
      },
      risk: { person_id: 'person-1', as_of: '2026-04-10', meta: {} },
      coverage: {
        person_id: 'person-1',
        as_of: '2026-04-10',
        total_holdings: 1,
        missing_prices: 0,
        missing_sectors: 0,
        missing_countries: 0,
        missing_currencies: 0,
        warnings: [],
        meta: {}
      },
      contributors: { person_id: 'person-1', top_contributors: [], top_detractors: [], meta: {} },
      meta: { loading: false, error: null, warnings: [] }
    }
    vi.mocked(fetchPortfolioDashboard).mockResolvedValue(bootstrapPayload)

    const vm = usePortfolioDashboard('person-1')
    await vm.loadAll()

    expect(fetchPortfolioDashboard).toHaveBeenCalledTimes(1)
    expect(fetchPortfolioSummary).not.toHaveBeenCalled()
    expect(fetchPortfolioHoldings).not.toHaveBeenCalled()
    expect(fetchPortfolioDataCoverage).not.toHaveBeenCalled()
    expect(fetchPortfolioPerformance).not.toHaveBeenCalled()
    expect(fetchPortfolioRisk).not.toHaveBeenCalled()
    expect(fetchPortfolioExposures).not.toHaveBeenCalled()
    expect(fetchPortfolioContributors).not.toHaveBeenCalled()
    expect(vm.error.value).toBe('')
  })

  it('uses holdings summary as primary summary source', async () => {
    const holdingsSummary: PortfolioSummaryReadModel = {
      person_id: 'person-1',
      as_of: '2026-04-10',
      currency: 'EUR',
      market_value: 100,
      invested_value: 90,
      unrealized_pnl: 10,
      portfolios_count: 1,
      holdings_count: 1,
      meta: {}
    }

    vi.mocked(fetchPortfolioDashboard).mockResolvedValue({
      person_id: 'person-1',
      as_of: '2026-04-10',
      range: '3m',
      summary: holdingsSummary,
      performance: { person_id: 'person-1', range: '3m', series: [], summary: {}, meta: {} },
      exposures: { person_id: 'person-1', by_position: [], by_sector: [], by_country: [], by_currency: [], meta: {} },
      holdings: { person_id: 'person-1', as_of: '2026-04-10', currency: 'EUR', items: [], summary: holdingsSummary, meta: {} },
      risk: { person_id: 'person-1', as_of: '2026-04-10', meta: {} },
      coverage: {
        person_id: 'person-1',
        as_of: '2026-04-10',
        total_holdings: 0,
        missing_prices: 0,
        missing_sectors: 0,
        missing_countries: 0,
        missing_currencies: 0,
        warnings: [],
        meta: {}
      },
      contributors: { person_id: 'person-1', top_contributors: [], top_detractors: [], meta: {} },
      meta: { loading: false, error: null, warnings: [] }
    })

    const vm = usePortfolioDashboard('person-1')
    await vm.loadAll()

    expect(vm.dashboardSummary.value).toEqual(holdingsSummary)
  })

  it('sets global error when one phase-1 request fails', async () => {
    vi.mocked(fetchPortfolioDashboard).mockRejectedValue(new Error('bootstrap failed'))

    const vm = usePortfolioDashboard('person-1')
    await vm.loadAll()

    expect(vm.errors.value.holdings.length).toBeGreaterThan(0)
    expect(vm.error.value.length).toBeGreaterThan(0)
    expect(fetchPortfolioDashboard).toHaveBeenCalledTimes(1)
    expect(fetchPortfolioSummary).not.toHaveBeenCalled()
    expect(fetchPortfolioContributors).not.toHaveBeenCalled()
  })
})
