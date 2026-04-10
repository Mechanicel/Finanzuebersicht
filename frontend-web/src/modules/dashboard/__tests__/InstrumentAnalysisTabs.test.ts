// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import InstrumentAnalysisTabs from '@/modules/dashboard/components/InstrumentAnalysisTabs.vue'

vi.mock('@/modules/dashboard/api/depotAnalysisApi', () => ({
  fetchBenchmarkCatalog: vi.fn(),
  fetchInstrumentBenchmark: vi.fn(),
  fetchInstrumentFinancials: vi.fn(),
  fetchInstrumentFundamentals: vi.fn(),
  fetchInstrumentRisk: vi.fn(),
  fetchInstrumentTimeseries: vi.fn(),
  searchBenchmarkCatalog: vi.fn()
}))

import {
  fetchBenchmarkCatalog,
  fetchInstrumentBenchmark,
  fetchInstrumentFinancials,
  fetchInstrumentFundamentals,
  fetchInstrumentRisk,
  fetchInstrumentTimeseries
} from '@/modules/dashboard/api/depotAnalysisApi'

function setupBaseMocks() {
  vi.mocked(fetchInstrumentTimeseries).mockResolvedValue({
    symbol: 'AAPL',
    series: 'price',
    benchmark_symbol: 'SPY',
    instrument: { points: [{ date: '2025-01-01', value: 100 }] },
    benchmark: { symbol: 'SPY', points: [] },
    meta: { warnings: [] }
  })
  vi.mocked(fetchInstrumentRisk).mockResolvedValue({
    symbol: 'AAPL',
    benchmark: 'SPY',
    aligned_points: 1,
    volatility_proxy: 0.2,
    benchmark_volatility_proxy: 0.1,
    meta: { warnings: [] }
  })
  vi.mocked(fetchInstrumentBenchmark).mockResolvedValue({ symbol: 'AAPL', benchmark: 'SPY' })
  vi.mocked(fetchBenchmarkCatalog).mockResolvedValue({ items: [{ symbol: 'SPY', name: 'S&P 500' }] })
  vi.mocked(fetchInstrumentFundamentals).mockResolvedValue({ symbol: 'AAPL', company_name: 'Apple' })
}

describe('InstrumentAnalysisTabs', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    setupBaseMocks()
  })

  it('shows balance sheet highlights and table rows for financials', async () => {
    vi.mocked(fetchInstrumentFinancials).mockResolvedValue({
      symbol: 'AAPL',
      period: 'annual',
      currency: 'USD',
      statements: {
        balance_sheet: [
          {
            date: '2025-12-31',
            fiscalYear: 2025,
            period: 'FY',
            reportedCurrency: 'USD',
            totalAssets: 120000000,
            totalCurrentAssets: 45000000,
            totalLiabilities: 75000000,
            totalCurrentLiabilities: 33000000,
            totalEquity: 45000000,
            cashAndCashEquivalents: 12000000,
            cashAndShortTermInvestments: 18000000,
            totalDebt: 31000000,
            netDebt: 13000000
          },
          {
            date: '2024-12-31',
            fiscalYear: 2024,
            period: 'FY',
            reportedCurrency: 'USD',
            totalAssets: 110000000
          }
        ],
        income_statement: [{ date: '2025-12-31' }],
        cash_flow: [{ date: '2025-12-31' }]
      },
      meta: { warnings: [{ code: 'partial_data', message: 'Some periods are missing.' }] }
    })

    const wrapper = mount(InstrumentAnalysisTabs, {
      props: { selectedSymbol: 'AAPL' },
      global: {
        stubs: {
          SimpleLineChart: { template: '<div class="chart-stub" />' }
        }
      }
    })

    await flushPromises()
    await wrapper.findAll('button').find((button) => button.text().includes('Finanzberichte'))?.trigger('click')

    expect(wrapper.text()).toContain('Neueste Balance-Sheet-Periode')
    expect(wrapper.text()).toContain('Balance Sheet Verlauf (2 Perioden)')
    expect(wrapper.text()).toContain('Some periods are missing.')
    expect(wrapper.find('table.financials-table').exists()).toBe(true)
    expect(wrapper.text()).toContain('Total Assets')
    expect(wrapper.text()).not.toContain('undefined')
  })

  it('shows empty state for missing balance sheet data', async () => {
    vi.mocked(fetchInstrumentFinancials).mockResolvedValue({
      symbol: 'AAPL',
      period: 'annual',
      statements: { balance_sheet: [] }
    })

    const wrapper = mount(InstrumentAnalysisTabs, {
      props: { selectedSymbol: 'AAPL' },
      global: {
        stubs: {
          SimpleLineChart: { template: '<div class="chart-stub" />' }
        }
      }
    })

    await flushPromises()
    await wrapper.findAll('button').find((button) => button.text().includes('Finanzberichte'))?.trigger('click')

    expect(wrapper.text()).toContain('keine Balance-Sheet-Daten')
    expect(wrapper.find('table.financials-table').exists()).toBe(false)
  })
})
