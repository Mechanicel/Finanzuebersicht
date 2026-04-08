<template>
  <section class="tabs-root">
    <header class="tabs-head">
      <h4>Instrument-Analyse</h4>
      <p v-if="selectedSymbol">Aktives Instrument: <strong>{{ selectedSymbol }}</strong></p>
      <p v-else>Wähle links ein Instrument, um Detailanalysen zu laden.</p>
    </header>

    <div class="tab-nav">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <EmptyState v-if="!selectedSymbol">Noch kein Instrument ausgewählt.</EmptyState>

    <template v-else>
      <div v-if="warnings.length" class="warning-box">
        <p v-for="warning in warnings" :key="warning">⚠️ {{ warning }}</p>
      </div>

      <LoadingState v-if="loading" />

      <template v-else>
        <article v-if="activeTab === 'overview'" class="card content-card">
          <h5>Überblick</h5>
          <dl class="kv-grid">
            <template v-for="item in overviewPairs" :key="item.key">
              <dt>{{ item.key }}</dt>
              <dd>{{ item.value }}</dd>
            </template>
          </dl>
        </article>

        <article v-else-if="activeTab === 'returns'" class="card content-card">
          <div class="row-between">
            <h5>Kurs & Rendite</h5>
            <label>
              Benchmark
              <input v-model="benchmarkInput" class="input" placeholder="z. B. SPY" @change="applyBenchmark" />
            </label>
          </div>

          <div class="series-select">
            <button v-for="series in timeseriesSeries" :key="series" class="chip" @click="loadTimeseries(series)">
              {{ series }}
            </button>
          </div>

          <div v-if="chartPoints.length" class="chart-box">
            <SimpleLineChart :points="chartPoints" />
          </div>
          <EmptyState v-else>Keine Zeitreihendaten für die gewählte Serie.</EmptyState>
        </article>

        <article v-else-if="activeTab === 'risk'" class="card content-card">
          <div class="row-between">
            <h5>Risiko & Benchmark</h5>
            <button type="button" class="btn small" @click="reloadRisk">Aktualisieren</button>
          </div>
          <p>Volatilität Instrument: {{ risk?.volatility_proxy ?? 'n/a' }}</p>
          <p>Volatilität Benchmark: {{ risk?.benchmark_volatility_proxy ?? 'n/a' }}</p>
          <p>Aligned Points: {{ risk?.aligned_points ?? 0 }}</p>

          <h6>Benchmark-Katalog</h6>
          <ul class="list">
            <li v-for="item in benchmarkCatalog.items" :key="item.symbol">
              <button type="button" class="link-btn" @click="selectBenchmark(item.symbol)">{{ item.symbol }} – {{ item.name }}</button>
            </li>
          </ul>

          <h6>Freie Vergleichssuche</h6>
          <div class="inline-row">
            <input v-model="searchTerm" class="input" placeholder="Name oder Symbol" />
            <button type="button" class="btn small" @click="searchBenchmark">Suchen</button>
          </div>
          <ul class="list" v-if="benchmarkSearch.items.length">
            <li v-for="item in benchmarkSearch.items" :key="`${item.symbol}-${item.name}`">
              {{ item.symbol }} – {{ item.name }}
            </li>
          </ul>
        </article>

        <article v-else-if="activeTab === 'fundamentals'" class="card content-card">
          <h5>Fundamentals</h5>
          <dl class="kv-grid">
            <template v-for="entry in fundamentalsEntries" :key="entry.key">
              <dt>{{ entry.key }}</dt>
              <dd>{{ entry.value }}</dd>
            </template>
          </dl>
        </article>

        <article v-else-if="activeTab === 'financials'" class="card content-card">
          <div class="row-between">
            <h5>Finanzberichte</h5>
            <select v-model="financialPeriod" class="input" @change="loadFinancials">
              <option value="annual">Annual</option>
              <option value="quarterly">Quarterly</option>
            </select>
          </div>
          <div class="blocks">
            <section class="block">
              <h6>Income Statement</h6>
              <p>{{ financials?.statements?.income_statement?.length ?? 0 }} Einträge</p>
            </section>
            <section class="block">
              <h6>Balance Sheet</h6>
              <p>{{ financials?.statements?.balance_sheet?.length ?? 0 }} Einträge</p>
            </section>
            <section class="block">
              <h6>Cash Flow</h6>
              <p>{{ financials?.statements?.cash_flow?.length ?? 0 }} Einträge</p>
            </section>
          </div>
        </article>

        <article v-else class="card content-card">
          <h5>Rohdaten</h5>
          <div class="blocks">
            <section class="block">
              <h6>Timeseries Meta</h6>
              <p>Serie: {{ timeseries?.series ?? 'n/a' }} | Benchmark: {{ timeseries?.benchmark_symbol ?? 'n/a' }}</p>
            </section>
            <section class="block">
              <h6>Risk Meta</h6>
              <p>Benchmark: {{ risk?.benchmark ?? 'n/a' }} | Aligned Points: {{ risk?.aligned_points ?? 0 }}</p>
            </section>
          </div>
        </article>
      </template>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  fetchBenchmarkCatalog,
  fetchInstrumentBenchmark,
  fetchInstrumentFinancials,
  fetchInstrumentFundamentals,
  fetchInstrumentRisk,
  fetchInstrumentTimeseries,
  searchBenchmarkCatalog
} from '@/modules/dashboard/api/depotAnalysisApi'
import type {
  DepotInstrumentBenchmarkCatalog,
  DepotInstrumentBenchmarkSearchResult,
  DepotInstrumentFinancials,
  DepotInstrumentFundamentals,
  DepotInstrumentRisk,
  DepotInstrumentTimeseries
} from '@/shared/model/types'
import EmptyState from '@/shared/ui/EmptyState.vue'
import LoadingState from '@/shared/ui/LoadingState.vue'
import SimpleLineChart from '@/shared/ui/SimpleLineChart.vue'

