<template>
  <article class="panel">
    <header class="panel-header">
      <div class="panel-heading">
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
      <div class="mode-toggle" role="group" aria-label="Performance-Darstellung">
        <button
          v-for="option in modeOptions"
          :key="option.key"
          type="button"
          class="mode-button"
          :class="{ active: chartMode === option.key }"
          :disabled="option.disabled"
          :title="option.title"
          @click="selectMode(option.key)"
        >
          {{ option.label }}
        </button>
      </div>
    </header>

    <div v-if="seriesToggleItems.length > 0" class="series-toolbar" aria-label="Sichtbare Linien">
      <span class="toolbar-label">Linien</span>
      <div class="series-toggle-group" role="group" aria-label="Sichtbare Linien">
        <button
          v-for="item in seriesToggleItems"
          :key="item.key"
          type="button"
          :class="['series-toggle', item.className, { active: visibleSeries[item.key] && !item.disabled }]"
          :aria-pressed="visibleSeries[item.key] && !item.disabled"
          :disabled="item.disabled"
          :title="item.title"
          @click="toggleSeries(item.key)"
        >
          <span class="series-dot" aria-hidden="true"></span>
          <span>{{ item.label }}</span>
        </button>
      </div>
    </div>

    <div class="chart-wrap">
      <SimpleLineChart v-if="hasVisibleChartData" :points="chartBasePoints" :datasets="lineDatasets" />
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
type SeriesToggleKey = 'portfolio' | 'benchmark' | 'relative'
type SeriesToggleItem = { key: SeriesToggleKey; label: string; className: string; disabled: boolean; title: string }
type ChartDataset = { label: string; points: ChartPoint[]; borderColor: string; seriesKey: SeriesToggleKey }

const props = defineProps<{
  performance: PortfolioPerformanceReadModel
  currency?: string
}>()

const currency = computed(() => props.currency ?? 'EUR')
const chartMode = ref<ChartMode>('absolute')
const visibleSeries = ref<Record<SeriesToggleKey, boolean>>({
  portfolio: true,
  benchmark: true,
  relative: true
})

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

const availableLineDatasets = computed<ChartDataset[]>(() => {
  if (chartMode.value === 'relative') {
    return [
      {
        label: 'Out-/Underperformance vs Benchmark (pp)',
        points: relativeLinePoints.value,
        borderColor: '#0f766e',
        seriesKey: 'relative'
      }
    ]
  }

  if (chartMode.value === 'drawdown') {
    const datasets: ChartDataset[] = [
      {
        label: 'Portfolio Drawdown',
        points: portfolioDrawdownLinePoints.value,
        borderColor: '#b91c1c',
        seriesKey: 'portfolio'
      }
    ]
    if (alignedBenchmarkDrawdownLinePoints.value.length > 0) {
      datasets.push({
        label: 'Benchmark Drawdown',
        points: alignedBenchmarkDrawdownLinePoints.value,
        borderColor: '#64748b',
        seriesKey: 'benchmark'
      })
    }
    return datasets
  }

  const suffix = chartMode.value === 'normalized' ? ' (Index 100)' : ''
  const datasets: ChartDataset[] = [
    {
      label: `Portfolio${suffix}`,
      points: activePortfolioLinePoints.value,
      borderColor: '#2563eb',
      seriesKey: 'portfolio'
    }
  ]
  if (activeBenchmarkLinePoints.value.length > 0) {
    datasets.push({
      label: `Benchmark${suffix}`,
      points: activeBenchmarkLinePoints.value,
      borderColor: '#67a4a5',
      seriesKey: 'benchmark'
    })
  }
  return datasets
})

const lineDatasets = computed(() => availableLineDatasets.value.filter((dataset) => visibleSeries.value[dataset.seriesKey]))
const chartBasePoints = computed(() => lineDatasets.value[0]?.points ?? [])
const hasVisibleChartData = computed(() => lineDatasets.value.some((dataset) => dataset.points.length > 0))

