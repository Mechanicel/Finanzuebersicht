<template>
  <article class="panel">
    <header class="panel-header">
      <h3>Holdings</h3>
      <p class="meta"><strong>Snapshot</strong> · Stand: {{ asOfLabel }}</p>
    </header>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Name</th>
            <th>Gewicht</th>
            <th>Marktwert</th>
            <th>Unreal. P&amp;L</th>
            <th>Unreal. Rendite</th>
            <th>Sektor</th>
            <th>Land</th>
            <th>Datenstatus</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="sortedItems.length === 0">
            <td colspan="9" class="empty-row">Keine Holdings vorhanden.</td>
          </tr>
          <tr
            v-for="item in sortedItems"
            :key="`${item.portfolio_id}-${item.holding_id || item.symbol}`"
            :class="{ active: item.symbol && item.symbol === selectedSymbol }"
            @click="onSelect(item)"
          >
            <td>{{ formatNullableText(item.symbol) }}</td>
            <td>{{ holdingName(item) }}</td>
            <td>{{ formatPercent(item.weight) }}</td>
            <td>{{ formatMoney(item.market_value, currency) }}</td>
            <td :class="pnlClass(item.unrealized_pnl)">{{ formatSignedMoney(item.unrealized_pnl, currency) }}</td>
            <td :class="pnlClass(item.unrealized_return_pct)">{{ formatPercentValue(item.unrealized_return_pct) }}</td>
            <td>{{ formatNullableText(item.sector) }}</td>
            <td>{{ formatNullableText(item.country) }}</td>
            <td>
              <span class="status-badge" :class="statusClass(item.data_status)">{{ mapHoldingDataStatus(item.data_status) }}</span>
              <p v-if="hasWarnings(item.warnings)" class="warning-hint">{{ formatWarnings(item.warnings) }}</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PortfolioHoldingItem } from '@/shared/model/types'
import {
  formatDate,
  formatMoney,
  formatNullableText,
  formatPercent,
  formatPercentValue,
  formatSignedMoney,
  mapHoldingDataStatus,
  mapPortfolioWarning
} from '@/modules/dashboard/model/portfolioFormatting'

const props = defineProps<{
  items: PortfolioHoldingItem[]
  currency?: string
  selectedSymbol?: string | null
  asOf?: string | null
}>()
const emit = defineEmits<{
  (event: 'select-holding', item: PortfolioHoldingItem): void
}>()

const currency = computed(() => props.currency ?? 'EUR')
const asOfLabel = computed(() => formatDate(props.asOf))

const sortedItems = computed(() => [...props.items].sort((left, right) => right.weight - left.weight))

function holdingName(item: PortfolioHoldingItem) {
  return formatNullableText(item.display_name, '') || formatNullableText(item.portfolio_name)
}

function onSelect(item: PortfolioHoldingItem) {
  emit('select-holding', item)
}

function pnlClass(value: number | null | undefined) {
  if (value == null) return 'neutral'
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}

function statusClass(status: string | null | undefined) {
  if (status === 'ok') return 'ok'
  if (status === 'fallback_acquisition_price') return 'fallback'
  return 'warning'
}

function hasWarnings(warnings: string[] | null | undefined) {
  return Boolean(warnings?.some((warning) => warning.trim().length > 0))
}

function formatWarnings(warnings: string[] | null | undefined) {
  return (warnings ?? [])
    .filter((warning) => warning.trim().length > 0)
    .map((warning) => mapPortfolioWarning(warning))
    .join(', ')
}
</script>

<style scoped>
.panel {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.9rem;
  background: #fff;
}

.panel-header {
  margin: 0 0 0.6rem;
}

h3 {
  margin: 0;
}

.meta {
  margin: 0.22rem 0 0;
  color: #64748b;
  font-size: 0.8rem;
}

.table-wrap {
  overflow-y: auto;
  overflow-x: auto;
  max-height: 26rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 760px;
}

th,
td {
  text-align: left;
  font-size: 0.82rem;
  padding: 0.45rem;
  border-bottom: 1px solid #e2e8f0;
  white-space: nowrap;
}

tbody tr {
  cursor: pointer;
}

tbody tr:hover {
  background: #f8fafc;
}

tbody tr.active {
  background: #e0f2fe;
  box-shadow: inset 3px 0 0 #0284c7;
}

th {
  color: #475569;
  font-weight: 700;
  position: sticky;
  top: 0;
  z-index: 1;
  background: #fff;
}

.positive {
  color: #166534;
  font-weight: 600;
}

.negative {
  color: #b91c1c;
  font-weight: 600;
}

.neutral {
  color: #334155;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.1rem 0.4rem;
  border: 1px solid #cbd5e1;
  font-size: 0.72rem;
}

.status-badge.ok {
  background: #dcfce7;
  color: #166534;
  border-color: #86efac;
}

.status-badge.fallback {
  background: #ffedd5;
  color: #9a3412;
  border-color: #fdba74;
}

.status-badge.warning {
  background: #fef3c7;
  color: #92400e;
  border-color: #fcd34d;
}

.warning-hint {
  margin: 0.18rem 0 0;
  color: #92400e;
  font-size: 0.72rem;
}

.empty-row {
  text-align: center;
  color: #64748b;
  font-style: italic;
}
</style>
