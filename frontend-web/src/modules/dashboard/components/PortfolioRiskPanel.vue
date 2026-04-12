<template>
  <article class="panel">
    <h3>Portfolio Risk</h3>
    <p class="meta">Typ: Snapshot-Kennzahlen</p>
    <p class="meta">Stand: {{ asOfLabel }}</p>
    <p class="meta">Benchmark: {{ risk.benchmark_symbol || 'n/a' }}</p>
    <p v-if="methodologyLabel !== 'n/a'" class="meta">Methodik: {{ methodologyLabel }}</p>

    <section class="group">
      <h4>Risikometriken</h4>
      <ul>
        <li><span>Volatilität</span><strong>{{ formatPercentPoints(risk.portfolio_volatility) }}</strong></li>
        <li><span>Max Drawdown</span><strong>{{ formatPercentPoints(risk.max_drawdown) }}</strong></li>
        <li><span>Korrelation</span><strong>{{ formatNumber(risk.correlation, 4) }}</strong></li>
        <li><span>Beta</span><strong>{{ formatNumber(risk.beta, 4) }}</strong></li>
        <li><span>Tracking Error</span><strong>{{ formatPercentPoints(risk.tracking_error) }}</strong></li>
      </ul>
    </section>

    <section class="group">
      <h4>Konzentration</h4>
      <ul>
        <li><span>Top Position</span><strong>{{ formatPercent(risk.top_position_weight) }}</strong></li>
        <li><span>Top 3</span><strong>{{ formatPercent(risk.top3_weight) }}</strong></li>
        <li><span>Hinweis</span><strong>{{ concentrationNote }}</strong></li>
      </ul>
    </section>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PortfolioRiskReadModel } from '@/shared/model/types'
import { formatAsOf, formatNumber, formatPercent, formatPercentPoints, mapConcentrationNote } from '@/modules/dashboard/model/portfolioFormatting'

const props = defineProps<{
  risk: PortfolioRiskReadModel
}>()

const concentrationNote = computed(() => {
  if (!props.risk.concentration_note || props.risk.concentration_note.trim().length === 0) {
    return 'n/a'
  }
  return mapConcentrationNote(props.risk.concentration_note)
})

const asOfLabel = computed(() => formatAsOf(props.risk.as_of))
const methodologyLabel = computed(() => {
  const method = props.risk.meta?.methodology
  return typeof method === 'string' && method.trim().length > 0 ? method : 'n/a'
})
</script>

<style scoped>
.panel {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.72rem;
  background: #fff;
}

h3 {
  margin: 0;
}

.meta {
  margin: 0.22rem 0 0.38rem;
  color: #64748b;
  font-size: 0.8rem;
}

.group + .group {
  margin-top: 0.45rem;
}

h4 {
  margin: 0 0 0.22rem;
  font-size: 0.79rem;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.28rem;
}

li {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  font-size: 0.86rem;
}

span {
  color: #64748b;
}

strong {
  color: #0f172a;
}
</style>
