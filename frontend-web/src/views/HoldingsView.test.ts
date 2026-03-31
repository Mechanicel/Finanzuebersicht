// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

import HoldingsView from './HoldingsView.vue'
import { apiClient } from '../api/client'

vi.mock('vue-router', () => ({ useRoute: () => ({ query: { personId: 'person-1' } }) }))
vi.mock('../api/client', () => ({
  apiClient: {
    portfolios: vi.fn(),
    createPortfolio: vi.fn(),
    portfolio: vi.fn(),
    searchInstruments: vi.fn(),
    addHolding: vi.fn()
  }
}))

async function flush() { await Promise.resolve(); await nextTick() }

describe('HoldingsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(apiClient.portfolios).mockResolvedValue({ items: [{ portfolio_id: 'p1', person_id: 'person-1', display_name: 'Core', created_at: 'x', updated_at: 'x' }], total: 1 })
    vi.mocked(apiClient.portfolio).mockResolvedValue({ portfolio_id: 'p1', person_id: 'person-1', display_name: 'Core', created_at: 'x', updated_at: 'x', holdings: [] })
    vi.mocked(apiClient.searchInstruments).mockResolvedValue({ query: 'aapl', total: 1, items: [{ symbol: 'AAPL', company_name: 'Apple', display_name: 'Apple', isin: 'US0378331005', wkn: '865985', last_price: 170, currency: 'USD' }] })
    vi.mocked(apiClient.addHolding).mockResolvedValue({} as never)
    vi.mocked(apiClient.createPortfolio).mockResolvedValue({ portfolio_id: 'p2', person_id: 'person-1', display_name: 'Neu', created_at: 'x', updated_at: 'x' })
  })

  it('renders search and add flow and adds holding', async () => {
    const wrapper = mount(HoldingsView, { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } })
    await flush()

    await wrapper.find('input[placeholder="Name / Symbol / ISIN / WKN"]').setValue('AAPL')
    await wrapper.findAll('button').find((b) => b.text() === 'Suchen')!.trigger('click')
    await flush()

    await wrapper.find('ul.search-list button').trigger('click')
    await flush()

    await wrapper.find('form.holding-form').trigger('submit.prevent')
    await flush()

    expect(apiClient.addHolding).toHaveBeenCalledWith('p1', expect.objectContaining({ symbol: 'AAPL' }))
  })

  it('shows empty search result state', async () => {
    vi.mocked(apiClient.searchInstruments).mockResolvedValue({ query: 'x', total: 0, items: [] })
    const wrapper = mount(HoldingsView, { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } })
    await flush()

    await wrapper.find('input[placeholder="Name / Symbol / ISIN / WKN"]').setValue('x')
    await wrapper.findAll('button').find((b) => b.text() === 'Suchen')!.trigger('click')
    await flush()

    expect(wrapper.text()).toContain('Keine Treffer gefunden.')
  })
})
