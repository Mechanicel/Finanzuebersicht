<template>
  <article class="panel">
    <h3>Portfolio Risk</h3>
    <p class="meta">Benchmark: {{ risk.benchmark_symbol || 'n/a' }}</p>

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
        <li><span>Hinweis</span><strong>{{ mapConcentrationNote(risk.concentration_note) }}</strong></li>
      </ul>
    </section>
  </article>
</template>

<script setup lang="ts">
import type { PortfolioRiskReadModel } from '@/shared/model/types'
import { formatNumber, formatPercent, formatPercentPoints, mapConcentrationNote } from '@/modules/dashboard/model/portfolioFormatting'

defineProps<{
  risk: PortfolioRiskReadModel
}>()
</script>

<style scoped>
.panel {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.9rem;
  background: #fff;
}

h3 {
  margin: 0;
}

.meta {
  margin: 0.3rem 0 0.5rem;
  color: #64748b;
  font-size: 0.85rem;
}

.group + .group {
  margin-top: 0.65rem;
}

h4 {
  margin: 0 0 0.35rem;
  font-size: 0.83rem;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.4rem;
}

li {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  font-size: 0.92rem;
}

span {
  color: #64748b;
}

strong {
  color: #0f172a;
}
</style>