const seriesToggleItems = computed<SeriesToggleItem[]>(() => {
  if (chartMode.value === 'relative') {
    return [
      {
        key: 'relative',
        label: 'Out-/Underperformance',
        className: 'relative',
        disabled: relativeLinePoints.value.length === 0,
        title: relativeLinePoints.value.length > 0 ? 'Relative Linie ein- oder ausblenden' : relativeUnavailableReason.value
      }
    ]
  }
  if (chartMode.value === 'drawdown') {
    return [
      {
        key: 'portfolio',
        label: 'Portfolio Drawdown',
        className: 'drawdown',
        disabled: portfolioDrawdownLinePoints.value.length === 0,
        title:
          portfolioDrawdownLinePoints.value.length > 0
            ? 'Portfolio-Drawdown ein- oder ausblenden'
            : 'Portfolio-Drawdown nicht ableitbar'
      },
      {
        key: 'benchmark',
        label: 'Benchmark Drawdown',
        className: 'benchmark',
        disabled: alignedBenchmarkDrawdownLinePoints.value.length === 0,
        title:
          alignedBenchmarkDrawdownLinePoints.value.length > 0
            ? 'Benchmark-Drawdown ein- oder ausblenden'
            : 'Benchmark-Drawdown nicht verfügbar'
      }
    ]
  }

  return [
    {
      key: 'portfolio',
      label: 'Portfolio',
      className: 'portfolio',
      disabled: activePortfolioLinePoints.value.length === 0,
      title: activePortfolioLinePoints.value.length > 0 ? 'Portfolio-Linie ein- oder ausblenden' : 'Portfolio-Serie nicht verfügbar'
    },
    {
      key: 'benchmark',
      label: 'Benchmark',
      className: 'benchmark',
      disabled: activeBenchmarkLinePoints.value.length === 0,
      title: activeBenchmarkLinePoints.value.length > 0 ? 'Benchmark-Linie ein- oder ausblenden' : 'Benchmark-Serie nicht verfügbar'
    }
  ]
})

function toggleSeries(key: SeriesToggleKey) {
  const option = seriesToggleItems.value.find((item) => item.key === key)
  if (option?.disabled) {
    return
  }

  visibleSeries.value[key] = !visibleSeries.value[key]
}

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
  if (availableLineDatasets.value.length > 0 && lineDatasets.value.length === 0) {
    return 'Keine sichtbare Linie ausgewählt.'
  }
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
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
  gap: 1rem;
}

.panel-heading {
  min-width: 0;
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

.mode-toggle {
  display: inline-flex;
  max-width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  overflow-x: auto;
  overflow-y: hidden;
  background: #ffffff;
  scrollbar-width: thin;
}

.mode-button {
  flex: 0 0 auto;
  border: 0;
  border-right: 1px solid #cbd5e1;
  background: #ffffff;
  color: #475569;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 700;
  line-height: 1.2;
  padding: 0.32rem 0.55rem;
  white-space: nowrap;
}

.mode-button:last-child {
  border-right: 0;
}

.mode-button.active {
  background: #e0f2fe;
  color: #0369a1;
}

.mode-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.series-toolbar {
  margin-top: 0.6rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  border-top: 1px solid #e2e8f0;
  padding-top: 0.5rem;
}

.toolbar-label {
  color: #64748b;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  white-space: nowrap;
}

.series-toggle-group {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.35rem;
  min-width: 0;
}

.series-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.32rem;
  min-height: 1.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #ffffff;
  color: #64748b;
  cursor: pointer;
  font-size: 0.76rem;
  font-weight: 700;
  line-height: 1.1;
  padding: 0.22rem 0.5rem;
  white-space: nowrap;
}

.series-toggle.active {
  color: #0f172a;
  border-color: #94a3b8;
  box-shadow: inset 0 0 0 1px #cbd5e1;
}

.series-toggle:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.series-dot {
  width: 0.58rem;
  height: 0.58rem;
  border-radius: 999px;
  background: #94a3b8;
  flex: 0 0 auto;
}

.series-toggle.portfolio .series-dot {
  background: #2563eb;
}

.series-toggle.benchmark .series-dot {
  background: #67a4a5;
}

.series-toggle.relative .series-dot {
  background: #0f766e;
}

.series-toggle.drawdown .series-dot {
  background: #b91c1c;
}

.series-toggle:not(.active) .series-dot {
  opacity: 0.35;
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
    grid-template-columns: minmax(0, 1fr);
  }

  .mode-toggle {
    justify-self: start;
    width: 100%;
  }

  .series-toolbar {
    align-items: flex-start;
    display: grid;
  }

  .series-toggle-group {
    justify-content: flex-start;
  }
}
</style>
