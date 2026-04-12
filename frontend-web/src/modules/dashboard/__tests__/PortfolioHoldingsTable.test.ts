// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PortfolioHoldingsTable from '@/modules/dashboard/components/PortfolioHoldingsTable.vue'
import type { PortfolioHoldingItem } from '@/shared/model/types'

function holding(overrides: Partial<PortfolioHoldingItem> = {}): PortfolioHoldingItem {
  return {
    portfolio_id: 'p-1',
    holding_id: 'h-1',
    symbol: 'AAPL',
    display_name: 'Apple',
    quantity: 2,
    acquisition_price: 100,
    current_price: 110,
    invested_value: 200,
    market_value: 220,
    unrealized_pnl: 20,
    unrealized_return_pct: 10,
    weight: 0.6,
    sector: 'Technology',
    country: 'US',
    currency: 'USD',
    data_status: 'ok',
    ...overrides
  }
}

describe('PortfolioHoldingsTable', () => {
  it('renders the normal prioritized table and keeps selection behavior', async () => {
    const wrapper = mount(PortfolioHoldingsTable, {
      props: {
        items: [
          holding(),
          holding({
            holding_id: 'h-2',
            symbol: 'MSFT',
            display_name: 'Microsoft',
            quantity: 1,
            acquisition_price: 150,
            current_price: 140,
            invested_value: 150,
            market_value: 140,
            unrealized_pnl: -10,
            unrealized_return_pct: -6.67,
            weight: 0.4,
            data_status: 'fallback_acquisition_price',
            warnings: ['missing_current_price']
          }),
          holding({
            holding_id: 'h-3',
            symbol: 'SAP',
            display_name: 'SAP',
            market_value: 100,
            unrealized_pnl: 0,
            weight: 0.2,
            country: 'DE'
          }),
          holding({
            holding_id: 'h-4',
            symbol: 'NESN',
            display_name: 'Nestle',
            market_value: 80,
            weight: 0.1,
            sector: 'Consumer Staples',
            country: 'CH'
          })
        ],
        selectedSymbol: 'AAPL'
      }
    })

    expect(wrapper.get('table').classes()).toContain('holdings-table')
    expect(wrapper.get('table').classes()).not.toContain('holdings-table--small')
    expect(wrapper.get('[data-test="holdings-table-wrap"]').classes()).not.toContain('table-wrap--small')
    expect(wrapper.findAll('col').map((col) => col.classes()[0])).toEqual([
      'col-symbol',
      'col-name',
      'col-weight',
      'col-market-value',
      'col-pnl',
      'col-return',
      'col-sector',
      'col-country',
      'col-status'
    ])
    expect(wrapper.findAll('thead .cell-number')).toHaveLength(4)

    const rows = wrapper.findAll('tbody tr')
    expect(rows[0].classes()).toContain('active')
    expect(rows[0].findAll('.cell-number')).toHaveLength(4)

    await rows[1].trigger('click')
    const emitted = wrapper.emitted('select-holding')
    const selectedItem = emitted?.[0]?.[0] as { symbol?: string } | undefined
    expect(emitted).toBeTruthy()
    expect(selectedItem?.symbol).toBe('MSFT')
    expect(wrapper.text()).toContain('Preis-Fallback')
    expect(wrapper.text()).toContain('Aktueller Preis fehlt')
  })

  it('truncates long instrument names and sectors with full title text', () => {
    const longName = 'Vanguard FTSE All-World UCITS ETF Accumulating mit sehr langem Anzeigenamen'
    const longSector = 'Information Technology Services and Semiconductor Infrastructure'
    const wrapper = mount(PortfolioHoldingsTable, {
      props: {
        items: [
          holding({
            display_name: longName,
            sector: longSector
          })
        ]
      }
    })

    const nameCell = wrapper.get('td.cell-name')
    const sectorCell = wrapper.get('td.cell-sector')

    expect(nameCell.classes()).toContain('text-truncate')
    expect(nameCell.attributes('title')).toBe(longName)
    expect(nameCell.text()).toBe(longName)
    expect(sectorCell.classes()).toContain('text-truncate')
    expect(sectorCell.attributes('title')).toBe(longSector)
    expect(sectorCell.text()).toBe(longSector)
  })

  it('summarizes multiple warnings and keeps the full warning text in the title', () => {
    const wrapper = mount(PortfolioHoldingsTable, {
      props: {
        items: [
          holding({
            warnings: ['missing_current_price', 'missing_price', 'fallback_acquisition_price_used']
          })
        ]
      }
    })

    const warningSummary = wrapper.get('.warning-summary')

    expect(warningSummary.attributes('title')).toBe(
      'Aktueller Preis fehlt, Preis fehlt, Fallback auf Einstandspreis aktiv'
    )
    expect(warningSummary.get('.warning-text').text()).toBe('Aktueller Preis fehlt')
    expect(warningSummary.get('.warning-count').text()).toBe('+2')
    expect(warningSummary.get('.warning-count').attributes('aria-label')).toContain(
      '2 weitere Warnungen: Preis fehlt, Fallback auf Einstandspreis aktiv'
    )
  })

  it('renders missing optional values compactly', () => {
    const wrapper = mount(PortfolioHoldingsTable, {
      props: {
        items: [
          holding({
            symbol: null,
            display_name: '   ',
            portfolio_name: null,
            unrealized_return_pct: null,
            sector: null,
            country: undefined,
            data_status: ''
          })
        ]
      }
    })

    expect(wrapper.get('td.cell-symbol').text()).toBe('n/a')
    expect(wrapper.get('td.cell-symbol').attributes('title')).toBe('n/a')
    expect(wrapper.get('td.cell-name').text()).toBe('n/a')
    expect(wrapper.get('td.cell-name').attributes('title')).toBe('n/a')
    expect(wrapper.get('td.cell-sector').text()).toBe('n/a')
    expect(wrapper.get('td.cell-country').text()).toBe('n/a')
    expect(wrapper.findAll('td.cell-number').at(3)?.text()).toBe('n/a')
    expect(wrapper.text()).toContain('Unbekannt')
    expect(wrapper.find('.warning-summary').exists()).toBe(false)
  })

  it('uses the readable small-table layout for a 1-holding portfolio', () => {
    const wrapper = mount(PortfolioHoldingsTable, {
      props: {
        items: [holding()]
      }
    })

    expect(wrapper.get('[data-test="holdings-table-wrap"]').classes()).toContain('table-wrap--small')
    expect(wrapper.get('table').classes()).toContain('holdings-table--small')
    expect(wrapper.findAll('tbody tr')).toHaveLength(1)
    expect(wrapper.get('td.cell-name').text()).toBe('Apple')
  })

  it('renders an empty state when there are no holdings', () => {
    const wrapper = mount(PortfolioHoldingsTable, {
      props: {
        items: []
      }
    })

    expect(wrapper.get('[data-test="holdings-table-wrap"]').classes()).toContain('table-wrap--small')
    expect(wrapper.get('table').classes()).toContain('holdings-table--small')
    expect(wrapper.get('.empty-row').text()).toBe('Keine Holdings vorhanden.')
    expect(wrapper.get('.empty-row').attributes('colspan')).toBe('9')
    expect(wrapper.emitted('select-holding')).toBeUndefined()
  })
})
