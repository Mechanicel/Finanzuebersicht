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
      <SimpleLineChart v-if="portfolioLinePoints.length > 0" :points="portfolioLinePoints" />
      <p v-else class="hint">Keine Portfolio-Serie verfügbar.</p>
    </div>

    <div class="chart-wrap benchmark-wrap">
      <SimpleLineChart v-if="benchmarkLinePoints.length > 0" :points="benchmarkLinePoints" />
      <p v-else class="hint">Keine Benchmark-Serie verfügbar.</p>
    </div>

    <div class="stats">
      <p><strong>Start:</strong> {{ formatMoney(performance.summary.start_value, currency) }}</p>
      <p><strong>Ende:</strong> {{ formatMoney(performance.summary.end_value, currency) }}</p>
      <p><strong>Veränderung:</strong> <span :class="changeClass">{{ formatSignedMoney(performance.summary.absolute_change, currency) }}</span></p>
      <p><strong>Rendite:</strong> {{ formatPercentPoints(performance.summary.return_pct) }}</p>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SimpleLineChart from '@/shared/ui/SimpleLineChart.vue'
import type { PortfolioPerformanceReadModel } from '@/shared/model/types'
import { formatMoney, formatPercentPoints, formatSignedMoney } from '@/modules/dashboard/model/portfolioFormatting'

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
  padding: 0.9rem;
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
  height: 160px;
  margin-top: 0.75rem;
}

.benchmark-wrap {
  opacity: 0.85;
}

.hint {
  color: #64748b;
  margin-top: 0.5rem;
}

.stats {
  margin-top: 0.75rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.4rem;
}

.stats p {
  margin: 0;
  font-size: 0.9rem;
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
  background: #ecfeff;
  color: #0e7490;
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
</style>
