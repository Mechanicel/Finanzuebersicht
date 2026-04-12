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
      <div class="legend">
        <span class="legend-item portfolio">Portfolio</span>
        <span class="legend-item benchmark">Benchmark</span>
      </div>
    </header>

    <div class="chart-wrap">
      <SimpleLineChart v-if="portfolioLinePoints.length > 0" :points="portfolioLinePoints" :datasets="lineDatasets" />
      <p v-else class="hint">Keine Portfolio-Serie verfügbar.</p>
    </div>

    <div class="stats">
      <p><strong>Startwert</strong><span>{{ formatMoney(performance.summary.start_value, currency) }}</span></p>
      <p><strong>Endwert</strong><span>{{ formatMoney(performance.summary.end_value, currency) }}</span></p>
      <p>
        <strong>Wertveränderung</strong>
        <span :class="changeClass">{{ formatSignedMoney(performance.summary.absolute_change, currency) }}</span>
      </p>
      <p><strong>Zeitraumrendite</strong><span>{{ formatPercentValue(performance.summary.return_pct) }}</span></p>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SimpleLineChart from '@/shared/ui/SimpleLineChart.vue'
import type { PortfolioPerformanceReadModel } from '@/shared/model/types'
import {
  formatDate,
  formatMoney,
  formatNullableText,
  formatPercentValue,
  formatRangeLabel,
  formatSignedMoney,
  getStringMeta,
  mapPortfolioMethodology
} from '@/modules/dashboard/model/portfolioFormatting'

const props = defineProps<{
  performance: PortfolioPerformanceReadModel
  currency?: string
}>()

const currency = computed(() => props.currency ?? 'EUR')

const benchmarkSymbol = computed(() => formatNullableText(props.performance.benchmark_symbol))
const rangeLabel = computed(() => formatRangeLabel(props.performance.range, props.performance.range_label))
const returnBasisLabel = computed(() =>
  props.performance.summary.return_basis ? mapPortfolioMethodology(props.performance.summary.return_basis) : ''
)

const portfolioLinePoints = computed(() => {
  const portfolioSeries = props.performance.series.find((series) => series.key === 'portfolio_value') ?? props.performance.series[0]
  if (!portfolioSeries?.points) {
    return []
  }
  return portfolioSeries.points.map((point) => ({ date: point.x, value: point.y }))
})

const latestPortfolioDate = computed(() => {
  const points = portfolioLinePoints.value
  return points.length > 0 ? points[points.length - 1].date : null
})
const asOfLabel = computed(() => formatDate(getStringMeta(props.performance.meta, 'as_of', 'generated_at', 'updated_at') ?? latestPortfolioDate.value))

const benchmarkLinePoints = computed(() => {
  const benchmarkSeries = props.performance.series.find((series) => series.key === 'benchmark_price')
  if (!benchmarkSeries?.points) {
    return []
  }
  return benchmarkSeries.points.map((point) => ({ date: point.x, value: point.y }))
})

const lineDatasets = computed(() => {
  const datasets = [{ label: 'Portfolio', points: portfolioLinePoints.value, borderColor: '#2563eb' }]
  if (benchmarkLinePoints.value.length > 0) {
    datasets.push({ label: 'Benchmark', points: benchmarkLinePoints.value, borderColor: '#67a4a5' })
  }
  return datasets
})

const changeClass = computed(() => {
  const change = props.performance.summary.absolute_change
  if (change == null) return 'neutral'
  if (change > 0) return 'positive'
  if (change < 0) return 'negative'
  return 'neutral'
})
</script>

<style scoped>
.panel {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.75rem;
  background: #fff;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
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

.stats {
  margin-top: 0.55rem;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
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
  gap: 0.5rem;
  align-items: center;
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
  .stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