const props = defineProps<{ selectedSymbol: string | null }>()

const tabs = [
  { key: 'overview', label: 'Überblick' },
  { key: 'returns', label: 'Kurs & Rendite' },
  { key: 'risk', label: 'Risiko & Benchmark' },
  { key: 'fundamentals', label: 'Fundamentals' },
  { key: 'financials', label: 'Finanzberichte' },
  { key: 'raw', label: 'Rohdaten' }
] as const

const timeseriesSeries = ['price', 'benchmark_price', 'returns', 'drawdown', 'benchmark_relative']
const activeTab = ref<(typeof tabs)[number]['key']>('overview')
const loading = ref(false)
const warnings = ref<string[]>([])
const benchmarkInput = ref('SPY')
const searchTerm = ref('')
const financialPeriod = ref<'annual' | 'quarterly'>('annual')

const timeseries = ref<DepotInstrumentTimeseries | null>(null)
const risk = ref<DepotInstrumentRisk | null>(null)
const fundamentals = ref<DepotInstrumentFundamentals | null>(null)
const financials = ref<DepotInstrumentFinancials | null>(null)
const benchmarkCatalog = ref<DepotInstrumentBenchmarkCatalog>({ items: [] })
const benchmarkSearch = ref<DepotInstrumentBenchmarkSearchResult>({ query: '', items: [], total: 0 })

const chartPoints = computed(() => timeseries.value?.instrument.points ?? [])
const overviewPairs = computed(() => [
  { key: 'Symbol', value: props.selectedSymbol ?? 'n/a' },
  { key: 'Benchmark', value: risk.value?.benchmark ?? benchmarkInput.value },
  { key: 'Datenpunkte', value: String(chartPoints.value.length) },
  { key: 'Warnungen', value: String(warnings.value.length) }
])
const fundamentalsEntries = computed(() =>
  Object.entries(fundamentals.value ?? {})
    .filter(([key, value]) => typeof value === 'string' || typeof value === 'number')
    .slice(0, 12)
    .map(([key, value]) => ({ key, value: String(value) }))
)

watch(
  () => props.selectedSymbol,
  (symbol) => {
    if (!symbol) return
    void loadAll(symbol)
  },
  { immediate: true }
)

