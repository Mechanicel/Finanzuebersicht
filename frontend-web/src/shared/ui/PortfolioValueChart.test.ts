// @vitest-environment jsdom
import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import PortfolioValueChart from '@/shared/ui/PortfolioValueChart.vue'


vi.mock('vue-chartjs', () => ({
  Line: {
    name: 'Line',
    template: '<div data-testid="line-chart" />'
  }
}))


type ChartProps = { points: { date: string; value: number }[]; range: '1m' | '3m' | '6m' | 'ytd' | '1y' | 'max'; loading?: boolean; error?: string }

function createWrapper(props: ChartProps) {
  return mount(PortfolioValueChart, {
    props,
  })
}

describe('PortfolioValueChart', () => {
  it('emits range-change when user selects another range', async () => {
    const wrapper = createWrapper({
        points: [{ date: '2026-01-01', value: 1000 }],
        range: '1m'
    })

    await wrapper.findAll('button').find((node) => node.text() === '3M')?.trigger('click')

    expect(wrapper.emitted('range-change')).toEqual([['3m']])
  })

  it('shows empty state when no points exist', () => {
    const wrapper = createWrapper({
        points: [],
        range: 'max'
    })

    expect(wrapper.text()).toContain('Keine Verlaufspunkte vorhanden.')
  })

  it('renders chart area when points exist', () => {
    const wrapper = createWrapper({
        points: [
          { date: '2026-01-01', value: 1000 },
          { date: '2026-01-02', value: 1010 }
        ],
        range: '1m'
    })

    expect(wrapper.find('.portfolio-value-chart__canvas-wrap').exists()).toBe(true)
    expect(wrapper.text()).not.toContain('Keine Verlaufspunkte vorhanden.')
  })
})
