<template>
  <article class="panel">
    <header class="panel-header">
      <div>
        <h3>Instrument-Detail</h3>
        <p v-if="selectedHolding">
          Aktiv: <strong>{{ selectedHolding.symbol || 'n/a' }}</strong>
          <span class="muted"> · {{ selectedHolding.display_name || selectedHolding.portfolio_name || 'Ohne Namen' }}</span>
        </p>
        <p v-else class="muted">Bitte eine Holding auswählen.</p>
      </div>
    </header>

    <div v-if="selectedHolding" class="holding-context">
      <span>Gewicht: {{ formatPercent(selectedHolding.weight) }}</span>
      <span>Marktwert: {{ formatMoney(selectedHolding.market_value, selectedHolding.currency || 'EUR') }}</span>
      <span>P&L: {{ formatSignedMoney(selectedHolding.unrealized_pnl, selectedHolding.currency || 'EUR') }}</span>
      <span v-if="selectedHolding.sector">Sektor: {{ selectedHolding.sector }}</span>
      <span v-if="selectedHolding.country">Land: {{ selectedHolding.country }}</span>
      <span v-if="selectedHolding.currency">Währung: {{ selectedHolding.currency }}</span>
    </div>

    <InstrumentAnalysisTabs :selected-symbol="selectedHolding?.symbol ?? null" />
  </article>
</template>

<script setup lang="ts">
import InstrumentAnalysisTabs from '@/modules/dashboard/components/InstrumentAnalysisTabs.vue'
import type { PortfolioHoldingItem } from '@/shared/model/types'
import { formatMoney, formatPercent, formatSignedMoney } from '@/modules/dashboard/model/portfolioFormatting'

defineProps<{
  selectedHolding: PortfolioHoldingItem | null
}>()
</script>

<style scoped>
.panel {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.9rem;
  background: #fff;
}

.panel-header h3 {
  margin: 0;
}

.panel-header p {
  margin: 0.3rem 0 0;
}

.holding-context {
  margin: 0.65rem 0 0.75rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  font-size: 0.88rem;
  color: #334155;
}

.muted {
  color: #64748b;
}
</style>
