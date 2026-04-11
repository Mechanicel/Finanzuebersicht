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
          <p v-if="financialsSummaryText" class="financials-summary">{{ financialsSummaryText }}</p>

          <template v-if="latestBalanceSheet">
            <h6>Neueste Balance-Sheet-Periode</h6>
            <dl class="kv-grid latest-financials">
              <template v-for="entry in latestBalanceSheetHighlights" :key="entry.key">
                <dt>{{ entry.key }}</dt>
                <dd>{{ entry.value }}</dd>
              </template>
            </dl>
          </template>
          <EmptyState v-else>Für dieses Instrument liegen aktuell keine Balance-Sheet-Daten vor.</EmptyState>

          <section v-if="balanceSheetRows.length" class="balance-sheet-table-wrap">
            <h6>Balance Sheet Verlauf ({{ balanceSheetRows.length }} Perioden)</h6>
            <div class="table-scroll">
              <table class="financials-table">
                <thead>
                  <tr>
                    <th scope="col">Kennzahl</th>
                    <th v-for="row in balanceSheetRows" :key="balanceSheetColumnTitle(row)" scope="col">
                      {{ balanceSheetColumnTitle(row) }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="metric in balanceSheetTableRows" :key="metric.label">
                    <th scope="row">{{ metric.label }}</th>
                    <td v-for="row in balanceSheetRows" :key="`${metric.key}-${balanceSheetColumnTitle(row)}`">
                      {{ formatStatementValue(row[metric.key], metric.monetary, row.reportedCurrency) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
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
  DepotInstrumentBalanceSheetStatementRow,
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
  { key: 'raw', label: 'Technische Details' }
] as const

const timeseriesSeries = ['price', 'benchmark_price', 'returns', 'drawdown', 'benchmark_relative']
const activeTab = ref<(typeof tabs)[number]['key']>('overview')
const loading = ref(false)
const nonFinancialWarnings = ref<string[]>([])
const financialWarnings = ref<string[]>([])
const benchmarkAutoWarning = ref<string | null>(null)
const benchmarkInput = ref('SPY')
const searchTerm = ref('')
const financialPeriod = ref<'annual' | 'quarterly'>('annual')
const selectedSeries = ref(timeseriesSeries[0])

const timeseries = ref<DepotInstrumentTimeseries | null>(null)
const risk = ref<DepotInstrumentRisk | null>(null)
const fundamentals = ref<DepotInstrumentFundamentals | null>(null)
const financials = ref<DepotInstrumentFinancials | null>(null)
const benchmarkCatalog = ref<DepotInstrumentBenchmarkCatalog>({ items: [] })
const benchmarkSearch = ref<DepotInstrumentBenchmarkSearchResult>({ query: '', items: [], total: 0 })

const warnings = computed(() => [...nonFinancialWarnings.value, ...financialWarnings.value])
const chartPoints = computed(() => timeseries.value?.instrument.points ?? [])
const balanceSheetRows = computed<DepotInstrumentBalanceSheetStatementRow[]>(() => {
  const rawRows = financials.value?.statements?.balance_sheet ?? []
  return [...rawRows]
    .sort((left, right) => {
      const leftDate = left?.date ? Date.parse(left.date) : Number.NaN
      const rightDate = right?.date ? Date.parse(right.date) : Number.NaN
      if (Number.isNaN(leftDate) && Number.isNaN(rightDate)) return 0
      if (Number.isNaN(leftDate)) return 1
      if (Number.isNaN(rightDate)) return -1
      return rightDate - leftDate
    })
    .slice(0, 6)
})
const latestBalanceSheet = computed(() => balanceSheetRows.value[0] ?? null)
const latestBalanceSheetHighlights = computed(() => {
  const row = latestBalanceSheet.value
  if (!row) return []
  return [
    { key: 'Stichtag', value: row.date ?? '—' },
    { key: 'Geschäftsjahr', value: row.fiscalYear != null ? String(row.fiscalYear) : '—' },
    { key: 'Periode', value: row.period ?? '—' },
    { key: 'Währung', value: row.reportedCurrency ?? financials.value?.currency ?? '—' },
    { key: 'Gesamtvermögen', value: formatStatementValue(row.totalAssets, true, row.reportedCurrency) },
    { key: 'Gesamtverbindlichkeiten', value: formatStatementValue(row.totalLiabilities, true, row.reportedCurrency) },
    { key: 'Eigenkapital', value: formatStatementValue(row.totalEquity, true, row.reportedCurrency) },
    { key: 'Nettoverschuldung', value: formatStatementValue(row.netDebt, true, row.reportedCurrency) }
  ]
})
const financialsSummaryText = computed(() => {
  if (!financials.value) return ''
  const incomeCount = financials.value.statements?.income_statement?.length ?? 0
  const balanceCount = financials.value.statements?.balance_sheet?.length ?? 0
  const cashflowCount = financials.value.statements?.cash_flow?.length ?? 0
  return `Income Statement: ${incomeCount} | Balance Sheet: ${balanceCount} | Cash Flow: ${cashflowCount}`
})
const balanceSheetTableRows: Array<{ label: string; key: keyof DepotInstrumentBalanceSheetStatementRow; monetary: boolean }> = [
  { label: 'Date', key: 'date', monetary: false },
  { label: 'Fiscal Year', key: 'fiscalYear', monetary: false },
  { label: 'Period', key: 'period', monetary: false },
  { label: 'Reported Currency', key: 'reportedCurrency', monetary: false },
  { label: 'Total Assets', key: 'totalAssets', monetary: true },
  { label: 'Total Current Assets', key: 'totalCurrentAssets', monetary: true },
  { label: 'Total Liabilities', key: 'totalLiabilities', monetary: true },
  { label: 'Total Current Liabilities', key: 'totalCurrentLiabilities', monetary: true },
  { label: 'Total Equity', key: 'totalEquity', monetary: true },
  { label: 'Cash & Cash Equivalents', key: 'cashAndCashEquivalents', monetary: true },
  { label: 'Cash & Short Term Investments', key: 'cashAndShortTermInvestments', monetary: true },
  { label: 'Total Debt', key: 'totalDebt', monetary: true },
  { label: 'Net Debt', key: 'netDebt', monetary: true }
]
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
    resetTabData()
    if (!symbol) return
    void loadActiveTabData()
  },
  { immediate: true }
)

