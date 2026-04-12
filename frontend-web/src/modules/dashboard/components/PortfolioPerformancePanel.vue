<template>
  <article class="panel">
    <header class="panel-header">
      <div>
        <h3>Portfolio Performance</h3>
        <p class="meta">
          Benchmark:
          <strong>{{ benchmarkSymbol }}</strong>
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
      <p><strong>Start</strong><span>{{ formatMoney(performance.summary.start_value, currency) }}</span></p>
      <p><strong>Ende</strong><span>{{ formatMoney(performance.summary.end_value, currency) }}</span></p>
      <p>
        <strong>Veränderung</strong>
        <span :class="changeClass">{{ formatSignedMoney(performance.summary.absolute_change, currency) }}</span>
      </p>
      <p><strong>Rendite</strong><span>{{ formatPercentValue(performance.summary.return_pct) }}</span></p>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SimpleLineChart from '@/shared/ui/SimpleLineChart.vue'
import type { PortfolioPerformanceReadModel } from '@/shared/model/types'
import { formatMoney, formatPercentValue, formatSignedMoney } from '@/modules/dashboard/model/portfolioFormatting'

const props = defineProps<{
  performance: PortfolioPerformanceReadModel
  currency?: string
}>()

const currency = computed(() => props.currency ?? 'EUR')

const benchmarkSymbol = computed(() => props.performance.benchmark_symbol ?? 'n/a')

const portfolioLinePoints = computed(() => {
  const portfolioSeries = props.performance.series.find((series) => series.key === 'portfolio_value') ?? props.performance.series[0]
  if (!portfolioSeries?.points) {
    return []
  }
  return portfolioSeries.points.map((point) => ({ date: point.x, value: point.y }))
})

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

.meta {
  margin: 0;
  color: #64748b;
  font-size: 0.85rem;
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
