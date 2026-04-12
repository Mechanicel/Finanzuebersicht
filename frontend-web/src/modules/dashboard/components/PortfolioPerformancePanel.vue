<template>
  <article class="panel">
    <header class="panel-header">
      <div>
        <div class="title-row">
          <h3>Portfolio Performance</h3>
          <span class="scope-badge">Zeitraum</span>
        </div>
        <p class="meta">
          <span>Stand: <strong>{{ asOfLabel }}</strong></span>
          <span>Zeitraum: <strong>{{ rangeLabel }}</strong></span>
          <span>Benchmark: <strong>{{ benchmarkSymbol }}</strong></span>
          <span v-if="returnBasisLabel">Methodik: <strong>{{ returnBasisLabel }}</strong></span>
        </p>
      </div>
      <div class="panel-tools">
        <div class="view-toggle" role="group" aria-label="Performance-Darstellung">
          <button
            v-for="option in modeOptions"
            :key="option.key"
            type="button"
            :class="{ active: chartMode === option.key }"
            :disabled="option.disabled"
            :title="option.title"
            @click="selectMode(option.key)"
          >
            {{ option.label }}
          </button>
        </div>
        <div v-if="legendItems.length > 0" class="legend">
          <span v-for="item in legendItems" :key="item.label" :class="['legend-item', item.className]">
            {{ item.label }}
          </span>
        </div>
      </div>
    </header>

    <div class="chart-wrap">
      <SimpleLineChart v-if="activePortfolioLinePoints.length > 0" :points="activePortfolioLinePoints" :datasets="lineDatasets" />
      <p v-else class="hint">{{ emptyChartHint }}</p>
    </div>
    <div v-if="fallbackHints.length > 0" class="fallbacks">
      <p v-for="hint in fallbackHints" :key="hint" class="hint hint--compact">{{ hint }}</p>
    </div>

    <div class="stats">
      <p v-for="item in statsItems" :key="item.label">
        <strong>{{ item.label }}</strong>
        <span :class="item.tone">{{ item.value }}</span>
      </p>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import SimpleLineChart from '@/shared/ui/SimpleLineChart.vue'
import type { PortfolioPerformanceReadModel, PortfolioPerformanceSeries } from '@/shared/model/types'
import {
  formatDate,
  formatMoney,
  formatNullableText,
  formatNumber,
  formatPercentValue,
  formatRangeLabel,
  formatSignedMoney,
  formatSignedPercentPoints,
  getStringMeta,
  mapPortfolioMethodology
} from '@/modules/dashboard/model/portfolioFormatting'

type ChartMode = 'absolute' | 'normalized' | 'relative' | 'drawdown'
type ChartPoint = { date: string; value: number }
type AlignedPoint = { date: string; portfolioValue: number; benchmarkValue: number }
type Tone = 'positive' | 'negative' | 'neutral'
type ModeOption = { key: ChartMode; label: string; disabled: boolean; title: string }
type StatItem = { label: string; value: string; tone: Tone }
type LegendItem = { label: string; className: string }

const props = defineProps<{
  performance: PortfolioPerformanceReadModel
  currency?: string
}>()

const currency = computed(() => props.currency ?? 'EUR')
const chartMode = ref<ChartMode>('absolute')

const benchmarkSymbol = computed(() => formatNullableText(props.performance.benchmark_symbol))
const rangeLabel = computed(() => formatRangeLabel(props.performance.range, props.performance.range_label))
const returnBasisLabel = computed(() =>
  props.performance.summary.return_basis ? mapPortfolioMethodology(props.performance.summary.return_basis) : ''
)

function toChartPoints(series: PortfolioPerformanceSeries | undefined): ChartPoint[] {
  if (!series?.points) {
    return []
  }

  return series.points
    .filter((point) => point.x.trim().length > 0 && Number.isFinite(point.y))
    .map((point) => ({ date: point.x.trim(), value: point.y }))
}

const portfolioLinePoints = computed(() => {
  const portfolioSeries = props.performance.series.find((series) => series.key === 'portfolio_value') ?? props.performance.series[0]
  return toChartPoints(portfolioSeries)
})

const latestPortfolioDate = computed(() => {
  const points = portfolioLinePoints.value
  return points.length > 0 ? points[points.length - 1].date : null
})
const asOfLabel = computed(() => formatDate(getStringMeta(props.performance.meta, 'as_of', 'generated_at', 'updated_at') ?? latestPortfolioDate.value))