watch(activeTab, () => {
  if (!props.selectedSymbol) return
  void loadActiveTabData()
})

function resetTabData() {
  nonFinancialWarnings.value = []
  financialWarnings.value = []
  benchmarkAutoWarning.value = null
  timeseries.value = null
  risk.value = null
  fundamentals.value = null
  financials.value = null
  benchmarkCatalog.value = { items: [] }
  benchmarkSearch.value = { query: '', items: [], total: 0 }
  selectedSeries.value = timeseriesSeries[0]
}

function recomputeNonFinancialWarnings() {
  nonFinancialWarnings.value = [
    ...(timeseries.value?.meta?.warnings ?? []).map((entry) => entry.message),
    ...(risk.value?.meta?.warnings ?? []).map((entry) => entry.message),
    ...(benchmarkAutoWarning.value ? [benchmarkAutoWarning.value] : [])
  ]
}

async function withLoading(task: () => Promise<void>) {
  loading.value = true
  try {
    await task()
  } catch {
    nonFinancialWarnings.value = ['Einige Instrumentdaten konnten nicht geladen werden.']
    financialWarnings.value = []
  } finally {
    loading.value = false
  }
}

async function loadActiveTabData() {
  if (!props.selectedSymbol) return
  const symbol = props.selectedSymbol
  if (activeTab.value === 'overview') {
    await withLoading(async () => {
      await loadTimeseries(timeseriesSeries[0], false, symbol)
    })
    return
  }
  if (activeTab.value === 'returns') {
    await withLoading(async () => {
      await loadTimeseries(selectedSeries.value, false, symbol)
    })
    return
  }
  if (activeTab.value === 'risk') {
    await withLoading(async () => {
      await loadRiskTabData(symbol)
    })
    return
  }
  if (activeTab.value === 'fundamentals') {
    await withLoading(async () => {
      if (!fundamentals.value || fundamentals.value.symbol !== symbol) {
        fundamentals.value = await fetchInstrumentFundamentals(symbol)
      }
    })
    return
  }
  if (activeTab.value === 'financials') {
    await withLoading(async () => {
      await loadFinancials(symbol)
    })
    return
  }
  await withLoading(async () => {
    await Promise.all([loadTimeseries(timeseriesSeries[0], false, symbol), loadRisk(symbol)])
  })
}

async function loadRiskTabData(symbol: string, force = false) {
  const shouldLoadCatalog = benchmarkCatalog.value.items.length === 0 || force
  const shouldLoadRisk = force || !risk.value || risk.value.symbol !== symbol || risk.value.benchmark !== benchmarkInput.value
  if (!shouldLoadCatalog && !shouldLoadRisk) return

  const [riskPayload, benchmarkPayload, catalogPayload] = await Promise.all([
    shouldLoadRisk ? fetchInstrumentRisk(symbol, benchmarkInput.value) : Promise.resolve(risk.value),
    shouldLoadRisk ? fetchInstrumentBenchmark(symbol, benchmarkInput.value) : Promise.resolve(null),
    shouldLoadCatalog ? fetchBenchmarkCatalog() : Promise.resolve(benchmarkCatalog.value)
  ])

  if (riskPayload) risk.value = riskPayload
  if (catalogPayload) benchmarkCatalog.value = catalogPayload
  if (benchmarkPayload?.benchmark && benchmarkPayload.benchmark !== benchmarkInput.value) {
    benchmarkAutoWarning.value = `Benchmark automatisch auf ${benchmarkPayload.benchmark} gesetzt.`
  } else {
    benchmarkAutoWarning.value = null
  }
  recomputeNonFinancialWarnings()
}

