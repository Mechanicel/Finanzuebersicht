import { beforeEach, describe, expect, it, vi } from 'vitest'
import { usePortfolioDashboard } from '@/modules/dashboard/composables/usePortfolioDashboard'

vi.mock('@/modules/dashboard/api/portfolioDashboardApi', () => ({
  fetchPortfolioSummary: vi.fn(),
  fetchPortfolioPerformance: vi.fn(),
  fetchPortfolioExposures: vi.fn(),
  fetchPortfolioHoldings: vi.fn(),
  fetchPortfolioRisk: vi.fn(),
  fetchPortfolioContributors: vi.fn(),
  fetchPortfolioDataCoverage: vi.fn()
}))

import {
  fetchPortfolioSummary,
  fetchPortfolioPerformance,
  fetchPortfolioExposures,
  fetchPortfolioHoldings,
  fetchPortfolioRisk,
  fetchPortfolioContributors,
  fetchPortfolioDataCoverage
} from '@/modules/dashboard/api/portfolioDashboardApi'
import type {
  PortfolioContributorsReadModel,
  PortfolioDataCoverageReadModel,
  PortfolioExposuresReadModel,
  PortfolioHoldingsReadModel,
  PortfolioPerformanceReadModel,
  PortfolioRiskReadModel,
  PortfolioSummaryReadModel
} from '@/shared/model/types'

describe('usePortfolioDashboard', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('loads dashboard slices in two phases and keeps summary and contributors out of auto load', async () => {
    const pendingInitial: Array<{ resolve: () => void }> = []

    const phaseOneFactory = (value: unknown) =>
      vi.fn().mockImplementation(
        () =>
          new Promise((resolve) => {
            pendingInitial.push({ resolve: () => resolve(value) })
          })
      )

    vi.mocked(fetchPortfolioHoldings).mockImplementation(
      phaseOneFactory({
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
      } as PortfolioHoldingsReadModel)
    )
    vi.mocked(fetchPortfolioDataCoverage).mockImplementation(
      phaseOneFactory({
        person_id: 'person-1',
        as_of: '2026-04-10',
        total_holdings: 0,
        missing_prices: 0,
        missing_sectors: 0,
        missing_countries: 0,
        missing_currencies: 0,
        warnings: [],
        meta: {}
      } as PortfolioDataCoverageReadModel)
    )

    const performance: PortfolioPerformanceReadModel = { person_id: 'person-1', range: '3m', series: [], summary: {}, meta: {} }
    const risk: PortfolioRiskReadModel = { person_id: 'person-1', as_of: '2026-04-10', meta: {} }
    const exposures: PortfolioExposuresReadModel = { person_id: 'person-1', by_position: [], by_sector: [], by_country: [], by_currency: [], meta: {} }

    vi.mocked(fetchPortfolioPerformance).mockResolvedValue(performance)
    vi.mocked(fetchPortfolioRisk).mockResolvedValue(risk)
    vi.mocked(fetchPortfolioExposures).mockResolvedValue(exposures)
    vi.mocked(fetchPortfolioSummary).mockResolvedValue({ person_id: 'person-1', meta: {} } as PortfolioSummaryReadModel)
    vi.mocked(fetchPortfolioContributors).mockResolvedValue({
      person_id: 'person-1',
      top_contributors: [],
      top_detractors: [],
      meta: {}
    } as PortfolioContributorsReadModel)

    const vm = usePortfolioDashboard('person-1')
    const loadAllPromise = vm.loadAll()

    expect(fetchPortfolioSummary).not.toHaveBeenCalled()
    expect(fetchPortfolioHoldings).toHaveBeenCalledTimes(1)
    expect(fetchPortfolioDataCoverage).toHaveBeenCalledTimes(1)
    expect(fetchPortfolioPerformance).not.toHaveBeenCalled()
    expect(fetchPortfolioRisk).not.toHaveBeenCalled()
    expect(fetchPortfolioExposures).not.toHaveBeenCalled()
    expect(fetchPortfolioContributors).not.toHaveBeenCalled()

    pendingInitial.forEach(({ resolve }) => resolve())
    await loadAllPromise

    expect(fetchPortfolioPerformance).toHaveBeenCalledTimes(1)
    expect(fetchPortfolioRisk).toHaveBeenCalledTimes(1)
    expect(fetchPortfolioExposures).toHaveBeenCalledTimes(1)
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

    vi.mocked(fetchPortfolioHoldings).mockResolvedValue({
      person_id: 'person-1',
      as_of: '2026-04-10',
      currency: 'EUR',
      items: [],
      summary: holdingsSummary,
      meta: {}
    })
    vi.mocked(fetchPortfolioDataCoverage).mockResolvedValue({
      person_id: 'person-1',
      as_of: '2026-04-10',
      total_holdings: 0,
      missing_prices: 0,
      missing_sectors: 0,
      missing_countries: 0,
      missing_currencies: 0,
      warnings: [],
      meta: {}
    })
    vi.mocked(fetchPortfolioPerformance).mockResolvedValue({ person_id: 'person-1', range: '3m', series: [], summary: {}, meta: {} })
    vi.mocked(fetchPortfolioRisk).mockResolvedValue({ person_id: 'person-1', as_of: '2026-04-10', meta: {} })
    vi.mocked(fetchPortfolioExposures).mockResolvedValue({ person_id: 'person-1', by_position: [], by_sector: [], by_country: [], by_currency: [], meta: {} })

    const vm = usePortfolioDashboard('person-1')
    await vm.loadAll()

    expect(vm.dashboardSummary.value).toEqual(holdingsSummary)
  })

  it('sets global error when one phase-1 request fails', async () => {
    vi.mocked(fetchPortfolioHoldings).mockRejectedValue(new Error('holdings failed'))
    vi.mocked(fetchPortfolioPerformance).mockResolvedValue({ person_id: 'person-1', range: '3m', series: [], summary: {}, meta: {} })
    vi.mocked(fetchPortfolioExposures).mockResolvedValue({ person_id: 'person-1', by_position: [], by_sector: [], by_country: [], by_currency: [], meta: {} })
    vi.mocked(fetchPortfolioRisk).mockResolvedValue({ person_id: 'person-1', as_of: '2026-04-10', meta: {} })
    vi.mocked(fetchPortfolioDataCoverage).mockResolvedValue({
      person_id: 'person-1',
      as_of: '2026-04-10',
      total_holdings: 0,
      missing_prices: 0,
      missing_sectors: 0,
      missing_countries: 0,
      missing_currencies: 0,
      warnings: [],
      meta: {}
    })

    const vm = usePortfolioDashboard('person-1')
    await vm.loadAll()

    expect(vm.errors.value.holdings.length).toBeGreaterThan(0)
    expect(vm.error.value.length).toBeGreaterThan(0)
    expect(fetchPortfolioSummary).not.toHaveBeenCalled()
    expect(fetchPortfolioContributors).not.toHaveBeenCalled()
  })
})