const benchmarkLinePoints = computed(() => {
  const benchmarkSeries =
    props.performance.series.find((series) => series.key === 'benchmark_price' || series.key === 'benchmark_value') ??
    props.performance.series.find((series) => series.key.toLowerCase().includes('benchmark'))
  return toChartPoints(benchmarkSeries)
})

function normalizeToIndex(points: ChartPoint[]): ChartPoint[] {
  const baseIndex = points.findIndex((point) => Number.isFinite(point.value) && point.value > 0)
  if (baseIndex < 0) {
    return []
  }

  const startValue = points[baseIndex].value
  return points.slice(baseIndex).map((point) => ({
    date: point.date,
    value: (point.value / startValue) * 100
  }))
}

function alignPortfolioAndBenchmark(portfolioPoints: ChartPoint[], benchmarkPoints: ChartPoint[]): AlignedPoint[] {
  const benchmarkByDate = new Map(
    benchmarkPoints
      .filter((point) => Number.isFinite(point.value) && point.value > 0)
      .map((point) => [point.date, point.value])
  )

  return portfolioPoints
    .filter((point) => Number.isFinite(point.value) && point.value > 0 && benchmarkByDate.has(point.date))
    .map((point) => ({
      date: point.date,
      portfolioValue: point.value,
      benchmarkValue: benchmarkByDate.get(point.date) as number
    }))
}

function calculateRelativePerformance(alignedPoints: AlignedPoint[]): ChartPoint[] {
  if (alignedPoints.length < 2) {
    return []
  }

  const base = alignedPoints[0]
  if (base.portfolioValue <= 0 || base.benchmarkValue <= 0) {
    return []
  }

  return alignedPoints.map((point) => ({
    date: point.date,
    value: ((point.portfolioValue / base.portfolioValue - point.benchmarkValue / base.benchmarkValue) * 100)
  }))
}

function calculateDrawdown(points: ChartPoint[]): ChartPoint[] {
  const drawdownPoints: ChartPoint[] = []
  let peak: number | null = null

  points.forEach((point) => {
    if (!Number.isFinite(point.value) || point.value <= 0) {
      return
    }

    if (peak == null || point.value > peak) {
      peak = point.value
    }

    drawdownPoints.push({
      date: point.date,
      value: ((point.value - peak) / peak) * 100
    })
  })

  return drawdownPoints
}

function alignByPortfolioDates(portfolioPoints: ChartPoint[], secondaryPoints: ChartPoint[]): ChartPoint[] {
  const secondaryByDate = new Map(secondaryPoints.map((point) => [point.date, point.value]))
  const aligned = portfolioPoints
    .filter((point) => secondaryByDate.has(point.date))
    .map((point) => ({ date: point.date, value: secondaryByDate.get(point.date) as number }))

  return aligned.length >= 2 ? aligned : []
}

function latestValue(points: ChartPoint[]): number | null {
  return points.length > 0 ? points[points.length - 1].value : null
}

function minValue(points: ChartPoint[]): number | null {
  if (points.length === 0) {
    return null
  }
  return Math.min(...points.map((point) => point.value))
}

function maxValue(points: ChartPoint[]): number | null {
  if (points.length === 0) {
    return null
  }
  return Math.max(...points.map((point) => point.value))
}

function minPoint(points: ChartPoint[]): ChartPoint | null {
  return points.reduce<ChartPoint | null>((lowest, point) => {
    if (lowest == null || point.value < lowest.value) {
      return point
    }
    return lowest
  }, null)
}

function numberTone(value: number | null | undefined): Tone {
  if (value == null || !Number.isFinite(value) || value === 0) return 'neutral'
  return value > 0 ? 'positive' : 'negative'
}

const normalizedPortfolioLinePoints = computed(() => normalizeToIndex(portfolioLinePoints.value))
const normalizedBenchmarkLinePoints = computed(() => normalizeToIndex(benchmarkLinePoints.value))
const alignedPerformancePoints = computed(() => alignPortfolioAndBenchmark(portfolioLinePoints.value, benchmarkLinePoints.value))
const relativeLinePoints = computed(() => calculateRelativePerformance(alignedPerformancePoints.value))
const portfolioDrawdownLinePoints = computed(() => calculateDrawdown(portfolioLinePoints.value))
const benchmarkDrawdownLinePoints = computed(() => calculateDrawdown(benchmarkLinePoints.value))
const alignedBenchmarkDrawdownLinePoints = computed(() =>
  alignByPortfolioDates(portfolioDrawdownLinePoints.value, benchmarkDrawdownLinePoints.value)
)