async function loadRisk(symbol: string, force = false) {
  const shouldLoad = force || !risk.value || risk.value.symbol !== symbol || risk.value.benchmark !== benchmarkInput.value
  if (!shouldLoad) return
  risk.value = await fetchInstrumentRisk(symbol, benchmarkInput.value)
  recomputeNonFinancialWarnings()
}

async function loadTimeseries(series: string, force = false, explicitSymbol?: string) {
  const symbol = explicitSymbol ?? props.selectedSymbol
  if (!symbol) return
  selectedSeries.value = series
  const shouldLoad =
    force ||
    !timeseries.value ||
    timeseries.value.symbol !== symbol ||
    timeseries.value.series !== series ||
    timeseries.value.benchmark_symbol !== benchmarkInput.value
  if (!shouldLoad) return
  timeseries.value = await fetchInstrumentTimeseries(symbol, series, benchmarkInput.value)
  recomputeNonFinancialWarnings()
}

async function reloadRisk() {
  if (!props.selectedSymbol) return
  await withLoading(async () => {
    await loadRiskTabData(props.selectedSymbol, true)
  })
}

function selectBenchmark(symbol: string) {
  benchmarkInput.value = symbol
  void applyBenchmark()
}

async function applyBenchmark() {
  if (!props.selectedSymbol) return
  if (activeTab.value === 'returns') {
    await withLoading(async () => {
      await loadTimeseries(selectedSeries.value, true)
    })
    return
  }
  if (activeTab.value === 'risk') {
    await withLoading(async () => {
      await loadRiskTabData(props.selectedSymbol as string, true)
    })
    return
  }
  if (activeTab.value === 'raw') {
    await withLoading(async () => {
      await Promise.all([loadTimeseries(timeseriesSeries[0], true), loadRisk(props.selectedSymbol as string, true)])
    })
  }
}

async function searchBenchmark() {
  const query = searchTerm.value.trim()
  if (!query) {
    benchmarkSearch.value = { query: '', items: [], total: 0 }
    return
  }
  benchmarkSearch.value = await searchBenchmarkCatalog(query)
}

async function loadFinancials(symbol = props.selectedSymbol ?? '') {
  if (activeTab.value !== 'financials' || !symbol) return
  if (financials.value?.symbol === symbol && financials.value.period === financialPeriod.value) return
  financials.value = await fetchInstrumentFinancials(symbol, financialPeriod.value)
  financialWarnings.value = (financials.value.meta?.warnings ?? []).map((entry) => `${entry.code}: ${entry.message}`)
}

function balanceSheetColumnTitle(row: DepotInstrumentBalanceSheetStatementRow) {
  return [row.date, row.period, row.fiscalYear != null ? `FY${row.fiscalYear}` : undefined].filter(Boolean).join(' · ') || 'Periode'
}

function formatStatementValue(value: unknown, monetary: boolean, currency?: string | null) {
  if (value == null || value === '') return '—'
  if (!monetary) return String(value)
  const numericValue = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(numericValue)) return String(value)
  const resolvedCurrency = currency ?? financials.value?.currency ?? undefined
  if (resolvedCurrency) {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: resolvedCurrency,
      notation: 'compact',
      maximumFractionDigits: 2
    }).format(numericValue)
  }
  return new Intl.NumberFormat('de-DE', {
    notation: 'compact',
    maximumFractionDigits: 2
  }).format(numericValue)
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
.financials-summary { margin: 0.35rem 0 0.65rem; color: #475569; font-size: 0.9rem; }
.latest-financials { margin-bottom: 0.85rem; }
.balance-sheet-table-wrap { display: grid; gap: 0.5rem; }
.table-scroll { overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 8px; }
.financials-table { width: 100%; border-collapse: collapse; min-width: 860px; }
.financials-table th,
.financials-table td {
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
  padding: 0.45rem 0.55rem;
  white-space: nowrap;
}
.financials-table thead th {
  position: sticky;
  top: 0;
  background: #f8fafc;
  z-index: 1;
}
.financials-table tbody tr:last-child th,
.financials-table tbody tr:last-child td { border-bottom: none; }
</style>
