// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import PortfolioExposuresPanel from '@/modules/dashboard/components/PortfolioExposuresPanel.vue'
import type { PortfolioExposureSlice, PortfolioExposuresReadModel } from '@/shared/model/types'

function exposure(label: string, weight: number, marketValue = weight * 100000): PortfolioExposureSlice {
  return {
    label,
    weight,
    market_value: marketValue
  }
}

function buildExposures(overrides: Partial<PortfolioExposuresReadModel> = {}): PortfolioExposuresReadModel {
  return {
    person_id: 'person-1',
    by_position: [],
    by_sector: [],
    by_country: [],
    by_currency: [],
    meta: {},
    ...overrides
  }
}

function mountPanel(exposures: PortfolioExposuresReadModel) {
  return mount(PortfolioExposuresPanel, {
    props: {
      exposures,
      currency: 'EUR'
    }
  })
}

describe('PortfolioExposuresPanel', () => {
  it('uses the compact small-portfolio state for one holding', () => {
    const wrapper = mountPanel(
      buildExposures({
        by_position: [exposure('Apple', 1, 1000)],
        by_sector: [exposure('Technology', 1, 1000)],
        by_country: [exposure('United States', 1, 1000)],
        by_currency: [exposure('USD', 1, 1000)]
      })
    )

    expect(wrapper.get('[data-testid="portfolio-exposures-panel"]').attributes('data-layout')).toBe('small')
    expect(wrapper.find('[data-testid="exposures-small-state"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="exposures-default-state"]').exists()).toBe(false)
    expect(wrapper.findAll('.exposure-section--balanced')).toHaveLength(4)
    expect(wrapper.findAll('.exposure-bar')).toHaveLength(4)
    expect(wrapper.get('[data-testid="exposure-small-row-position"]').text()).toContain('Apple')
    expect(wrapper.find('button.toggle').exists()).toBe(false)
  })

  it('keeps two to three holdings balanced across exposure dimensions', () => {
    const wrapper = mountPanel(
      buildExposures({
        by_position: [exposure('Nestle', 0.15), exposure('SAP', 0.55), exposure('Apple', 0.3)],
        by_sector: [exposure('Technology', 0.85), exposure('Consumer Staples', 0.15)],
        by_country: [exposure('Germany', 0.55), exposure('United States', 0.3), exposure('Switzerland', 0.15)],
        by_currency: [exposure('EUR', 0.7), exposure('USD', 0.3)]
      })
    )

    expect(wrapper.get('[data-testid="portfolio-exposures-panel"]').attributes('data-layout')).toBe('small')
    expect(wrapper.findAll('[data-testid="exposure-small-row-position"]').map((row) => row.find('.exposure-label').text())).toEqual([
      'SAP',
      'Apple',
      'Nestle'
    ])
    expect(wrapper.get('[data-testid="exposure-card-position"] .section-count').text()).toBe('3')
    expect(wrapper.get('[data-testid="exposure-card-sector"] .section-count').text()).toBe('2')
    expect(wrapper.get('[data-testid="exposure-card-country"] .section-count').text()).toBe('3')
    expect(wrapper.get('[data-testid="exposure-card-currency"] .section-count').text()).toBe('2')
    expect(wrapper.find('.sections-sidebar').exists()).toBe(false)
  })

  it('uses the default state for normal portfolios and keeps expand collapse behavior', async () => {
    const wrapper = mountPanel(
      buildExposures({
        by_position: Array.from({ length: 9 }, (_, index) => exposure(`Holding ${index + 1}`, 0.18 - index * 0.01)),
        by_sector: [exposure('Technology', 0.45), exposure('Healthcare', 0.3), exposure('Industrials', 0.25)],
        by_country: [exposure('United States', 0.7), exposure('Germany', 0.3)],
        by_currency: [exposure('USD', 0.7), exposure('EUR', 0.3)]
      })
    )

    expect(wrapper.get('[data-testid="portfolio-exposures-panel"]').attributes('data-layout')).toBe('default')
    expect(wrapper.find('[data-testid="exposures-default-state"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="exposures-small-state"]').exists()).toBe(false)
    expect(wrapper.findAll('[data-testid="exposure-default-row-position"]')).toHaveLength(8)

    const toggle = wrapper.get('button.toggle')
    expect(toggle.text()).toBe('Mehr anzeigen')

    await toggle.trigger('click')

    expect(wrapper.findAll('[data-testid="exposure-default-row-position"]')).toHaveLength(9)
    expect(wrapper.get('button.toggle').text()).toBe('Weniger anzeigen')

    await wrapper.get('button.toggle').trigger('click')

    expect(wrapper.findAll('[data-testid="exposure-default-row-position"]')).toHaveLength(8)
  })

  it('renders empty exposure sections without falling back to the large default layout', () => {
    const wrapper = mountPanel(buildExposures())

    expect(wrapper.get('[data-testid="portfolio-exposures-panel"]').attributes('data-layout')).toBe('empty')
    expect(wrapper.find('[data-testid="exposures-empty-state"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="exposures-default-state"]').exists()).toBe(false)
    expect(wrapper.get('[data-testid="exposure-empty-position"]').text()).toBe('Keine Daten')
    expect(wrapper.get('[data-testid="exposure-empty-sector"]').text()).toBe('Keine Daten')
    expect(wrapper.get('[data-testid="exposure-empty-country"]').text()).toBe('Keine Daten')
    expect(wrapper.get('[data-testid="exposure-empty-currency"]').text()).toBe('Keine Daten')
  })
})
