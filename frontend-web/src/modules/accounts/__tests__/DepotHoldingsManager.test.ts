// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

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

async function mountManager() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', component: DepotHoldingsManager }],
  })
  await router.push('/')
  await router.isReady()
  const wrapper = mount(DepotHoldingsManager, {
    props: { personId: 'person-1', depotLabel: 'Depot Core' },
    global: { plugins: [router] },
  })
  return { wrapper, router }
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

    const { wrapper } = await mountManager()
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

    const { wrapper } = await mountManager()
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
    expect(wrapper.find('ul.search-list button.result-item--compact').exists()).toBe(true)
  })

  it('opens detail form without separate profile overview and renders profile data in one mask', async () => {
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
      isin: 'DE000CBK1001',
      wkn: 'CBK100',
      quote_type: 'NASDAQ Global Select',
      asset_type: 'Stock',
      industry: 'Banks',
      website: 'www.commerzbank.de',
      ceo: 'Bettina Orlopp',
      sector: 'Financial Services',
      country: 'DE',
      phone: '+49 69 136 20',
      address: 'Kaiserplatz',
      zip: '60311',
      city: 'Frankfurt am Main',
      image: 'https://example.com/logo.png',
      description: 'Deutsche Geschäftsbank.',
      price: 18.35,
    })

    const { wrapper } = await mountManager()
    await flushUi()

    await wrapper.find('input[placeholder*="Name / Symbol / ISIN / WKN"]').setValue('Commerzbank')
    await vi.advanceTimersByTimeAsync(1000)
    await flushUi()

    await wrapper.find('ul.search-list button').trigger('click')
    await flushUi()

    expect(wrapper.text()).toContain('← Zurück')
    expect(wrapper.text()).toContain('Position bearbeiten: Commerzbank AG')
    expect(apiClient.marketdataProfile).toHaveBeenCalledWith('CBK.DE')
    expect(wrapper.text()).not.toContain('Profilübersicht')
    expect(wrapper.findAll('form.holding-form').length).toBe(1)
    const formText = wrapper.find('form.holding-form').text()
    expect(formText).toContain('WKN')
    expect(formText).toContain('Quote-Type')
    expect(formText).toContain('Asset-Type')
    expect(formText).toContain('Industrie')
    expect(formText).toContain('Adresse')
    expect(formText).toContain('Beschreibung')
    expect(formText).toContain('Deutsche Geschäftsbank.')
    expect(formText).not.toContain('ipo_date')
    expect(formText).not.toContain('default_image')
    expect((wrapper.find('input[readonly][value="Banks"]').element as HTMLInputElement).value).toBe('Banks')
    expect((wrapper.find('input[readonly][value="Kaiserplatz, 60311 Frankfurt am Main"]').element as HTMLInputElement).value).toBe('Kaiserplatz, 60311 Frankfurt am Main')
    const websiteLink = wrapper.find('a[href="https://www.commerzbank.de"]')
    expect(websiteLink.exists()).toBe(true)
    expect(wrapper.find('img.profile-image--inline').attributes('src')).toBe('https://example.com/logo.png')
    expect(wrapper.find('ul.search-list').exists()).toBe(false)
  })

  it('prefills holding form from loaded profile and keeps only quantity, buy date and notes editable', async () => {
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
      website: 'www.commerzbank.de',
    })

    const { wrapper } = await mountManager()
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
    expect(wrapper.find('[data-testid="holding-asset-type"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="holding-quote-type"]').exists()).toBe(false)

    const allEditableInputs = wrapper
      .find('form.holding-form')
      .findAll('input')
      .filter((input) => input.attributes('readonly') === undefined)
      .map((input) => input.attributes('data-testid'))
    expect(allEditableInputs).toEqual(['holding-quantity', 'holding-buy-date', 'holding-notes'])

    expect(wrapper.find('[data-testid="holding-symbol"]').attributes('readonly')).toBeDefined()
    expect(wrapper.find('[data-testid="holding-isin"]').attributes('readonly')).toBeDefined()
    expect(wrapper.find('[data-testid="holding-acquisition-price"]').attributes('readonly')).toBeDefined()
    expect(wrapper.find('[data-testid="holding-currency"]').attributes('readonly')).toBeDefined()
    expect(wrapper.find('a[href="https://www.commerzbank.de"]').exists()).toBe(true)
  })

  it('does not render empty optional profile fields and keeps address in one line', async () => {
    vi.mocked(apiClient.searchInstruments).mockResolvedValue({
      query: 'Commerzbank',
      total: 1,
      items: [{ symbol: 'CBK.DE', company_name: 'Commerzbank AG', display_name: 'Commerzbank AG' }],
    })
    vi.mocked(apiClient.marketdataProfile).mockResolvedValue({
      symbol: 'CBK.DE',
      company_name: 'Commerzbank AG',
      isin: 'DE000CBK1001',
      currency: 'EUR',
      price: 18.35,
      industry: 'Banks',
      address: 'Kaiserplatz',
      zip: '60311',
      city: 'Frankfurt am Main',
      description: 'Kurzbeschreibung',
      website: '',
      ceo: '',
      sector: '',
      country: '',
      phone: '',
      wkn: '',
      quote_type: '',
      asset_type: '',
    })

    const { wrapper } = await mountManager()
    await flushUi()
    await wrapper.find('input[placeholder*="Name / Symbol / ISIN / WKN"]').setValue('Commerzbank')
    await vi.advanceTimersByTimeAsync(1000)
    await flushUi()
    await wrapper.find('ul.search-list button').trigger('click')
    await flushUi()

    const formText = wrapper.find('form.holding-form').text()
    expect(formText).toContain('Industrie')
    expect(formText).toContain('Adresse')
    expect(formText).toContain('Beschreibung')
    expect(formText).not.toContain('CEO')
    expect(formText).not.toContain('Sektor')
    expect(formText).not.toContain('Land')
    expect(formText).not.toContain('Telefon')
    expect(formText).not.toContain('Quote-Type')
    expect(formText).not.toContain('Asset-Type')
    expect(formText).not.toContain('WKN')
    expect(wrapper.find('.profile-link').exists()).toBe(false)
    expect((wrapper.find('input[readonly][value="Kaiserplatz, 60311 Frankfurt am Main"]').element as HTMLInputElement).value).toBe('Kaiserplatz, 60311 Frankfurt am Main')
  })

  it('keeps search query and result list after returning from detail view', async () => {
    vi.mocked(apiClient.searchInstruments).mockResolvedValue({
      query: 'Commerzbank',
      total: 1,
      items: [{ symbol: 'CBK.DE', company_name: 'Commerzbank AG', display_name: 'Commerzbank AG', currency: 'EUR' }],
    })
    vi.mocked(apiClient.marketdataProfile).mockResolvedValue({
      symbol: 'CBK.DE',
      company_name: 'Commerzbank AG',
      currency: 'EUR',
      price: 18.35,
    })

    const { wrapper } = await mountManager()
    await flushUi()

    const input = wrapper.find('input[placeholder*="Name / Symbol / ISIN / WKN"]')
    await input.setValue('Commerzbank')
    await vi.advanceTimersByTimeAsync(1000)
    await flushUi()
    await wrapper.find('ul.search-list button').trigger('click')
    await flushUi()
    expect(wrapper.text()).toContain('← Zurück')
    await wrapper.find('button.btn.secondary').trigger('click')
    await flushUi()

    expect((wrapper.find('input[placeholder*="Name / Symbol / ISIN / WKN"]').element as HTMLInputElement).value).toBe('Commerzbank')
    expect(wrapper.find('ul.search-list').text()).toContain('CBK.DE')
    expect(wrapper.find('form.holding-form').exists()).toBe(false)
  })

  it('shows errors for failed search and failed profile requests', async () => {
    vi.mocked(apiClient.searchInstruments).mockRejectedValueOnce(new Error('Search failed'))
      .mockResolvedValueOnce({
        query: 'Commerzbank',
        total: 1,
        items: [{ symbol: 'CBK.DE', company_name: 'Commerzbank AG', display_name: 'Commerzbank AG', currency: 'EUR' }],
      })
    vi.mocked(apiClient.marketdataProfile).mockRejectedValueOnce(new Error('Profile failed'))

    const { wrapper } = await mountManager()
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
