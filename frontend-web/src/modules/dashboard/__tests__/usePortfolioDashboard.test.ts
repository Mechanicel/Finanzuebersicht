import { beforeEach, describe, expect, it, vi } from 'vitest'
import { usePortfolioDashboard } from '@/modules/dashboard/composables/usePortfolioDashboard'

vi.mock('@/modules/dashboard/api/portfolioDashboardApi', () => ({
  fetchPortfolioDashboard: vi.fn(),
  fetchPortfolioSummary: vi.fn(),
  fetchPortfolioPerformance: vi.fn(),
  fetchPortfolioExposures: vi.fn(),
  fetchPortfolioHoldings: vi.fn(),
  fetchPortfolioRisk: vi.fn(),
  fetchPortfolioAttribution: vi.fn(),
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
  fetchPortfolioAttribution,
  fetchPortfolioContributors,
  fetchPortfolioDataCoverage
} from '@/modules/dashboard/api/portfolioDashboardApi'
import type { PortfolioDashboardRange, PortfolioDashboardReadModel, PortfolioSummaryReadModel } from '@/shared/model/types'

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

function buildSummary(personId = 'person-1', marketValue = 100): PortfolioSummaryReadModel {
  return {
    person_id: personId,
    as_of: '2026-04-10',
    currency: 'EUR',
    market_value: marketValue,
    invested_value: 90,
    unrealized_pnl: marketValue - 90,
    portfolios_count: 1,
    holdings_count: 1,
    meta: {}
  }
}

function buildDashboard(range: PortfolioDashboardRange | string = '3m', personId = 'person-1', marketValue = 100): PortfolioDashboardReadModel {
  const summary = buildSummary(personId, marketValue)
  return {
    person_id: personId,
    as_of: '2026-04-10',
    range,
    benchmark_symbol: 'SPY',
    summary,
    performance: {
      person_id: personId,
      range,
      benchmark_symbol: 'SPY',
      series: [],
      summary: {},
      meta: {}
    },
    exposures: { person_id: personId, by_position: [], by_sector: [], by_country: [], by_currency: [], meta: {} },
    holdings: {
      person_id: personId,
      as_of: '2026-04-10',
      currency: 'EUR',
      items: [],
      summary,
      meta: {}
    },
    risk: { person_id: personId, as_of: '2026-04-10', range, benchmark_symbol: 'SPY', meta: {} },
    coverage: {
      person_id: personId,
      as_of: '2026-04-10',
      total_holdings: 1,
      missing_prices: 0,
      missing_sectors: 0,
      missing_countries: 0,
      missing_currencies: 0,
      warnings: [],
      meta: {}
    },
    contributors: { person_id: personId, as_of: '2026-04-10', range, top_contributors: [], top_detractors: [], meta: {} },
    meta: {}
  }
}

describe('usePortfolioDashboard', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(fetchPortfolioDashboard).mockImplementation(async (personId: string, range = '3m') => buildDashboard(range, personId))
  })

  it('loads the complete dashboard through the bootstrap endpoint for the requested range', async () => {
    const vm = usePortfolioDashboard('person-1')

    await vm.loadBootstrap('6m')

    expect(fetchPortfolioDashboard).toHaveBeenCalledTimes(1)
    expect(fetchPortfolioDashboard).toHaveBeenCalledWith('person-1', '6m')
    expect(fetchPortfolioSummary).not.toHaveBeenCalled()
    expect(fetchPortfolioPerformance).not.toHaveBeenCalled()
    expect(fetchPortfolioHoldings).not.toHaveBeenCalled()
    expect(fetchPortfolioRisk).not.toHaveBeenCalled()
    expect(fetchPortfolioAttribution).not.toHaveBeenCalled()
    expect(fetchPortfolioContributors).not.toHaveBeenCalled()
    expect(fetchPortfolioDataCoverage).not.toHaveBeenCalled()
    expect(fetchPortfolioExposures).not.toHaveBeenCalled()

    expect(vm.summary.value?.person_id).toBe('person-1')
    expect(vm.performance.value?.range).toBe('6m')
    expect(vm.attribution.value?.benchmark_symbol).toBe('SPY')
    expect(vm.attribution.value?.meta.source).toBe('contributors_fallback')
    expect(vm.dashboardSummary.value?.market_value).toBe(100)
    expect(vm.loading.value).toBe(false)
    expect(Object.values(vm.loadingStates.value).every((value) => !value)).toBe(true)
  })

  it('prefers the dashboard attribution contract when it is present', async () => {
    const dashboard = buildDashboard('3m')
    dashboard.attribution = {
      person_id: 'person-1',
      as_of: '2026-04-10',
      range: '3m',
      range_label: '3 Monate',
      benchmark_symbol: 'MSCI World',
      methodology: {
        key: 'range_contribution',
        label: 'Beitrag zur Zeitraumrendite',
        description: 'Beitrag in Prozentpunkten',
        contribution_basis: 'range_contribution',
        contribution_unit: 'percentage_points'
      },
      summary: {
        total_contribution_pct_points: 2.1,
        covered_positions: 1,
        total_positions: 1,
        unattributed_positions: 0
      },
      by_position: [{ label: 'Apple', contribution_pct_points: 1.2, direction: 'positive' }],
      by_sector: [{ label: 'Technology', contribution_pct_points: 0.9, direction: 'positive' }],
      by_country: [],
      by_currency: [],
      warnings: [],
      meta: { source: 'portfolio_attribution' }
    }
    vi.mocked(fetchPortfolioDashboard).mockResolvedValueOnce(dashboard)

    const vm = usePortfolioDashboard('person-1')

    await vm.loadBootstrap('3m')

    expect(vm.attribution.value?.benchmark_symbol).toBe('MSCI World')
    expect(vm.attribution.value?.by_sector?.[0]?.label).toBe('Technology')
    expect(vm.attribution.value?.meta.source).toBe('portfolio_attribution')
  })

  it('keeps legacy loadInitial and loadAll on the bootstrap path', async () => {
    const vm = usePortfolioDashboard('person-1')

    await vm.loadInitial('1y')
    await vm.loadAll('max')

    expect(fetchPortfolioDashboard).toHaveBeenNthCalledWith(1, 'person-1', '1y')
    expect(fetchPortfolioDashboard).toHaveBeenNthCalledWith(2, 'person-1', 'max')
    expect(fetchPortfolioSummary).not.toHaveBeenCalled()
  })

  it('sets global and section errors when the bootstrap endpoint fails', async () => {
    vi.mocked(fetchPortfolioDashboard).mockRejectedValue(new Error('bootstrap failed'))

    const vm = usePortfolioDashboard('person-1')

    await expect(vm.loadBootstrap('3m')).rejects.toThrow('bootstrap failed')

    expect(vm.hasData.value).toBe(false)
    expect(vm.error.value).toContain('bootstrap failed')
    expect(vm.errors.value.performance).toContain('bootstrap failed')
    expect(vm.loading.value).toBe(false)
    expect(Object.values(vm.loadingStates.value).every((value) => !value)).toBe(true)
  })

  it('ignores stale bootstrap responses on rapid range reloads', async () => {
    const firstLoad = deferred<PortfolioDashboardReadModel>()
    const secondLoad = deferred<PortfolioDashboardReadModel>()
    vi.mocked(fetchPortfolioDashboard).mockImplementation((_personId: string, range = '3m') =>
      range === '3m' ? firstLoad.promise : secondLoad.promise
    )

    const vm = usePortfolioDashboard('person-1')
    const staleRequest = vm.loadBootstrap('3m')
    const currentRequest = vm.loadBootstrap('1y')

    secondLoad.resolve(buildDashboard('1y', 'person-1', 200))
    await currentRequest
    expect(vm.performance.value?.range).toBe('1y')
    expect(vm.dashboardSummary.value?.market_value).toBe(200)

    firstLoad.resolve(buildDashboard('3m', 'person-1', 999))
    await staleRequest

    expect(vm.performance.value?.range).toBe('1y')
    expect(vm.dashboardSummary.value?.market_value).toBe(200)
  })
})
