import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
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
import type { PortfolioSummaryReadModel } from '@/shared/model/types'

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

describe('usePortfolioDashboard', () => {
  beforeEach(() => {
    vi.resetAllMocks()

    vi.mocked(fetchPortfolioSummary).mockResolvedValue({
      person_id: 'person-1',
      as_of: '2026-04-10',
      currency: 'EUR',
      market_value: 100,
      invested_value: 90,
      unrealized_pnl: 10,
      portfolios_count: 1,
      holdings_count: 1,
      meta: {}
    })
    vi.mocked(fetchPortfolioPerformance).mockResolvedValue({ person_id: 'person-1', range: '3m', series: [], summary: {}, meta: {} })
    vi.mocked(fetchPortfolioHoldings).mockResolvedValue({
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
    })
    vi.mocked(fetchPortfolioRisk).mockResolvedValue({ person_id: 'person-1', as_of: '2026-04-10', meta: {} })
    vi.mocked(fetchPortfolioContributors).mockResolvedValue({ person_id: 'person-1', top_contributors: [], top_detractors: [], meta: {} })
    vi.mocked(fetchPortfolioDataCoverage).mockResolvedValue({
      person_id: 'person-1',
      as_of: '2026-04-10',
      total_holdings: 1,
      missing_prices: 0,
      missing_sectors: 0,
      missing_countries: 0,
      missing_currencies: 0,
      warnings: [],
      meta: {}
    })
    vi.mocked(fetchPortfolioExposures).mockResolvedValue({ person_id: 'person-1', by_position: [], by_sector: [], by_country: [], by_currency: [], meta: {} })
  })

  it('loads sections sequentially and does not use bootstrap endpoint for initial load', async () => {
    const callOrder: string[] = []
    vi.mocked(fetchPortfolioSummary).mockImplementation(async () => {
      callOrder.push('summary')
      return {
        person_id: 'person-1', as_of: '2026-04-10', currency: 'EUR', market_value: 100, invested_value: 90, unrealized_pnl: 10, portfolios_count: 1, holdings_count: 1, meta: {}
      }
    })
    vi.mocked(fetchPortfolioPerformance).mockImplementation(async () => {
      callOrder.push('performance')
      return { person_id: 'person-1', range: '3m', series: [], summary: {}, meta: {} }
    })
    vi.mocked(fetchPortfolioHoldings).mockImplementation(async () => {
      callOrder.push('holdings')
      return { person_id: 'person-1', as_of: '2026-04-10', currency: 'EUR', items: [], summary: null, meta: {} }
    })
    vi.mocked(fetchPortfolioRisk).mockImplementation(async () => {
      callOrder.push('risk')
      return { person_id: 'person-1', as_of: '2026-04-10', meta: {} }
    })
    vi.mocked(fetchPortfolioContributors).mockImplementation(async () => {
      callOrder.push('contributors')
      return { person_id: 'person-1', top_contributors: [], top_detractors: [], meta: {} }
    })
    vi.mocked(fetchPortfolioDataCoverage).mockImplementation(async () => {
      callOrder.push('coverage')
      return {
        person_id: 'person-1', as_of: '2026-04-10', total_holdings: 1, missing_prices: 0, missing_sectors: 0, missing_countries: 0, missing_currencies: 0, warnings: [], meta: {}
      }
    })
    vi.mocked(fetchPortfolioExposures).mockImplementation(async () => {
      callOrder.push('exposures')
      return { person_id: 'person-1', by_position: [], by_sector: [], by_country: [], by_currency: [], meta: {} }
    })

    const vm = usePortfolioDashboard('person-1')
    await vm.loadAll()

    expect(fetchPortfolioDashboard).not.toHaveBeenCalled()
    expect(callOrder).toEqual(['summary', 'performance', 'holdings', 'risk', 'contributors', 'coverage', 'exposures'])
  })

  it('continues loading remaining sections when one section fails', async () => {
    vi.mocked(fetchPortfolioPerformance).mockRejectedValue(new Error('performance failed'))

    const vm = usePortfolioDashboard('person-1')
    await vm.loadAll()

    expect(fetchPortfolioHoldings).toHaveBeenCalledTimes(1)
    expect(fetchPortfolioRisk).toHaveBeenCalledTimes(1)
    expect(fetchPortfolioContributors).toHaveBeenCalledTimes(1)
    expect(fetchPortfolioDataCoverage).toHaveBeenCalledTimes(1)
    expect(fetchPortfolioExposures).toHaveBeenCalledTimes(1)
    expect(vm.errors.value.performance).toContain('performance failed')
    expect(vm.error.value).toBe('')
  })

  it('sets global error only when no section data could be loaded', async () => {
    vi.mocked(fetchPortfolioSummary).mockRejectedValue(new Error('summary failed'))
    vi.mocked(fetchPortfolioPerformance).mockRejectedValue(new Error('performance failed'))
    vi.mocked(fetchPortfolioHoldings).mockRejectedValue(new Error('holdings failed'))
    vi.mocked(fetchPortfolioRisk).mockRejectedValue(new Error('risk failed'))
    vi.mocked(fetchPortfolioContributors).mockRejectedValue(new Error('contributors failed'))
    vi.mocked(fetchPortfolioDataCoverage).mockRejectedValue(new Error('coverage failed'))
    vi.mocked(fetchPortfolioExposures).mockRejectedValue(new Error('exposures failed'))

    const vm = usePortfolioDashboard('person-1')
    await vm.loadAll()

    expect(vm.hasData.value).toBe(false)
    expect(vm.error.value).toContain('Portfolio-Dashboard-Daten konnten nicht vollständig geladen werden.')
  })

  it('keeps dashboardSummary compatible and prefers holdings.summary', async () => {
    const sharedSummary: PortfolioSummaryReadModel = {
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

    vi.mocked(fetchPortfolioSummary).mockResolvedValue(sharedSummary)
    vi.mocked(fetchPortfolioHoldings).mockResolvedValue({
      person_id: 'person-1',
      as_of: '2026-04-10',
      currency: 'EUR',
      items: [],
      summary: {
        ...sharedSummary,
        market_value: 555
      },
      meta: {}
    })

    const vm = usePortfolioDashboard('person-1')
    await vm.loadAll()

    expect(vm.dashboardSummary.value?.market_value).toBe(555)

    vi.mocked(fetchPortfolioHoldings).mockResolvedValueOnce({
      person_id: 'person-1',
      as_of: '2026-04-10',
      currency: 'EUR',
      items: [],
      summary: null,
      meta: {}
    })
    await vm.loadAll()
    expect(vm.dashboardSummary.value).toEqual(sharedSummary)
  })

  it('ignores stale responses on reload and person switch', async () => {
    const personId = ref('person-1')
    const firstSummary = deferred<PortfolioSummaryReadModel>()
    const secondSummary = deferred<PortfolioSummaryReadModel>()

    vi.mocked(fetchPortfolioSummary).mockImplementation((requestedPersonId: string) => {
      if (requestedPersonId === 'person-1') return firstSummary.promise
      return secondSummary.promise
    })
    vi.mocked(fetchPortfolioPerformance).mockImplementation(async (requestedPersonId: string) => ({ person_id: requestedPersonId, range: '3m', series: [], summary: {}, meta: {} }))
    vi.mocked(fetchPortfolioHoldings).mockImplementation(async (requestedPersonId: string) => ({ person_id: requestedPersonId, as_of: '2026-04-10', currency: 'EUR', items: [], summary: null, meta: {} }))
    vi.mocked(fetchPortfolioRisk).mockImplementation(async (requestedPersonId: string) => ({ person_id: requestedPersonId, as_of: '2026-04-10', meta: {} }))
    vi.mocked(fetchPortfolioContributors).mockImplementation(async (requestedPersonId: string) => ({ person_id: requestedPersonId, top_contributors: [], top_detractors: [], meta: {} }))
    vi.mocked(fetchPortfolioDataCoverage).mockImplementation(async (requestedPersonId: string) => ({
      person_id: requestedPersonId,
      as_of: '2026-04-10',
      total_holdings: 0,
      missing_prices: 0,
      missing_sectors: 0,
      missing_countries: 0,
      missing_currencies: 0,
      warnings: [],
      meta: {}
    }))
    vi.mocked(fetchPortfolioExposures).mockImplementation(async (requestedPersonId: string) => ({ person_id: requestedPersonId, by_position: [], by_sector: [], by_country: [], by_currency: [], meta: {} }))

    const vm = usePortfolioDashboard(personId)
    const firstLoad = vm.loadAll()

    personId.value = 'person-2'
    const secondLoad = vm.loadAll()

    secondSummary.resolve({
      person_id: 'person-2',
      as_of: '2026-04-10',
      currency: 'EUR',
      market_value: 200,
      invested_value: 190,
      unrealized_pnl: 10,
      portfolios_count: 1,
      holdings_count: 2,
      meta: {}
    })
    await secondLoad
    expect(vm.summary.value?.person_id).toBe('person-2')

    firstSummary.resolve({
      person_id: 'person-1',
      as_of: '2026-04-10',
      currency: 'EUR',
      market_value: 999,
      invested_value: 1,
      unrealized_pnl: 998,
      portfolios_count: 1,
      holdings_count: 1,
      meta: {}
    })
    await firstLoad

    expect(vm.summary.value?.person_id).toBe('person-2')
    expect(vm.summary.value?.market_value).toBe(200)
  })
})
