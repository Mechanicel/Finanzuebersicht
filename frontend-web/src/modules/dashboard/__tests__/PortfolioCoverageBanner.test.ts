// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PortfolioCoverageBanner from '@/modules/dashboard/components/PortfolioCoverageBanner.vue'
import type { PortfolioDataCoverageReadModel } from '@/shared/model/types'

function makeCoverage(overrides: Partial<PortfolioDataCoverageReadModel> = {}): PortfolioDataCoverageReadModel {
  return {
    person_id: 'person-1',
    as_of: '2026-04-10',
    total_holdings: 18,
    missing_prices: 0,
    missing_sectors: 0,
    missing_countries: 0,
    missing_currencies: 0,
    fallback_acquisition_prices: 0,
    holdings_with_marketdata_warnings: 0,
    warnings: [],
    meta: {},
    ...overrides
  }
}

describe('PortfolioCoverageBanner', () => {
  it('renders a compact ok state for complete coverage', () => {
    const wrapper = mount(PortfolioCoverageBanner, {
      props: { coverage: makeCoverage() }
    })

    expect(wrapper.get('[data-test="coverage-status"]').text()).toBe('OK')
    expect(wrapper.text()).toContain('Datenabdeckung ok')
    expect(wrapper.text()).toContain('18 Holdings')
    expect(wrapper.get('[data-test="coverage-indicators"]').text()).toContain('Keine Datenlücken')
    expect(wrapper.find('[data-test="coverage-warning-summary"]').exists()).toBe(false)
  })

  it('highlights data quality gaps and summarizes warnings', () => {
    const wrapper = mount(PortfolioCoverageBanner, {
      props: {
        coverage: makeCoverage({
          missing_prices: 1,
          missing_sectors: 2,
          fallback_acquisition_prices: 1,
          holdings_with_marketdata_warnings: 3,
          warnings: [
            'missing_sector_data',
            'fallback_acquisition_price_used',
            'holdings_with_marketdata_warnings',
            'missing_currency_data'
          ]
        })
      }
    })

    expect(wrapper.get('[data-test="coverage-banner"]').classes()).toContain('coverage--critical')
    expect(wrapper.get('[data-test="coverage-status"]').text()).toContain('7 Signale')
    expect(wrapper.get('[data-indicator="missing-prices"]').text()).toContain('1 Preise fehlen')
    expect(wrapper.get('[data-indicator="missing-sectors"]').text()).toContain('2 Sektoren fehlen')
    expect(wrapper.get('[data-test="coverage-warning-count"]').text()).toContain('4 Hinweise')
    expect(wrapper.get('[data-test="coverage-warning-summary"]').text()).toContain('Sektordaten unvollständig')
    expect(wrapper.get('[data-test="coverage-warning-summary"]').text()).toContain('+1 weitere')
  })

  it('handles missing optional coverage fields without noisy indicators', () => {
    const coverageWithoutOptionalFields = {
      person_id: 'person-1',
      as_of: '2026-04-10',
      total_holdings: 18,
      missing_prices: 0,
      missing_sectors: 0,
      missing_countries: 0,
      missing_currencies: 0,
      meta: {}
    } as PortfolioDataCoverageReadModel
    const wrapper = mount(PortfolioCoverageBanner, {
      props: { coverage: coverageWithoutOptionalFields }
    })

    expect(wrapper.get('[data-test="coverage-status"]').text()).toBe('OK')
    expect(wrapper.get('[data-test="coverage-indicators"]').text()).toContain('Keine Datenlücken')
    expect(wrapper.text()).not.toContain('Preis-Fallbacks')
    expect(wrapper.text()).not.toContain('undefined')
  })
})
