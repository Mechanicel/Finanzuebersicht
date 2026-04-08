<template>
  <section class="panel-root">
    <div class="panel-head">
      <h4>Depot-Allokation</h4>
      <p>Gruppierung nach Position, Sektor, Land und Währung.</p>
    </div>

    <div class="group-toggle" role="tablist" aria-label="Allokationsgruppe">
      <button
        v-for="group in groups"
        :key="group.key"
        class="chip"
        :class="{ active: groupBy === group.key }"
        type="button"
        @click="$emit('update:groupBy', group.key)"
      >
        {{ group.label }}
      </button>
    </div>

    <div v-if="summaryRows.length" class="summary-grid">
      <button
        v-for="row in summaryRows"
        :key="`${groupBy}-${row.key}`"
        class="summary-card"
        type="button"
        @click="pickRow(row)"
      >
        <span class="summary-label">{{ row.label }}</span>
        <strong>{{ row.count }} Positionen</strong>
        <span class="summary-share">{{ row.share.toFixed(1) }}%</span>
      </button>
    </div>
    <EmptyState v-else>Keine Allokationsdaten verfügbar.</EmptyState>

    <div class="table-shell">
      <h5>Holdings</h5>
      <table v-if="filteredHoldings.length" class="holdings-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Name</th>
            <th>Sektor</th>
            <th>Land</th>
            <th>Währung</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="holding in filteredHoldings"
            :key="holding.holding_id"
            :class="{ active: selectedSymbol === holding.symbol }"
            @click="$emit('select-symbol', holding.symbol)"
          >
            <td>{{ holding.symbol }}</td>
            <td>{{ holding.marketdata?.company_name ?? holding.display_name ?? '–' }}</td>
            <td>{{ holding.marketdata?.sector ?? 'n/a' }}</td>
            <td>{{ holding.marketdata?.country ?? 'n/a' }}</td>
            <td>{{ holding.marketdata?.currency ?? holding.currency }}</td>
          </tr>
        </tbody>
      </table>
      <EmptyState v-else>Keine Holdings in dieser Gruppierung.</EmptyState>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { DepotHoldingWithSummary } from '@/shared/model/types'
import EmptyState from '@/shared/ui/EmptyState.vue'

const props = defineProps<{
  holdings: DepotHoldingWithSummary[]
  selectedSymbol: string | null
  groupBy: 'position' | 'sector' | 'country' | 'currency'
  activeGroupValue: string | null
}>()

const emit = defineEmits<{
  'update:groupBy': [value: 'position' | 'sector' | 'country' | 'currency']
  'update:activeGroupValue': [value: string | null]
  'select-symbol': [symbol: string]
}>()

const groups = [
  { key: 'position', label: 'Position' },
  { key: 'sector', label: 'Sektor' },
  { key: 'country', label: 'Land' },
  { key: 'currency', label: 'Währung' }
] as const

const summaryRows = computed(() => {
  const map = new Map<string, { label: string; count: number }>()
  for (const holding of props.holdings) {
    const key = getGroupValue(holding)
    const entry = map.get(key)
    if (entry) entry.count += 1
    else map.set(key, { label: key, count: 1 })
  }
  const total = props.holdings.length || 1
  return Array.from(map.entries())
    .map(([key, value]) => ({ key, label: value.label, count: value.count, share: (value.count / total) * 100 }))
    .sort((a, b) => b.count - a.count)
})

const activeSummaryKey = computed(() => props.activeGroupValue ?? summaryRows.value[0]?.key ?? null)

const filteredHoldings = computed(() => {
  if (!activeSummaryKey.value) return props.holdings
  return props.holdings.filter((holding) => getGroupValue(holding) === activeSummaryKey.value)
})

function getGroupValue(holding: DepotHoldingWithSummary): string {
  if (props.groupBy === 'position') return holding.symbol
  if (props.groupBy === 'sector') return holding.marketdata?.sector ?? 'Unbekannter Sektor'
  if (props.groupBy === 'country') return holding.marketdata?.country ?? 'Unbekanntes Land'
  return holding.marketdata?.currency ?? holding.currency
}

function pickRow(row: { key: string }) {
  emit('update:activeGroupValue', row.key)
  const match = props.holdings.find((holding) => getGroupValue(holding) === row.key)
  if (match) emit('select-symbol', match.symbol)
}
</script>

<style scoped>
.panel-root { display: grid; gap: 0.8rem; }
.panel-head p { margin: 0.25rem 0 0; color: #64748b; }
.group-toggle { display: flex; flex-wrap: wrap; gap: 0.35rem; }
.chip { border: 1px solid #cbd5e1; background: #f8fafc; border-radius: 999px; padding: 0.25rem 0.65rem; cursor: pointer; }
.chip.active { background: #dbeafe; border-color: #60a5fa; color: #1d4ed8; }
.summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 0.45rem; }
.summary-card { text-align: left; border: 1px solid #e2e8f0; background: white; border-radius: 10px; padding: 0.5rem; cursor: pointer; display: grid; }
.summary-label { color: #475569; font-size: 0.8rem; }
.summary-share { color: #1e293b; font-size: 0.8rem; }
.table-shell h5 { margin: 0 0 0.35rem; }
.holdings-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.holdings-table th, .holdings-table td { border-bottom: 1px solid #e2e8f0; padding: 0.45rem; text-align: left; }
.holdings-table tbody tr { cursor: pointer; }
.holdings-table tbody tr.active { background: #eff6ff; }
</style>
