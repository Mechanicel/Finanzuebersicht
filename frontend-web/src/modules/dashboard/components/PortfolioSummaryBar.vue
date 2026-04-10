<template>
  <section class="summary-grid">
    <article class="summary-card" v-for="item in kpis" :key="item.label">
      <p class="label">{{ item.label }}</p>
      <p class="value">{{ item.value }}</p>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PortfolioSummaryReadModel } from '@/shared/model/types'
import { formatMoney, formatNumber, formatPercent, formatPercentPoints } from '@/modules/dashboard/model/portfolioFormatting'

const props = defineProps<{
  summary: PortfolioSummaryReadModel
}>()

const kpis = computed(() => {
  const currency = props.summary.currency || 'EUR'
  return [
    { label: 'Marktwert', value: formatMoney(props.summary.market_value, currency) },
    { label: 'Investierter Wert', value: formatMoney(props.summary.invested_value, currency) },
    { label: 'Unrealized P&L', value: formatMoney(props.summary.unrealized_pnl, currency) },
    { label: 'Rendite', value: formatPercentPoints(props.summary.unrealized_return_pct) },
    { label: 'Holdings', value: formatNumber(props.summary.holdings_count, 0) },
    { label: 'Top Position', value: formatPercent(props.summary.top_position_weight) },
    { label: 'Top 3 Konzentration', value: formatPercent(props.summary.top3_weight) }
  ]
})
</script>

<style scoped>
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.75rem;
}

.summary-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.75rem;
  background: #fff;
}

.label {
  margin: 0;
  font-size: 0.8rem;
  color: #64748b;
}

.value {
  margin: 0.35rem 0 0;
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
}
</style>
