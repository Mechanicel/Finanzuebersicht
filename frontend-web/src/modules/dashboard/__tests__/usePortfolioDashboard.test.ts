import { describe, expect, it, vi, beforeEach } from 'vitest'
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

  it('loads all portfolio slices and exposes helper states', async () => {
    const summary: PortfolioSummaryReadModel = {
      person_id: 'person-1',
      as_of: '2026-04-10',
      currency: 'EUR',
      market_value: 360,
      invested_value: 350,
      unrealized_pnl: 10,
      unrealized_return_pct: 2.8,
      portfolios_count: 1,
      holdings_count: 2,
      top_position_weight: 0.61,
      top3_weight: 1,
      meta: {}
    }
    const performance: PortfolioPerformanceReadModel = {
      person_id: 'person-1',
      range: '3m',
      benchmark_symbol: null,
      series: [],
      summary: {},
      meta: {}
    }
    const exposures: PortfolioExposuresReadModel = {
      person_id: 'person-1',
      by_position: [],
      by_sector: [],
      by_country: [],
      by_currency: [],
      meta: {}
    }
    const holdings: PortfolioHoldingsReadModel = {
      person_id: 'person-1',
      as_of: '2026-04-10',
      currency: 'EUR',
      items: [
        {
          portfolio_id: 'p-1',
          quantity: 1,
          invested_value: 100,
          market_value: 220,
          unrealized_pnl: 120,
          weight: 1,
          data_status: 'ok'
        }
      ],
      summary,
      meta: {}
    }
    const risk: PortfolioRiskReadModel = {
      person_id: 'person-1',
      as_of: '2026-04-10',
      meta: {}
    }
    const contributors: PortfolioContributorsReadModel = {
      person_id: 'person-1',
      top_contributors: [],
      top_detractors: [],
      meta: {}
    }
    const coverage: PortfolioDataCoverageReadModel = {
      person_id: 'person-1',
      as_of: '2026-04-10',
      total_holdings: 2,
      missing_prices: 1,
      missing_sectors: 0,
      missing_countries: 0,
      missing_currencies: 0,
      warnings: ['missing_prices'],
      meta: {}
    }

    vi.mocked(fetchPortfolioSummary).mockResolvedValue(summary)
    vi.mocked(fetchPortfolioPerformance).mockResolvedValue(performance)
    vi.mocked(fetchPortfolioExposures).mockResolvedValue(exposures)
    vi.mocked(fetchPortfolioHoldings).mockResolvedValue(holdings)
    vi.mocked(fetchPortfolioRisk).mockResolvedValue(risk)
    vi.mocked(fetchPortfolioContributors).mockResolvedValue(contributors)
    vi.mocked(fetchPortfolioDataCoverage).mockResolvedValue(coverage)

    const vm = usePortfolioDashboard('person-1')
    await vm.loadAll()

    expect(fetchPortfolioSummary).toHaveBeenCalledWith('person-1')
    expect(fetchPortfolioDataCoverage).toHaveBeenCalledWith('person-1')
    expect(vm.hasData.value).toBe(true)
    expect(vm.hasCoverageWarnings.value).toBe(true)
    expect(vm.topHoldings.value).toHaveLength(1)
    expect(vm.error.value).toBe('')
  })

  it('sets global error when one request fails', async () => {
    vi.mocked(fetchPortfolioSummary).mockRejectedValue(new Error('summary failed'))
    vi.mocked(fetchPortfolioPerformance).mockResolvedValue({
      person_id: 'person-1',
      range: '3m',
      series: [],
      summary: {},
      meta: {}
    })
    vi.mocked(fetchPortfolioExposures).mockResolvedValue({
      person_id: 'person-1',
      by_position: [],
      by_sector: [],
      by_country: [],
      by_currency: [],
      meta: {}
    })
    vi.mocked(fetchPortfolioHoldings).mockResolvedValue({
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
    vi.mocked(fetchPortfolioRisk).mockResolvedValue({
      person_id: 'person-1',
      as_of: '2026-04-10',
      meta: {}
    })
    vi.mocked(fetchPortfolioContributors).mockResolvedValue({
      person_id: 'person-1',
      top_contributors: [],
      top_detractors: [],
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

    const vm = usePortfolioDashboard('person-1')
    await vm.loadAll()

    expect(vm.errors.value.summary).toContain('Portfolio Summary')
    expect(vm.error.value.length).toBeGreaterThan(0)
  })
})