async function loadAll(symbol: string) {
  loading.value = true
  warnings.value = []
  try {
    const [seriesPayload, riskPayload, benchmarkPayload, catalogPayload, fundamentalsPayload, financialPayload] = await Promise.all([
      fetchInstrumentTimeseries(symbol, timeseriesSeries[0], benchmarkInput.value),
      fetchInstrumentRisk(symbol, benchmarkInput.value),
      fetchInstrumentBenchmark(symbol, benchmarkInput.value),
      fetchBenchmarkCatalog(),
      fetchInstrumentFundamentals(symbol),
      fetchInstrumentFinancials(symbol, financialPeriod.value)
    ])

    timeseries.value = seriesPayload
    risk.value = riskPayload
    benchmarkCatalog.value = catalogPayload
    fundamentals.value = fundamentalsPayload
    financials.value = financialPayload

    const collectedWarnings = [
      ...(seriesPayload.meta?.warnings ?? []).map((entry) => `${entry.code}: ${entry.message}`),
      ...(riskPayload.meta?.warnings ?? []).map((entry) => `${entry.code}: ${entry.message}`),
      ...(financialPayload.meta?.warnings ?? []).map((entry) => `${entry.code}: ${entry.message}`)
    ]
    if (benchmarkPayload?.benchmark && benchmarkPayload.benchmark !== benchmarkInput.value) {
      collectedWarnings.push(`Benchmark automatisch auf ${benchmarkPayload.benchmark} gesetzt.`)
    }
    warnings.value = collectedWarnings
  } catch {
    warnings.value = ['Einige Instrumentdaten konnten nicht geladen werden.']
  } finally {
    loading.value = false
  }
}

async function loadTimeseries(series: string) {
  if (!props.selectedSymbol) return
  timeseries.value = await fetchInstrumentTimeseries(props.selectedSymbol, series, benchmarkInput.value)
}

async function reloadRisk() {
  if (!props.selectedSymbol) return
  risk.value = await fetchInstrumentRisk(props.selectedSymbol, benchmarkInput.value)
}

function selectBenchmark(symbol: string) {
  benchmarkInput.value = symbol
  void applyBenchmark()
}

async function applyBenchmark() {
  if (!props.selectedSymbol) return
  await Promise.all([loadTimeseries(timeseries.value?.series ?? timeseriesSeries[0]), reloadRisk()])
}

async function searchBenchmark() {
  const query = searchTerm.value.trim()
  if (!query) {
    benchmarkSearch.value = { query: '', items: [], total: 0 }
    return
  }
  benchmarkSearch.value = await searchBenchmarkCatalog(query)
}

async function loadFinancials() {
  if (!props.selectedSymbol) return
  financials.value = await fetchInstrumentFinancials(props.selectedSymbol, financialPeriod.value)
}
</script>

<style scoped>
.tabs-root { display: grid; gap: 0.75rem; }
.tabs-head p { margin: 0.2rem 0 0; color: #64748b; }
.tab-nav { display: flex; flex-wrap: wrap; gap: 0.35rem; }
.tab-btn { border: 1px solid #cbd5e1; background: #f8fafc; border-radius: 8px; padding: 0.35rem 0.6rem; }
.tab-btn.active { background: #dbeafe; border-color: #60a5fa; color: #1d4ed8; }
.warning-box { border: 1px solid #f59e0b; background: #fffbeb; border-radius: 8px; padding: 0.45rem 0.65rem; color: #92400e; }
.content-card { padding: 0.8rem; }
.row-between { display: flex; justify-content: space-between; gap: 0.75rem; align-items: center; flex-wrap: wrap; }
.inline-row { display: flex; gap: 0.45rem; }
.input { border: 1px solid #cbd5e1; border-radius: 8px; padding: 0.35rem 0.55rem; }
.chip { border: 1px solid #cbd5e1; background: #f8fafc; border-radius: 999px; padding: 0.2rem 0.55rem; }
.chart-box { height: 260px; }
.kv-grid { display: grid; grid-template-columns: auto 1fr; gap: 0.35rem 0.7rem; margin: 0; }
.kv-grid dt { color: #475569; }
.kv-grid dd { margin: 0; color: #0f172a; }
.blocks { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.55rem; }
.block { border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.45rem; background: #f8fafc; }
.block h6 { margin: 0 0 0.25rem; }
.block p { margin: 0; }
.list { margin: 0.2rem 0 0; padding-left: 1.1rem; }
.link-btn { border: none; padding: 0; background: none; color: #2563eb; text-decoration: underline; cursor: pointer; }
.small { padding: 0.25rem 0.45rem; font-size: 0.8rem; }
</style>
