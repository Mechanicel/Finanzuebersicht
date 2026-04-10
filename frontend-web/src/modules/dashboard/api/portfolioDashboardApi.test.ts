import { describe, expect, it, vi, beforeEach } from 'vitest'

const getMock = vi.fn()

vi.mock('@/shared/api/http', () => ({
  http: {
    get: getMock
  }
}))

import {
  fetchPortfolioContributors,
  fetchPortfolioDataCoverage,
  fetchPortfolioExposures,
  fetchPortfolioHoldings,
  fetchPortfolioPerformance,
  fetchPortfolioRisk,
  fetchPortfolioSummary
} from '@/modules/dashboard/api/portfolioDashboardApi'

describe('portfolioDashboardApi', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('requests all portfolio dashboard endpoints with the expected URLs', async () => {
    getMock.mockResolvedValue({ data: { data: { ok: true } } })

    await fetchPortfolioSummary('person-1')
    await fetchPortfolioPerformance('person-1')
    await fetchPortfolioExposures('person-1')
    await fetchPortfolioHoldings('person-1')
    await fetchPortfolioRisk('person-1')
    await fetchPortfolioContributors('person-1')
    await fetchPortfolioDataCoverage('person-1')

    expect(getMock).toHaveBeenNthCalledWith(1, '/app/persons/person-1/portfolio-summary')
    expect(getMock).toHaveBeenNthCalledWith(2, '/app/persons/person-1/portfolio-performance')
    expect(getMock).toHaveBeenNthCalledWith(3, '/app/persons/person-1/portfolio-exposures')
    expect(getMock).toHaveBeenNthCalledWith(4, '/app/persons/person-1/portfolio-holdings')
    expect(getMock).toHaveBeenNthCalledWith(5, '/app/persons/person-1/portfolio-risk')
    expect(getMock).toHaveBeenNthCalledWith(6, '/app/persons/person-1/portfolio-contributors')
    expect(getMock).toHaveBeenNthCalledWith(7, '/app/persons/person-1/portfolio-data-coverage')
  })
})
