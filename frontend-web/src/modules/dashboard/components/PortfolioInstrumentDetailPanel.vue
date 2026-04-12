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
      <span>P&amp;L: {{ formatSignedMoney(selectedHolding.unrealized_pnl, selectedHolding.currency || 'EUR') }}</span>
      <span>Sektor: {{ selectedHolding.sector || 'n/a' }}</span>
      <span>Land: {{ selectedHolding.country || 'n/a' }}</span>
      <span>Währung: {{ selectedHolding.currency || 'n/a' }}</span>
    </div>

    <button
      v-if="selectedHolding"
      type="button"
      class="analysis-toggle"
      :disabled="!selectedHolding?.symbol"
      @click="openAnalysisModal"
    >
      Detailanalyse öffnen
    </button>
  </article>

  <div
    v-if="isAnalysisModalOpen && selectedHolding?.symbol"
    class="analysis-modal-overlay"
    role="dialog"
    aria-modal="true"
    aria-labelledby="instrument-analysis-title"
    @click.self="closeAnalysisModal"
  >
    <section class="analysis-modal">
      <header class="analysis-modal-header">
        <div>
          <h3 id="instrument-analysis-title">Instrument-Analyse</h3>
          <p>Aktiv: <strong>{{ selectedHolding.symbol }}</strong></p>
        </div>
        <button type="button" class="analysis-modal-close" @click="closeAnalysisModal">Schließen</button>
      </header>

      <div class="analysis-modal-content">
        <InstrumentAnalysisTabs :selected-symbol="selectedHolding?.symbol ?? null" />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import InstrumentAnalysisTabs from '@/modules/dashboard/components/InstrumentAnalysisTabs.vue'
import type { PortfolioHoldingItem } from '@/shared/model/types'
import { formatMoney, formatPercent, formatSignedMoney } from '@/modules/dashboard/model/portfolioFormatting'

const props = defineProps<{
  selectedHolding: PortfolioHoldingItem | null
}>()

const isAnalysisModalOpen = ref(false)

const openAnalysisModal = (): void => {
  if (!props.selectedHolding?.symbol) return
  isAnalysisModalOpen.value = true
}

const closeAnalysisModal = (): void => {
  isAnalysisModalOpen.value = false
}

const handleEscape = (event: KeyboardEvent): void => {
  if (event.key === 'Escape') closeAnalysisModal()
}

watch(
  () => props.selectedHolding,
  (holding) => {
    if (!holding) closeAnalysisModal()
  }
)

onMounted(() => {
  window.addEventListener('keydown', handleEscape)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleEscape)
})
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

.analysis-toggle {
  display: inline-flex;
  align-items: center;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  color: #0f172a;
  font-size: 0.82rem;
  font-weight: 600;
  padding: 0.4rem 0.65rem;
  cursor: pointer;
}

.analysis-toggle:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.analysis-toggle:hover {
  background: #f8fafc;
}

.analysis-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: rgba(15, 23, 42, 0.45);
}

.analysis-modal {
  width: min(1100px, 100%);
  max-height: calc(100vh - 4rem);
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #cbd5e1;
  box-shadow: 0 24px 48px rgba(15, 23, 42, 0.28);
}

.analysis-modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.95rem 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.analysis-modal-header h3 {
  margin: 0;
}

.analysis-modal-header p {
  margin: 0.3rem 0 0;
  color: #334155;
}

.analysis-modal-close {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  color: #0f172a;
  font-size: 0.82rem;
  font-weight: 600;
  padding: 0.4rem 0.65rem;
  cursor: pointer;
}

.analysis-modal-close:hover {
  background: #f8fafc;
}

.analysis-modal-content {
  padding: 1rem;
  overflow-y: auto;
}

.muted {
  color: #64748b;
}
</style>
