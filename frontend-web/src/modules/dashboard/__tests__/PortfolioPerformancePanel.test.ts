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

type Dataset = {
  label: string
  points: Array<{ date: string; value: number }>
}

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

function chartDatasets(wrapper: ReturnType<typeof mountPanel>): Dataset[] {
  return wrapper.getComponent(SimpleLineChartStub).props('datasets') as Dataset[]
}

function modeButton(wrapper: ReturnType<typeof mountPanel>, text: string) {
  const button = wrapper.findAll('button').find((candidate) => candidate.text() === text)
  if (!button) {
    throw new Error(`Mode button "${text}" not found`)
  }
  return button
}

function lineToggle(wrapper: ReturnType<typeof mountPanel>, text: string) {
  const button = wrapper.findAll('.series-toggle').find((candidate) => candidate.text() === text)
  if (!button) {
    throw new Error(`Line toggle "${text}" not found`)
  }
  return button
}

function roundedValues(dataset: Dataset): number[] {
  return dataset.points.map((point) => Number(point.value.toFixed(2)))
}

describe('PortfolioPerformancePanel', () => {
  it('renders absolute portfolio and benchmark values by default', () => {
    const wrapper = mountPanel(buildPerformance())

    const datasets = chartDatasets(wrapper)
    expect(datasets).toHaveLength(2)
    expect(datasets[0].label).toBe('Portfolio')
    expect(datasets[0].points.map((point) => point.value)).toEqual([100, 120, 90])
    expect(datasets[1].label).toBe('Benchmark')
    expect(datasets[1].points.map((point) => point.value)).toEqual([50, 75, 60])
    expect(wrapper.find('button.active').text()).toBe('Absolut')
    expect(wrapper.text()).toContain('Startwert')
    expect(wrapper.text()).toContain('Zeitraumrendite')
  })

  it('can switch from absolute values to normalized index values', async () => {
    const wrapper = mountPanel(buildPerformance())

    await modeButton(wrapper, 'Normalisiert').trigger('click')

    const datasets = chartDatasets(wrapper)
    expect(datasets).toHaveLength(2)
    expect(datasets[0].label).toBe('Portfolio (Index 100)')
    expect(datasets[0].points.map((point) => point.value)).toEqual([100, 120, 90])
    expect(datasets[1].label).toBe('Benchmark (Index 100)')
    expect(datasets[1].points.map((point) => point.value)).toEqual([100, 150, 120])
    expect(wrapper.text()).toContain('Portfolio-Index')
    expect(wrapper.text()).toContain('Abstand vs Benchmark')
  })

  it('shows relative out- and underperformance with an aligned benchmark', async () => {
    const wrapper = mountPanel(buildPerformance())

    await modeButton(wrapper, 'Relativ vs Benchmark').trigger('click')

    const datasets = chartDatasets(wrapper)
    expect(datasets).toHaveLength(1)
    expect(datasets[0].label).toBe('Out-/Underperformance vs Benchmark (pp)')
    expect(roundedValues(datasets[0])).toEqual([0, -30, -30])
    expect(wrapper.text()).toContain('Aktive Renditediff.')
    expect(wrapper.text()).toContain('-30,00 pp')
    expect(wrapper.text()).toContain('Aligned Punkte')
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

    const datasets = chartDatasets(wrapper)
    expect(datasets).toHaveLength(1)
    expect(datasets[0].label).toBe('Portfolio')
    expect(modeButton(wrapper, 'Relativ vs Benchmark').attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('Benchmark-Serie nicht verfügbar.')
  })

  it('toggles portfolio and benchmark lines without changing the active mode', async () => {
    const wrapper = mountPanel(buildPerformance())

    await lineToggle(wrapper, 'Benchmark').trigger('click')

    let datasets = chartDatasets(wrapper)
    expect(datasets).toHaveLength(1)
    expect(datasets[0].label).toBe('Portfolio')
    expect(wrapper.find('.mode-button.active').text()).toBe('Absolut')

    await lineToggle(wrapper, 'Portfolio').trigger('click')

    expect(wrapper.find('[data-testid="chart"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Keine sichtbare Linie ausgewählt.')

    await lineToggle(wrapper, 'Benchmark').trigger('click')

    datasets = chartDatasets(wrapper)
    expect(datasets).toHaveLength(1)
    expect(datasets[0].label).toBe('Benchmark')
    expect(datasets[0].points.map((point) => point.value)).toEqual([50, 75, 60])
  })

  it('calculates portfolio and benchmark drawdown curves from existing series', async () => {
    const wrapper = mountPanel(buildPerformance())

    await modeButton(wrapper, 'Drawdown').trigger('click')

    const datasets = chartDatasets(wrapper)
    expect(datasets).toHaveLength(2)
    expect(datasets[0].label).toBe('Portfolio Drawdown')
    expect(roundedValues(datasets[0])).toEqual([0, 0, -25])
    expect(datasets[1].label).toBe('Benchmark Drawdown')
    expect(roundedValues(datasets[1])).toEqual([0, 0, -20])
    expect(wrapper.text()).toContain('Aktueller Drawdown')
    expect(wrapper.text()).toContain('Max Drawdown')
    expect(wrapper.text()).toContain('-25,00 %')
    expect(wrapper.text()).toContain('Benchmark Max DD')
    expect(wrapper.text()).toContain('-20,00 %')
  })
})
