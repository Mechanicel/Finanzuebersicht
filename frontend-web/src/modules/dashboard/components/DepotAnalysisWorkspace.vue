<template>
  <article class="card section-card depot-analysis">
    <div class="workspace-head">
      <h3>Depot-Analyse</h3>
      <p>Personenbezogene Depotallokation und instrumentbezogene Analyse im Dashboard.</p>
    </div>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" />
    <EmptyState v-else-if="!holdings.length">Keine Holdings für diese Person verfügbar.</EmptyState>

    <div v-else class="workspace-grid">
      <DepotAllocationPanel
        :holdings="holdings"
        :selected-symbol="selectedSymbol"
        :group-by="groupBy"
        :active-group-value="activeGroupValue"
        @update:group-by="onGroupByChanged"
        @update:active-group-value="onActiveGroupValueChanged"
        @select-symbol="onSymbolSelected"
      />
      <InstrumentAnalysisTabs :selected-symbol="selectedSymbol" />
    </div>
  </article>
</template>

<script setup lang="ts">
import axios from 'axios'
import { onMounted, ref, watch } from 'vue'
import { extractApiErrorMessage } from '@/shared/api/extractApiErrorMessage'
import {
  fetchHoldingsSummary,
  fetchPersonPortfolios,
  fetchPortfolioDetails
} from '@/modules/dashboard/api/depotAnalysisApi'
import type { DepotHoldingWithSummary } from '@/shared/model/types'
import DepotAllocationPanel from '@/modules/dashboard/components/DepotAllocationPanel.vue'
import InstrumentAnalysisTabs from '@/modules/dashboard/components/InstrumentAnalysisTabs.vue'
import LoadingState from '@/shared/ui/LoadingState.vue'
import ErrorState from '@/shared/ui/ErrorState.vue'
import EmptyState from '@/shared/ui/EmptyState.vue'

const props = defineProps<{ personId: string }>()

const holdings = ref<DepotHoldingWithSummary[]>([])
const selectedSymbol = ref<string | null>(null)
const groupBy = ref<'position' | 'sector' | 'country' | 'currency'>('position')
const activeGroupValue = ref<string | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

watch(
  () => props.personId,
  () => {
    void loadWorkspace()
  }
)

onMounted(() => {
  void loadWorkspace()
})

function onGroupByChanged(value: 'position' | 'sector' | 'country' | 'currency') {
  groupBy.value = value
  activeGroupValue.value = null
}

function onActiveGroupValueChanged(value: string | null) {
  activeGroupValue.value = value
}

function onSymbolSelected(symbol: string) {
  selectedSymbol.value = symbol
}

async function loadWorkspace() {
  loading.value = true
  error.value = null
  holdings.value = []
  try {
    const portfolios = await fetchPersonPortfolios(props.personId)
    const details = await Promise.all(portfolios.items.map((portfolio) => fetchPortfolioDetails(portfolio.portfolio_id)))
    const flatHoldings: DepotHoldingWithSummary[] = details.flatMap((portfolio) =>
      portfolio.holdings.map((holding) => ({ ...holding, portfolio_id: portfolio.portfolio_id, portfolio_name: portfolio.display_name }))
    )

    const symbols = Array.from(new Set(flatHoldings.map((holding) => holding.symbol).filter(Boolean)))
    const summary = await fetchHoldingsSummary(symbols)
    const bySymbol = new Map(summary.items.map((item) => [item.symbol.toUpperCase(), item]))

    holdings.value = flatHoldings.map((holding) => ({ ...holding, marketdata: bySymbol.get(holding.symbol.toUpperCase()) ?? null }))
    selectedSymbol.value = holdings.value[0]?.symbol ?? null
  } catch (rawError) {
    if (axios.isAxiosError(rawError) && rawError.response?.status === 404) {
      error.value = 'Für diese Person konnten keine Depotdaten geladen werden.'
    } else {
      error.value = extractApiErrorMessage(rawError, 'Depot-Analyse konnte nicht geladen werden.')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.workspace-head p { margin-top: 0.35rem; color: #475569; }
.workspace-grid { display: grid; grid-template-columns: 1.05fr 1fr; gap: 1rem; align-items: start; }
.depot-analysis { overflow: hidden; }
@media (max-width: 1080px) {
  .workspace-grid { grid-template-columns: 1fr; }
}
</style>
