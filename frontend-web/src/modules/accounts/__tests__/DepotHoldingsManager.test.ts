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
    refreshHoldingPrices: vi.fn(),
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
    vi.mocked(apiClient.refreshHoldingPrices).mockResolvedValue({
      portfolio_id: 'p1',
      status: 'not_implemented_yet',
      accepted: false,
      detail: 'Technischer Refresh-Flow vorbereitet. Marktpreislogik folgt in einem späteren Schritt.',
    } as never)
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

  it('opens detail form without separate profile overview and renders extended profile data', async () => {
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

    expect(wrapper.find('[data-testid="detail-back-button"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Position bearbeiten: Commerzbank AG')
    expect(apiClient.marketdataProfile).toHaveBeenCalledWith('CBK.DE')
    expect(wrapper.text()).not.toContain('Profilübersicht')
    expect(wrapper.findAll('form.holding-form').length).toBe(1)
    const formText = wrapper.find('form.holding-form').text()
    expect(formText).toContain('WKN')
    expect(formText).toContain('Börsenplatz')
    expect(formText).toContain('Quote-Type')
    expect(formText).toContain('Asset-Type')
    expect(formText).toContain('Industrie')
    expect(formText).toContain('Adresse')
    expect(formText).toContain('Beschreibung')
    expect(formText).toContain('Deutsche Geschäftsbank.')
    expect(formText).not.toContain('ipo_date')
    expect(formText).not.toContain('default_image')
    expect(wrapper.findAll('.profile-description-block').some((node) => node.text() === 'Banks')).toBe(true)
    expect(wrapper.findAll('.profile-description-block').some((node) => node.text() === 'Deutsche Börse Xetra')).toBe(true)
    expect(wrapper.find('[data-testid="holding-address"]').text()).toBe('Kaiserplatz, 60311 Frankfurt am Main')
    expect(wrapper.find('[data-testid="holding-description"]').text()).toBe('Deutsche Geschäftsbank.')
    const websiteLink = wrapper.find('[data-testid="holding-website-link"]')
    expect(websiteLink.exists()).toBe(true)
    expect(websiteLink.attributes('href')).toBe('https://www.commerzbank.de')
    expect(wrapper.find('img.profile-image--inline').attributes('src')).toBe('https://example.com/logo.png')
    expect(wrapper.find('ul.search-list').exists()).toBe(false)
  })

  it('prefills holding form from loaded profile and keeps only quantity, buy date, notes and acquisition price editable', async () => {
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

    expect(wrapper.find('[data-testid="holding-symbol"]').text()).toBe('CBK.DE')
    expect(wrapper.find('[data-testid="holding-isin"]').text()).toBe('DE000CBK1001')
    expect(wrapper.find('[data-testid="holding-company-name"]').text()).toBe('Commerzbank AG')
    expect(wrapper.find('[data-testid="holding-exchange"]').text()).toBe('XETRA')
    expect(wrapper.find('[data-testid="holding-currency"]').text()).toBe('EUR')
    expect((wrapper.find('[data-testid="holding-acquisition-price"]').element as HTMLInputElement).value).toBe('18.35')
    expect(wrapper.find('[data-testid="holding-asset-type"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="holding-quote-type"]').exists()).toBe(false)

    const allEditableInputs = wrapper
      .find('form.holding-form')
      .findAll('input')
      .filter((input) => input.attributes('readonly') === undefined)
      .map((input) => input.attributes('data-testid'))
    expect(allEditableInputs).toEqual(['holding-quantity', 'holding-acquisition-price', 'holding-buy-date', 'holding-notes'])

    expect(wrapper.find('[data-testid="holding-symbol"]').element.tagName).toBe('DIV')
    expect(wrapper.find('[data-testid="holding-isin"]').element.tagName).toBe('DIV')
    expect(wrapper.find('[data-testid="holding-currency"]').element.tagName).toBe('DIV')
    expect(wrapper.find('[data-testid="holding-website-link"]').attributes('href')).toBe('https://www.commerzbank.de')
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
    expect(wrapper.find('[data-testid="holding-website-link"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="holding-address"]').text()).toBe('Kaiserplatz, 60311 Frankfurt am Main')
    expect(wrapper.find('[data-testid="holding-description"]').text()).toBe('Kurzbeschreibung')
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
    expect(wrapper.find('[data-testid="detail-back-button"]').exists()).toBe(true)
    await wrapper.find('[data-testid="detail-back-button"]').trigger('click')
    await flushUi()

    expect((wrapper.find('input[placeholder*="Name / Symbol / ISIN / WKN"]').element as HTMLInputElement).value).toBe('Commerzbank')
    expect(wrapper.find('ul.search-list').text()).toContain('CBK.DE')
    expect(wrapper.find('form.holding-form').exists()).toBe(false)
  })

  it('renders top action bar right-aligned with save and back buttons and without bottom save button', async () => {
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
    await wrapper.find('input[placeholder*="Name / Symbol / ISIN / WKN"]').setValue('Commerzbank')
    await vi.advanceTimersByTimeAsync(1000)
    await flushUi()
    await wrapper.find('ul.search-list button').trigger('click')
    await flushUi()

    const actionBar = wrapper.find('[data-testid="detail-top-actions"]')
    expect(actionBar.exists()).toBe(true)
    expect(actionBar.find('[data-testid="detail-save-button"]').exists()).toBe(true)
    expect(actionBar.find('[data-testid="detail-back-button"]').exists()).toBe(true)
    expect(wrapper.findAll('button[type="submit"]').length).toBe(1)
  })

  it('navigates back to search after successful save and preserves search state', async () => {
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

    const searchInput = wrapper.find('input[placeholder*="Name / Symbol / ISIN / WKN"]')
    await searchInput.setValue('Commerzbank')
    await vi.advanceTimersByTimeAsync(1000)
    await flushUi()
    await wrapper.find('ul.search-list button').trigger('click')
    await flushUi()

    await wrapper.find('[data-testid="holding-quantity"]').setValue('5')
    await wrapper.find('[data-testid="holding-acquisition-price"]').setValue('19.5')
    await wrapper.find('form#holding-create-form').trigger('submit.prevent')
    await flushUi()

    expect(apiClient.addHolding).toHaveBeenCalledTimes(1)
    expect(vi.mocked(apiClient.addHolding).mock.calls[0]?.[1]).toMatchObject({
      quantity: 5,
      acquisition_price: 19.5,
    })
    expect(wrapper.find('form.holding-form').exists()).toBe(false)
    expect((wrapper.find('input[placeholder*="Name / Symbol / ISIN / WKN"]').element as HTMLInputElement).value).toBe('Commerzbank')
    expect(wrapper.find('ul.search-list').text()).toContain('CBK.DE')
  })

  it('stays in detail view when save fails', async () => {
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
    vi.mocked(apiClient.addHolding).mockRejectedValueOnce(new Error('Save failed'))

    const { wrapper } = await mountManager()
    await flushUi()
    await wrapper.find('input[placeholder*="Name / Symbol / ISIN / WKN"]').setValue('Commerzbank')
    await vi.advanceTimersByTimeAsync(1000)
    await flushUi()
    await wrapper.find('ul.search-list button').trigger('click')
    await flushUi()

    await wrapper.find('form#holding-create-form').trigger('submit.prevent')
    await flushUi()

    expect(wrapper.find('form.holding-form').exists()).toBe(true)
    expect(wrapper.text()).toContain('Save failed')
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

  it('opens holding edit view by clicking the full holding row and has no Bearbeiten button', async () => {
    vi.mocked(apiClient.portfolio).mockResolvedValueOnce({
      portfolio_id: 'p1',
      person_id: 'person-1',
      display_name: 'Depot Core',
      created_at: 'x',
      updated_at: 'x',
      holdings: [{
        holding_id: 'h1',
        symbol: 'CBK.DE',
        isin: 'DE000CBK1001',
        display_name: 'Commerzbank AG',
        company_name: 'Commerzbank AG',
        quantity: 10,
        acquisition_price: 18.4,
        currency: 'EUR',
        buy_date: '2026-01-10',
        notes: 'Langfristig',
      }],
    })

    const { wrapper } = await mountManager()
    await flushUi()

    expect(wrapper.text()).not.toContain('Bearbeiten')
    expect(wrapper.find('button.holding-row-button').exists()).toBe(true)
    expect(wrapper.find('form.holding-form').exists()).toBe(false)

    await wrapper.find('button.holding-row-button').trigger('click')
    await flushUi()

    expect(wrapper.find('form.holding-form').exists()).toBe(true)
  })

  it('uses delete icon as separate action with confirm dialog and hover-target class', async () => {
    vi.mocked(apiClient.portfolio).mockResolvedValueOnce({
      portfolio_id: 'p1',
      person_id: 'person-1',
      display_name: 'Depot Core',
      created_at: 'x',
      updated_at: 'x',
      holdings: [{
        holding_id: 'h1',
        symbol: 'CBK.DE',
        quantity: 10,
        acquisition_price: 18.4,
        currency: 'EUR',
        buy_date: '2026-01-10',
        notes: null,
      }],
    } as never)
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

    const { wrapper } = await mountManager()
    await flushUi()

    const deleteButton = wrapper.find('button.holding-delete-button')
    expect(deleteButton.exists()).toBe(true)
    expect(deleteButton.find('svg.delete-icon').exists()).toBe(true)

    await deleteButton.trigger('click')
    await flushUi()

    expect(confirmSpy).toHaveBeenCalledWith('Position wirklich löschen?')
    expect(apiClient.deleteHolding).toHaveBeenCalledWith('p1', 'h1')
    expect(wrapper.find('form.holding-form').exists()).toBe(false)
  })

  it('shows refresh button and triggers refresh flow through api client', async () => {
    vi.mocked(apiClient.portfolio).mockResolvedValueOnce({
      portfolio_id: 'p1',
      person_id: 'person-1',
      display_name: 'Depot Core',
      created_at: 'x',
      updated_at: 'x',
      holdings: [],
    })

    const { wrapper } = await mountManager()
    await flushUi()

    const refreshButton = wrapper.find('[data-testid="holdings-refresh-button"]')
    expect(refreshButton.exists()).toBe(true)
    expect(refreshButton.text()).toContain('Aktualisieren')

    await refreshButton.trigger('click')
    await flushUi()

    expect(apiClient.refreshHoldingPrices).toHaveBeenCalledWith('p1')
    expect(wrapper.text()).toContain('Aktualisierung ausgelöst:')
  })

  it('filters holdings list client-side by symbol, isin and company name', async () => {
    vi.mocked(apiClient.portfolio).mockResolvedValueOnce({
      portfolio_id: 'p1',
      person_id: 'person-1',
      display_name: 'Depot Core',
      created_at: 'x',
      updated_at: 'x',
      holdings: [
        {
          holding_id: 'h1',
          symbol: 'CBK.DE',
          isin: 'DE000CBK1001',
          display_name: 'Commerzbank AG',
          company_name: 'Commerzbank AG',
          quantity: 10,
          acquisition_price: 18.4,
          currency: 'EUR',
          buy_date: '2026-01-10',
          notes: null,
        },
        {
          holding_id: 'h2',
          symbol: 'AAPL',
          isin: 'US0378331005',
          display_name: 'Apple Inc.',
          company_name: 'Apple Inc.',
          quantity: 5,
          acquisition_price: 199,
          currency: 'USD',
          buy_date: '2026-02-02',
          notes: null,
        }
      ],
    } as never)

    const { wrapper } = await mountManager()
    await flushUi()

    const filterInput = wrapper.find('#holding-filter-input')
    expect(wrapper.text()).toContain('CBK.DE')
    expect(wrapper.text()).toContain('AAPL')

    await filterInput.setValue('US0378331005')
    await flushUi()
    expect(wrapper.text()).toContain('AAPL')
    expect(wrapper.text()).not.toContain('CBK.DE')

    await filterInput.setValue('Commerzbank')
    await flushUi()
    expect(wrapper.text()).toContain('CBK.DE')
    expect(wrapper.text()).not.toContain('AAPL')

    await filterInput.setValue('')
    await flushUi()
    expect(wrapper.text()).toContain('CBK.DE')
    expect(wrapper.text()).toContain('AAPL')
  })
})