const canUseNormalized = computed(() => normalizedPortfolioLinePoints.value.length > 0)
const canUseRelative = computed(() => relativeLinePoints.value.length > 0)
const canUseDrawdown = computed(() => portfolioDrawdownLinePoints.value.length > 0)

const activePortfolioLinePoints = computed(() => {
  if (chartMode.value === 'normalized') return normalizedPortfolioLinePoints.value
  if (chartMode.value === 'relative') return relativeLinePoints.value
  if (chartMode.value === 'drawdown') return portfolioDrawdownLinePoints.value
  return portfolioLinePoints.value
})

const activeBenchmarkLinePoints = computed(() => {
  if (chartMode.value === 'normalized') return normalizedBenchmarkLinePoints.value
  if (chartMode.value === 'drawdown') return alignedBenchmarkDrawdownLinePoints.value
  if (chartMode.value === 'relative') return []
  return benchmarkLinePoints.value
})

const isBenchmarkSeriesMissing = computed(() => Boolean(props.performance.benchmark_symbol) && benchmarkLinePoints.value.length === 0)
const isBenchmarkSeriesUnalignable = computed(() => benchmarkLinePoints.value.length > 0 && alignedPerformancePoints.value.length < 2)

const relativeUnavailableReason = computed(() => {
  if (benchmarkLinePoints.value.length === 0) {
    return 'Benchmark-Serie nicht verfügbar.'
  }
  if (alignedPerformancePoints.value.length < 2) {
    return 'Benchmark-Serie nicht ausreichend mit Portfolio-Daten alignbar.'
  }
  return ''
})

function isChartModeAvailable(mode: ChartMode): boolean {
  if (mode === 'normalized') return canUseNormalized.value
  if (mode === 'relative') return canUseRelative.value
  if (mode === 'drawdown') return canUseDrawdown.value
  return true
}

function selectMode(mode: ChartMode) {
  if (isChartModeAvailable(mode)) {
    chartMode.value = mode
  }
}

const modeOptions = computed<ModeOption[]>(() => [
  { key: 'absolute', label: 'Absolut', disabled: false, title: 'Absolute Portfolio- und Benchmark-Werte' },
  {
    key: 'normalized',
    label: 'Normalisiert',
    disabled: !canUseNormalized.value,
    title: canUseNormalized.value ? 'Indexierte Entwicklung ab Startwert 100' : 'Portfolio-Serie nicht normalisierbar'
  },
  {
    key: 'relative',
    label: 'Relativ vs Benchmark',
    disabled: !canUseRelative.value,
    title: canUseRelative.value ? 'Out-/Underperformance in Prozentpunkten' : relativeUnavailableReason.value
  },
  {
    key: 'drawdown',
    label: 'Drawdown',
    disabled: !canUseDrawdown.value,
    title: canUseDrawdown.value ? 'Rückgang vom bisherigen Höchststand' : 'Drawdown aus Portfolio-Serie nicht ableitbar'
  }
])

const lineDatasets = computed(() => {
  if (chartMode.value === 'relative') {
    return [
      {
        label: 'Out-/Underperformance vs Benchmark (pp)',
        points: relativeLinePoints.value,
        borderColor: '#0f766e'
      }
    ]
  }

  if (chartMode.value === 'drawdown') {
    const datasets = [{ label: 'Portfolio Drawdown', points: portfolioDrawdownLinePoints.value, borderColor: '#b91c1c' }]
    if (alignedBenchmarkDrawdownLinePoints.value.length > 0) {
      datasets.push({ label: 'Benchmark Drawdown', points: alignedBenchmarkDrawdownLinePoints.value, borderColor: '#64748b' })
    }
    return datasets
  }

  const suffix = chartMode.value === 'normalized' ? ' (Index 100)' : ''
  const datasets = [{ label: `Portfolio${suffix}`, points: activePortfolioLinePoints.value, borderColor: '#2563eb' }]
  if (activeBenchmarkLinePoints.value.length > 0) {
    datasets.push({ label: `Benchmark${suffix}`, points: activeBenchmarkLinePoints.value, borderColor: '#67a4a5' })
  }
  return datasets
})

