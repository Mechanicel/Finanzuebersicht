// @vitest-environment jsdom
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import DepotAnalysisWorkspace from '@/modules/dashboard/components/DepotAnalysisWorkspace.vue'

vi.mock('@/modules/dashboard/api/depotAnalysisApi', () => ({
  fetchPersonPortfolios: vi.fn(),
  fetchPortfolioDetails: vi.fn(),
  fetchHoldingsSummary: vi.fn()
}))

import {
  fetchPersonPortfolios,
  fetchPortfolioDetails,
  fetchHoldingsSummary
} from '@/modules/dashboard/api/depotAnalysisApi'

describe('DepotAnalysisWorkspace', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('loads holdings and passes selected symbol to analysis tabs', async () => {
    vi.mocked(fetchPersonPortfolios).mockResolvedValue({ items: [{ portfolio_id: 'p1', person_id: 'person-1', display_name: 'Core', created_at: '', updated_at: '' }], total: 1 })
    vi.mocked(fetchPortfolioDetails).mockResolvedValue({
      portfolio_id: 'p1',
      person_id: 'person-1',
      display_name: 'Core',
      created_at: '',
      updated_at: '',
      holdings: [
        {
          holding_id: 'h1',
          portfolio_id: 'p1',
          symbol: 'AAPL',
          quantity: 2,
          acquisition_price: 100,
          currency: 'USD',
          buy_date: '2025-01-01',
          created_at: '',
          updated_at: ''
        }
      ]
    })
    vi.mocked(fetchHoldingsSummary).mockResolvedValue({
      items: [{ symbol: 'AAPL', company_name: 'Apple', sector: 'Technology', country: 'US', currency: 'USD', last_price: 180 }],
      total: 1,
      source: 'cache'
    })

    const wrapper = mount(DepotAnalysisWorkspace, {
      props: { personId: 'person-1' },
      global: {
        stubs: {
          DepotAllocationPanel: { template: '<div class="allocation-stub">allocation</div>' },
          InstrumentAnalysisTabs: { template: '<div class="tabs-stub">symbol={{ selectedSymbol }}</div>', props: ['selectedSymbol'] }
        }
      }
    })

    await flushPromises()

    expect(fetchPersonPortfolios).toHaveBeenCalledWith('person-1')
    expect(wrapper.find('.allocation-stub').exists()).toBe(true)
    expect(wrapper.find('.tabs-stub').text()).toContain('AAPL')
  })
})
