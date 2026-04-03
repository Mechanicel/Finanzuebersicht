// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

import DepotHoldingsManager from '@/modules/accounts/components/DepotHoldingsManager.vue'
import { apiClient } from '@/shared/api/client'

vi.mock('@/shared/api/client', () => ({
  apiClient: {
    portfolios: vi.fn(),
    createPortfolio: vi.fn(),
    portfolio: vi.fn(),
    searchInstruments: vi.fn(),
    marketdataProfile: vi.fn(),
    addHolding: vi.fn(),
    updateHolding: vi.fn(),
    deleteHolding: vi.fn(),
  }
}))

async function flushUi() {
  await Promise.resolve()
  await nextTick()
  await Promise.resolve()
  await nextTick()
}

describe('DepotHoldingsManager (FMP flow)', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()

    vi.mocked(apiClient.portfolios).mockResolvedValue({
      items: [{ portfolio_id: 'p1', person_id: 'person-1', display_name: 'Depot Core', created_at: 'x', updated_at: 'x' }],
      total: 1,
    })
    vi.mocked(apiClient.portfolio).mockResolvedValue({
      portfolio_id: 'p1',
      person_id: 'person-1',
      display_name: 'Depot Core',
      created_at: 'x',
      updated_at: 'x',
      holdings: [],
    })
    vi.mocked(apiClient.createPortfolio).mockResolvedValue({ portfolio_id: 'p2', person_id: 'person-1', display_name: 'Depot Core', created_at: 'x', updated_at: 'x' })
    vi.mocked(apiClient.addHolding).mockResolvedValue({} as never)
    vi.mocked(apiClient.updateHolding).mockResolvedValue({} as never)
    vi.mocked(apiClient.deleteHolding).mockResolvedValue(undefined)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('uses a higher debounce and does not fire search on every keystroke', async () => {
    vi.mocked(apiClient.searchInstruments).mockResolvedValue({ query: 'Commerzbank', total: 1, items: [] })

    const wrapper = mount(DepotHoldingsManager, { props: { personId: 'person-1', depotLabel: 'Depot Core' } })
    await flushUi()

    const input = wrapper.find('input[placeholder*="Name / Symbol / ISIN / WKN"]')
    await input.setValue('C')
    await input.setValue('Co')
    await input.setValue('Com')

    await vi.advanceTimersByTimeAsync(900)
    await flushUi()
    expect(apiClient.searchInstruments).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(100)
    await flushUi()
    expect(apiClient.searchInstruments).toHaveBeenCalledTimes(1)
    expect(apiClient.searchInstruments).toHaveBeenCalledWith('Com')
  })

  it('renders search list with symbol, name, currency, exchange and exchange full name', async () => {
    vi.mocked(apiClient.searchInstruments).mockResolvedValue({
      query: 'Commerzbank',
      total: 1,
      items: [{
        symbol: 'CBK.DE',
        company_name: 'Commerzbank AG',
        display_name: 'Commerzbank AG',
        currency: 'EUR',
        exchange: 'XETRA',
        exchange_full_name: 'Deutsche Börse Xetra',
      }],
    })

    const wrapper = mount(DepotHoldingsManager, { props: { personId: 'person-1', depotLabel: 'Depot Core' } })
    await flushUi()

    await wrapper.find('input[placeholder*="Name / Symbol / ISIN / WKN"]').setValue('Commerzbank')
    await vi.advanceTimersByTimeAsync(1000)
    await flushUi()

    const listText = wrapper.find('ul.search-list').text()
    expect(listText).toContain('CBK.DE')
    expect(listText).toContain('Commerzbank AG')
    expect(listText).toContain('EUR')
    expect(listText).toContain('XETRA')
    expect(listText).toContain('Deutsche Börse Xetra')
  })

  it('loads profile when clicking search result and shows FMP fields', async () => {
    vi.mocked(apiClient.searchInstruments).mockResolvedValue({
      query: 'Commerzbank',
      total: 1,
      items: [{ symbol: 'CBK.DE', company_name: 'Commerzbank AG', display_name: 'Commerzbank AG', currency: 'EUR', exchange: 'XETRA', exchange_full_name: 'Deutsche Börse Xetra' }],
    })
    vi.mocked(apiClient.marketdataProfile).mockResolvedValue({
      symbol: 'CBK.DE',
      company_name: 'Commerzbank AG',
      currency: 'EUR',
      exchange: 'XETRA',
      exchange_full_name: 'Deutsche Börse Xetra',
      sector: 'Financial Services',
      country: 'DE',
      price: 18.35,
    })

    const wrapper = mount(DepotHoldingsManager, { props: { personId: 'person-1', depotLabel: 'Depot Core' } })
    await flushUi()

    await wrapper.find('input[placeholder*="Name / Symbol / ISIN / WKN"]').setValue('Commerzbank')
    await vi.advanceTimersByTimeAsync(1000)
    await flushUi()

    await wrapper.find('ul.search-list button').trigger('click')
    await flushUi()

    expect(apiClient.marketdataProfile).toHaveBeenCalledWith('CBK.DE')
    const profilePanelText = wrapper.find('.profile-panel').text()
    expect(profilePanelText).toContain('company_name')
    expect(profilePanelText).toContain('Commerzbank AG')
    expect(profilePanelText).toContain('exchange_full_name')
    expect(profilePanelText).toContain('Deutsche Börse Xetra')
    expect(profilePanelText).toContain('sector')
    expect(profilePanelText).toContain('Financial Services')
  })

  it('prefills holding form from loaded profile', async () => {
    vi.mocked(apiClient.searchInstruments).mockResolvedValue({
      query: 'Commerzbank',
      total: 1,
      items: [{ symbol: 'CBK.DE', company_name: 'Commerzbank AG', display_name: 'Commerzbank AG', currency: 'EUR' }],
    })
    vi.mocked(apiClient.marketdataProfile).mockResolvedValue({
      symbol: 'CBK.DE',
      company_name: 'Commerzbank AG',
      isin: 'DE000CBK1001',
      exchange: 'XETRA',
      currency: 'EUR',
      price: 18.35,
    })

    const wrapper = mount(DepotHoldingsManager, { props: { personId: 'person-1', depotLabel: 'Depot Core' } })
    await flushUi()

    await wrapper.find('input[placeholder*="Name / Symbol / ISIN / WKN"]').setValue('Commerzbank')
    await vi.advanceTimersByTimeAsync(1000)
    await flushUi()
    await wrapper.find('ul.search-list button').trigger('click')
    await flushUi()

    expect((wrapper.find('[data-testid="holding-symbol"]').element as HTMLInputElement).value).toBe('CBK.DE')
    expect((wrapper.find('[data-testid="holding-isin"]').element as HTMLInputElement).value).toBe('DE000CBK1001')
    expect((wrapper.find('[data-testid="holding-company-name"]').element as HTMLInputElement).value).toBe('Commerzbank AG')
    expect((wrapper.find('[data-testid="holding-exchange"]').element as HTMLInputElement).value).toBe('XETRA')
    expect((wrapper.find('[data-testid="holding-currency"]').element as HTMLInputElement).value).toBe('EUR')
    expect((wrapper.find('[data-testid="holding-acquisition-price"]').element as HTMLInputElement).value).toBe('18.35')
    expect((wrapper.find('[data-testid="holding-asset-type"]').element as HTMLInputElement).value).toBe('')
  })

  it('shows errors for failed search and failed profile requests', async () => {
    vi.mocked(apiClient.searchInstruments).mockRejectedValueOnce(new Error('Search failed'))
      .mockResolvedValueOnce({
        query: 'Commerzbank',
        total: 1,
        items: [{ symbol: 'CBK.DE', company_name: 'Commerzbank AG', display_name: 'Commerzbank AG', currency: 'EUR' }],
      })
    vi.mocked(apiClient.marketdataProfile).mockRejectedValueOnce(new Error('Profile failed'))

    const wrapper = mount(DepotHoldingsManager, { props: { personId: 'person-1', depotLabel: 'Depot Core' } })
    await flushUi()

    const input = wrapper.find('input[placeholder*="Name / Symbol / ISIN / WKN"]')
    await input.setValue('Commerzbank')
    await vi.advanceTimersByTimeAsync(1000)
    await flushUi()
    expect(wrapper.text()).toContain('Search failed')

    await input.setValue('Commerzbank AG')
    await vi.advanceTimersByTimeAsync(1000)
    await flushUi()
    await wrapper.find('ul.search-list button').trigger('click')
    await flushUi()

    expect(wrapper.text()).toContain('Profile failed')
  })
})