const legendItems = computed<LegendItem[]>(() => {
  if (chartMode.value === 'relative') {
    return [{ label: 'Out-/Underperformance', className: 'relative' }]
  }
  if (chartMode.value === 'drawdown') {
    const items = [{ label: 'Portfolio Drawdown', className: 'drawdown' }]
    if (alignedBenchmarkDrawdownLinePoints.value.length > 0) {
      items.push({ label: 'Benchmark Drawdown', className: 'benchmark' })
    }
    return items
  }

  const items = [{ label: 'Portfolio', className: 'portfolio' }]
  if (activeBenchmarkLinePoints.value.length > 0) {
    items.push({ label: 'Benchmark', className: 'benchmark' })
  }
  return items
})

const maxDrawdownPct = computed(() => minValue(portfolioDrawdownLinePoints.value))
const latestRelativePerformancePct = computed(() => latestValue(relativeLinePoints.value))
const bestRelativePerformancePct = computed(() => maxValue(relativeLinePoints.value))
const worstRelativePerformancePct = computed(() => minValue(relativeLinePoints.value))
const latestPortfolioIndex = computed(() => latestValue(normalizedPortfolioLinePoints.value))
const latestBenchmarkIndex = computed(() => latestValue(normalizedBenchmarkLinePoints.value))
const latestPortfolioDrawdownPct = computed(() => latestValue(portfolioDrawdownLinePoints.value))
const latestBenchmarkDrawdownPct = computed(() => latestValue(alignedBenchmarkDrawdownLinePoints.value))
const benchmarkMaxDrawdownPct = computed(() => minValue(alignedBenchmarkDrawdownLinePoints.value))
const drawdownTroughDate = computed(() => formatDate(minPoint(portfolioDrawdownLinePoints.value)?.date))

const statsItems = computed<StatItem[]>(() => {
  if (chartMode.value === 'normalized') {
    return [
      { label: 'Startindex', value: formatNumber(100), tone: 'neutral' },
      { label: 'Portfolio-Index', value: formatNumber(latestPortfolioIndex.value), tone: numberTone((latestPortfolioIndex.value ?? 100) - 100) },
      { label: 'Benchmark-Index', value: formatNumber(latestBenchmarkIndex.value), tone: numberTone((latestBenchmarkIndex.value ?? 100) - 100) },
      { label: 'Abstand vs Benchmark', value: formatSignedPercentPoints(latestRelativePerformancePct.value), tone: numberTone(latestRelativePerformancePct.value) },
      { label: 'Max Drawdown', value: formatPercentValue(maxDrawdownPct.value), tone: numberTone(maxDrawdownPct.value) }
    ]
  }

  if (chartMode.value === 'relative') {
    return [
      {
        label: 'Aktive Renditediff.',
        value: formatSignedPercentPoints(latestRelativePerformancePct.value),
        tone: numberTone(latestRelativePerformancePct.value)
      },
      {
        label: 'Bester Abstand',
        value: formatSignedPercentPoints(bestRelativePerformancePct.value),
        tone: numberTone(bestRelativePerformancePct.value)
      },
      {
        label: 'Schlechtester Abstand',
        value: formatSignedPercentPoints(worstRelativePerformancePct.value),
        tone: numberTone(worstRelativePerformancePct.value)
      },
      { label: 'Aligned Punkte', value: `${alignedPerformancePoints.value.length}`, tone: 'neutral' },
      { label: 'Benchmark', value: benchmarkSymbol.value, tone: 'neutral' }
    ]
  }

  if (chartMode.value === 'drawdown') {
    return [
      { label: 'Aktueller Drawdown', value: formatPercentValue(latestPortfolioDrawdownPct.value), tone: numberTone(latestPortfolioDrawdownPct.value) },
      { label: 'Max Drawdown', value: formatPercentValue(maxDrawdownPct.value), tone: numberTone(maxDrawdownPct.value) },
      { label: 'Benchmark aktuell', value: formatPercentValue(latestBenchmarkDrawdownPct.value), tone: numberTone(latestBenchmarkDrawdownPct.value) },
      { label: 'Benchmark Max DD', value: formatPercentValue(benchmarkMaxDrawdownPct.value), tone: numberTone(benchmarkMaxDrawdownPct.value) },
      { label: 'Tiefpunkt', value: drawdownTroughDate.value, tone: 'neutral' }
    ]
  }

  return [
    { label: 'Startwert', value: formatMoney(props.performance.summary.start_value, currency.value), tone: 'neutral' },
    { label: 'Endwert', value: formatMoney(props.performance.summary.end_value, currency.value), tone: 'neutral' },
    {
      label: 'Wertveränderung',
      value: formatSignedMoney(props.performance.summary.absolute_change, currency.value),
      tone: numberTone(props.performance.summary.absolute_change)
    },
    { label: 'Zeitraumrendite', value: formatPercentValue(props.performance.summary.return_pct), tone: numberTone(props.performance.summary.return_pct) },
    { label: 'Max Drawdown', value: formatPercentValue(maxDrawdownPct.value), tone: numberTone(maxDrawdownPct.value) }
  ]
})

