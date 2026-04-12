// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import PortfolioPerformancePanel from '@/modules/dashboard/components/PortfolioPerformancePanel.vue'
import type { PortfolioPerformanceReadModel } from '@/shared/model/types'

const SimpleLineChartStub = defineComponent({
  name: 'SimpleLineChart',
  props: {
    points: { type: Array, required: true },
    datasets: { type: Array, required: false }
  },
  template: '<div data-testid="chart"></div>'
})

function buildPerformance(overrides: Partial<PortfolioPerformanceReadModel> = {}): PortfolioPerformanceReadModel {
  return {
    person_id: 'person-1',
    range: '3m',
    range_label: '3 Monate',
    benchmark_symbol: 'SPY',
    series: [
      {
        key: 'portfolio_value',
        label: 'Portfolio',
        points: [
          { x: '2026-01-01', y: 100 },
          { x: '2026-01-02', y: 120 },
          { x: '2026-01-03', y: 90 }
        ]
      },
      {
        key: 'benchmark_price',
        label: 'Benchmark SPY',
        points: [
          { x: '2026-01-01', y: 50 },
          { x: '2026-01-02', y: 75 },
          { x: '2026-01-03', y: 60 }
        ]
      }
    ],
    summary: { start_value: 100, end_value: 90, absolute_change: -10, return_pct: -10 },
    meta: {},
    ...overrides
  }
}

function mountPanel(performance: PortfolioPerformanceReadModel) {
  return mount(PortfolioPerformancePanel, {
    props: { performance, currency: 'EUR' },
    global: {
      stubs: {
        SimpleLineChart: SimpleLineChartStub
      }
    }
  })
}

describe('PortfolioPerformancePanel', () => {
  it('can switch from absolute values to normalized index values', async () => {
    const wrapper = mountPanel(buildPerformance())

    await wrapper.findAll('button').find((button) => button.text() === 'Normalisiert')?.trigger('click')

    const datasets = wrapper.getComponent(SimpleLineChartStub).props('datasets') as Array<{
      label: string
      points: Array<{ date: string; value: number }>
    }>
    expect(datasets).toHaveLength(2)
    expect(datasets[0].label).toBe('Portfolio (Index 100)')
    expect(datasets[0].points.map((point) => point.value)).toEqual([100, 120, 90])
    expect(datasets[1].label).toBe('Benchmark (Index 100)')
    expect(datasets[1].points.map((point) => point.value)).toEqual([100, 150, 120])
    expect(wrapper.text()).toContain('Max Drawdown')
    expect(wrapper.text()).toContain('-25,00 %')
  })

  it('keeps rendering defensively when the benchmark series is missing', () => {
    const wrapper = mountPanel(
      buildPerformance({
        series: [
          {
            key: 'portfolio_value',
            label: 'Portfolio',
            points: [
              { x: '2026-01-01', y: 100 },
              { x: '2026-01-02', y: 110 }
            ]
          }
        ]
      })
    )

    const datasets = wrapper.getComponent(SimpleLineChartStub).props('datasets') as Array<{ label: string }>
    expect(datasets).toHaveLength(1)
    expect(datasets[0].label).toBe('Portfolio')
    expect(wrapper.text()).toContain('Benchmark-Serie nicht verfügbar.')
  })
})
