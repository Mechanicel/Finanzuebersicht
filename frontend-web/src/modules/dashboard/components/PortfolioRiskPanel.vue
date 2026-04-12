<template>
  <article class="panel">
    <header class="panel-heading">
      <div class="title-row">
        <h3>Portfolio Risk</h3>
        <span class="scope-badge">Zeitraum + Snapshot</span>
      </div>
      <p class="meta">
        <span>Stand: <strong>{{ asOfLabel }}</strong></span>
        <span>Zeitraum: <strong>{{ rangeLabel }}</strong></span>
        <span>Benchmark: <strong>{{ benchmarkSymbol }}</strong></span>
        <span v-if="methodologyLabel">Methodik: <strong>{{ methodologyLabel }}</strong></span>
      </p>
    </header>

    <section class="group">
      <h4>Risikometriken <span>Zeitraum</span></h4>
      <ul>
        <li><span>Volatilität</span><strong>{{ formatPercentValue(risk.portfolio_volatility) }}</strong></li>
        <li><span>Max Drawdown</span><strong>{{ formatPercentValue(risk.max_drawdown) }}</strong></li>
        <li><span>Korrelation</span><strong>{{ formatNumber(risk.correlation, 4) }}</strong></li>
        <li><span>Beta</span><strong>{{ formatNumber(risk.beta, 4) }}</strong></li>
        <li><span>Tracking Error</span><strong>{{ formatPercentValue(risk.tracking_error) }}</strong></li>
      </ul>
    </section>

    <section class="group">
      <h4>Konzentration <span>Snapshot</span></h4>
      <ul>
        <li><span>Top-Position</span><strong>{{ formatPercent(risk.top_position_weight) }}</strong></li>
        <li><span>Top 3</span><strong>{{ formatPercent(risk.top3_weight) }}</strong></li>
        <li><span>Hinweis</span><strong>{{ concentrationNote }}</strong></li>
      </ul>
    </section>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PortfolioRiskReadModel } from '@/shared/model/types'
import {
  formatDate,
  formatNullableText,
  formatNumber,
  formatPercent,
  formatPercentValue,
  formatRangeLabel,
  getStringMeta,
  mapConcentrationNote,
  mapPortfolioMethodology
} from '@/modules/dashboard/model/portfolioFormatting'

const props = defineProps<{
  risk: PortfolioRiskReadModel
}>()

const asOfLabel = computed(() => formatDate(getStringMeta(props.risk.meta, 'as_of', 'generated_at', 'updated_at') ?? props.risk.as_of))
const rangeLabel = computed(() =>
  formatRangeLabel(props.risk.range ?? getStringMeta(props.risk.meta, 'range'), props.risk.range_label ?? getStringMeta(props.risk.meta, 'range_label'))
)
const benchmarkSymbol = computed(() => formatNullableText(props.risk.benchmark_symbol))
const methodologyLabel = computed(() => {
  const parts = [props.risk.methodology, props.risk.benchmark_relation].filter(
    (part): part is string => typeof part === 'string' && part.trim().length > 0
  )
  return parts.map((part) => mapPortfolioMethodology(part)).join(' · ')
})

const concentrationNote = computed(() => {
  if (!props.risk.concentration_note || props.risk.concentration_note.trim().length === 0) {
    return 'n/a'
  }
  return mapConcentrationNote(props.risk.concentration_note)
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

.panel-heading {
  margin-bottom: 0.38rem;
}

.title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
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
  margin: 0.22rem 0 0;
  color: #64748b;
  font-size: 0.8rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.42rem;
}

.meta strong {
  color: #334155;
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

h4 span {
  margin-left: 0.25rem;
  color: #64748b;
  font-size: 0.72rem;
  letter-spacing: 0;
  text-transform: none;
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