const fallbackHints = computed(() => {
  const hints: string[] = []
  if (isBenchmarkSeriesMissing.value) {
    hints.push('Benchmark-Serie nicht verfügbar.')
  }
  if (isBenchmarkSeriesUnalignable.value) {
    hints.push('Benchmark-Serie nicht ausreichend mit Portfolio-Daten alignbar; relative Ansicht deaktiviert.')
  }
  if (
    chartMode.value === 'drawdown' &&
    benchmarkLinePoints.value.length > 0 &&
    alignedBenchmarkDrawdownLinePoints.value.length === 0
  ) {
    hints.push('Benchmark-Drawdown nicht robust mit Portfolio-Daten alignbar.')
  }
  return hints
})

const emptyChartHint = computed(() => {
  if (chartMode.value === 'relative') {
    return relativeUnavailableReason.value || 'Relative Performance nicht ableitbar.'
  }
  if (chartMode.value === 'drawdown') {
    return 'Drawdown aus Portfolio-Serie nicht ableitbar.'
  }
  return 'Keine Portfolio-Serie verfügbar.'
})

watch(
  [canUseNormalized, canUseRelative, canUseDrawdown],
  () => {
    if (!isChartModeAvailable(chartMode.value)) {
      chartMode.value = 'absolute'
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.panel {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem;
  background: #fff;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.panel-tools {
  display: grid;
  justify-items: end;
  gap: 0.35rem;
}

.panel-header h3 {
  margin: 0;
}

.title-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
}

.scope-badge {
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  padding: 0.08rem 0.4rem;
  color: #475569;
  font-size: 0.72rem;
  font-weight: 700;
}

.meta {
  margin: 0.2rem 0 0;
  color: #64748b;
  font-size: 0.85rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.chart-wrap {
  height: 132px;
  margin-top: 0.55rem;
}

.hint {
  color: #64748b;
  margin-top: 0.5rem;
}

.fallbacks {
  display: grid;
  gap: 0.12rem;
}

.hint--compact {
  margin: 0.2rem 0 0;
  font-size: 0.78rem;
}

.stats {
  margin-top: 0.55rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 0.35rem;
}

.stats p {
  margin: 0;
  font-size: 0.82rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.35rem 0.45rem;
  display: grid;
  gap: 0.12rem;
}

.stats strong {
  color: #64748b;
  font-size: 0.74rem;
}

.stats span {
  color: #0f172a;
  font-weight: 600;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  align-items: center;
  justify-content: flex-end;
}

.view-toggle {
  display: inline-flex;
  flex-wrap: wrap;
  max-width: min(100%, 31rem);
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  overflow: hidden;
  background: #ffffff;
}

.view-toggle button {
  border: 0;
  border-right: 1px solid #cbd5e1;
  background: #ffffff;
  color: #475569;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.22rem 0.4rem;
}

.view-toggle button:last-child {
  border-right: 0;
}

.view-toggle button.active {
  background: #e0f2fe;
  color: #0369a1;
}

.view-toggle button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.legend-item {
  border-radius: 999px;
  padding: 0.15rem 0.5rem;
  font-size: 0.75rem;
  border: 1px solid #cbd5e1;
}

.legend-item.portfolio {
  background: #dbeafe;
  color: #1d4ed8;
}

.legend-item.benchmark {
  background: #f1f5f9;
  color: #475569;
}

.legend-item.relative {
  background: #ccfbf1;
  color: #0f766e;
}

.legend-item.drawdown {
  background: #fee2e2;
  color: #991b1b;
}

.positive {
  color: #166534;
}

.negative {
  color: #b91c1c;
}

.neutral {
  color: #334155;
}

@media (max-width: 900px) {
  .panel-header {
    display: grid;
  }

  .panel-tools {
    justify-items: start;
  }

  .legend {
    justify-content: flex-start;
  }
}
</style>
