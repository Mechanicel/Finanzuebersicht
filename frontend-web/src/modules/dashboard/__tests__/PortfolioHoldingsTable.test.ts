// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PortfolioHoldingsTable from '@/modules/dashboard/components/PortfolioHoldingsTable.vue'

describe('PortfolioHoldingsTable', () => {
  it('emits select-holding and marks selected row', async () => {
    const wrapper = mount(PortfolioHoldingsTable, {
      props: {
        items: [
          {
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
            data_status: 'ok'
          },
          {
            portfolio_id: 'p-1',
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
            sector: 'Technology',
            country: 'US',
            currency: 'USD',
            data_status: 'fallback_acquisition_price',
            warnings: ['missing_current_price']
          }
        ],
        selectedSymbol: 'AAPL'
      }
    })

    const rows = wrapper.findAll('tbody tr')
    expect(rows[0].classes()).toContain('active')

    await rows[1].trigger('click')
    const emitted = wrapper.emitted('select-holding')
    const selectedItem = emitted?.[0]?.[0] as { symbol?: string } | undefined
    expect(emitted).toBeTruthy()
    expect(selectedItem?.symbol).toBe('MSFT')
    expect(wrapper.text()).toContain('Preis-Fallback')
    expect(wrapper.text()).toContain('Aktueller Preis fehlt')
  })
})
