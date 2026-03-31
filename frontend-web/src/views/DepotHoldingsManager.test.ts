// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

import DepotHoldingsManager from './DepotHoldingsManager.vue'
import { apiClient } from '../api/client'

vi.mock('../api/client', () => ({
  apiClient: {
    portfolios: vi.fn(),
    createPortfolio: vi.fn(),
    portfolio: vi.fn(),
    searchInstruments: vi.fn(),
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

describe('DepotHoldingsManager', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
    vi.mocked(apiClient.portfolios).mockResolvedValue({
      items: [{ portfolio_id: 'p1', person_id: 'person-1', display_name: 'Depot Core', created_at: 'x', updated_at: 'x' }],
      total: 1,
    })
    vi.mocked(apiClient.portfolio).mockResolvedValue({
      portfolio_id: 'p1', person_id: 'person-1', display_name: 'Depot Core', created_at: 'x', updated_at: 'x',
      holdings: [{ holding_id: 'h1', portfolio_id: 'p1', symbol: 'AAPL', quantity: 2, acquisition_price: 100, currency: 'USD', buy_date: '2026-03-01', created_at: 'x', updated_at: 'x' }],
    })
    vi.mocked(apiClient.searchInstruments).mockResolvedValue({ query: 'AAPL', total: 1, items: [{ symbol: 'AAPL', company_name: 'Apple', display_name: 'Apple', currency: 'USD', last_price: 170 }] })
    vi.mocked(apiClient.addHolding).mockResolvedValue({} as never)
    vi.mocked(apiClient.updateHolding).mockResolvedValue({} as never)
    vi.mocked(apiClient.deleteHolding).mockResolvedValue(undefined)
    vi.mocked(apiClient.createPortfolio).mockResolvedValue({ portfolio_id: 'p2', person_id: 'person-1', display_name: 'Depot Core', created_at: 'x', updated_at: 'x' })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('runs search while typing (debounced), no explicit search button, then adds holding', async () => {
    const wrapper = mount(DepotHoldingsManager, { props: { personId: 'person-1', depotLabel: 'Depot Core' } })
    await flushUi()
    expect(wrapper.findAll('button').some((b) => b.text() === 'Suchen')).toBe(false)
    await wrapper.find('input[placeholder*="Name / Symbol / ISIN / WKN"]').setValue('AAPL')
    await vi.advanceTimersByTimeAsync(350)
    await flushUi()
    expect(apiClient.searchInstruments).toHaveBeenCalledWith('AAPL')
    await wrapper.find('ul.search-list button').trigger('click')
    await flushUi()
    await wrapper.find('form.holding-form').trigger('submit.prevent')
    await flushUi()

    expect(apiClient.addHolding).toHaveBeenCalledWith('p1', expect.objectContaining({ symbol: 'AAPL' }))
  })

  it('refreshes results while typing and handles empty search state', async () => {
    vi.mocked(apiClient.searchInstruments)
      .mockResolvedValueOnce({ query: 'AAP', total: 1, items: [{ symbol: 'AAPL', company_name: 'Apple', display_name: 'Apple' }] })
      .mockResolvedValueOnce({ query: 'ZZZ', total: 0, items: [] })
    const wrapper = mount(DepotHoldingsManager, { props: { personId: 'person-1', depotLabel: 'Depot Core' } })
    await flushUi()
    const input = wrapper.find('input[placeholder*="Name / Symbol / ISIN / WKN"]')
    await input.setValue('AAP')
    await vi.advanceTimersByTimeAsync(350)
    await flushUi()
    expect(wrapper.text()).toContain('Apple')

    await input.setValue('ZZZ')
    await vi.advanceTimersByTimeAsync(350)
    await flushUi()
    expect(wrapper.text()).toContain('Keine Treffer gefunden.')
  })

  it('updates and deletes an existing holding', async () => {
    const wrapper = mount(DepotHoldingsManager, { props: { personId: 'person-1', depotLabel: 'Depot Core' } })
    await vi.runAllTimersAsync()
    await flushUi()

    expect(wrapper.text()).toContain('Bearbeiten')
    const editButton = wrapper.findAll('button').find((b) => b.text().includes('Bearbeiten'))
    expect(editButton).toBeTruthy()
    await editButton!.trigger('click')
    await flushUi()
    const editForm = wrapper.findAll('form.holding-form').at(-1)
    expect(editForm).toBeTruthy()
    await editForm!.trigger('submit.prevent')
    await flushUi()

    expect(apiClient.updateHolding).toHaveBeenCalledWith('p1', 'h1', expect.any(Object))

    const deleteButton = wrapper.findAll('button').find((b) => b.text().includes('Löschen'))
    expect(deleteButton).toBeTruthy()
    await deleteButton!.trigger('click')
    await flushUi()
    expect(apiClient.deleteHolding).toHaveBeenCalledWith('p1', 'h1')
  })
})
