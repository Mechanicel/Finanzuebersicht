<template>
  <section class="portfolio-cockpit">
    <header class="cockpit-header">
      <div>
        <p class="eyebrow">Portfolio-Cockpit</p>
        <h2>Portfolio Dashboard</h2>
      </div>
      <button class="btn flow-btn" type="button" @click="void loadAll()" :disabled="loading">Neu laden</button>
    </header>

    <LoadingState v-if="loading && !hasData" />
    <ErrorState v-else-if="error && !hasData" :message="error" />
    <EmptyState v-else-if="isEmpty">Keine Portfolio-Daten für dieses Personenkonto verfügbar.</EmptyState>

    <template v-else>
      <PortfolioCoverageBanner v-if="coverage" :coverage="coverage" />
      <PortfolioSummaryBar v-if="summary" :summary="summary" />

      <div class="top-row">
        <PortfolioPerformancePanel v-if="performance" :performance="performance" :currency="summary?.currency" />
        <PortfolioRiskPanel v-if="risk" :risk="risk" />
      </div>

      <PortfolioExposuresPanel v-if="exposures" :exposures="exposures" :currency="summary?.currency" />

      <div class="workspace-grid">
        <PortfolioHoldingsTable
          v-if="holdings"
          :items="holdings.items"
          :currency="summary?.currency"
          :selected-symbol="selectedSymbol"
          @select-holding="onSelectHolding"
        />
        <PortfolioInstrumentDetailPanel :selected-holding="selectedHolding" />
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, watch, toRef, ref } from 'vue'
import EmptyState from '@/shared/ui/EmptyState.vue'
import ErrorState from '@/shared/ui/ErrorState.vue'
import LoadingState from '@/shared/ui/LoadingState.vue'
import PortfolioSummaryBar from '@/modules/dashboard/components/PortfolioSummaryBar.vue'
import PortfolioPerformancePanel from '@/modules/dashboard/components/PortfolioPerformancePanel.vue'
import PortfolioRiskPanel from '@/modules/dashboard/components/PortfolioRiskPanel.vue'
import PortfolioExposuresPanel from '@/modules/dashboard/components/PortfolioExposuresPanel.vue'
import PortfolioHoldingsTable from '@/modules/dashboard/components/PortfolioHoldingsTable.vue'
import PortfolioCoverageBanner from '@/modules/dashboard/components/PortfolioCoverageBanner.vue'
import PortfolioInstrumentDetailPanel from '@/modules/dashboard/components/PortfolioInstrumentDetailPanel.vue'
import { usePortfolioDashboard } from '@/modules/dashboard/composables/usePortfolioDashboard'
import type { PortfolioHoldingItem } from '@/shared/model/types'

const props = defineProps<{ personId: string }>()

const personIdRef = toRef(props, 'personId')
const portfolioDashboard = usePortfolioDashboard(personIdRef)

const summary = computed(() => portfolioDashboard.summary.value)
const performance = computed(() => portfolioDashboard.performance.value)
const exposures = computed(() => portfolioDashboard.exposures.value)
const holdings = computed(() => portfolioDashboard.holdings.value)
const risk = computed(() => portfolioDashboard.risk.value)
const coverage = computed(() => portfolioDashboard.coverage.value)

const loading = computed(() => portfolioDashboard.loading.value)
const error = computed(() => portfolioDashboard.error.value)
const hasData = computed(() => portfolioDashboard.hasData.value)
const isEmpty = computed(() => portfolioDashboard.isEmpty.value)

const loadAll = portfolioDashboard.loadAll
const selectedSymbol = ref<string | null>(null)
const fallbackHolding = (items: PortfolioHoldingItem[]) => items.find((item) => item.symbol) ?? items[0] ?? null
const selectedHolding = computed<PortfolioHoldingItem | null>(() => {
  const items = holdings.value?.items ?? []
  if (!items.length) return null
  if (!selectedSymbol.value) return fallbackHolding(items)
  return items.find((item) => item.symbol === selectedSymbol.value) ?? fallbackHolding(items)
})

function onSelectHolding(item: PortfolioHoldingItem) {
  selectedSymbol.value = item.symbol ?? null
}

watch(
  () => holdings.value?.items,
  (items) => {
    if (!items || !items.length) {
      selectedSymbol.value = null
      return
    }
    const hasSelection = selectedSymbol.value && items.some((item) => item.symbol === selectedSymbol.value)
    if (!hasSelection) {
      selectedSymbol.value = fallbackHolding(items)?.symbol ?? null
    }
  },
  { immediate: true }
)

watch(
  personIdRef,
  (newPersonId) => {
    if (newPersonId) {
      void loadAll()
    }
  },
  { immediate: false }
)

onMounted(() => {
  if (props.personId) {
    void loadAll()
  }
})
</script>

<style scoped>
.portfolio-cockpit {
  display: grid;
  gap: 0.85rem;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  padding: 1rem;
  background: #f8fafc;
}

.cockpit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.eyebrow {
  margin: 0;
  color: #475569;
  font-weight: 600;
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

h2 {
  margin: 0.2rem 0 0;
  font-size: 1.25rem;
}

.top-row {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  gap: 0.75rem;
}

.workspace-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  gap: 0.75rem;
}

@media (max-width: 900px) {
  .top-row {
    grid-template-columns: 1fr;
  }

  .workspace-grid {
    grid-template-columns: 1fr;
  }
}
</style>
