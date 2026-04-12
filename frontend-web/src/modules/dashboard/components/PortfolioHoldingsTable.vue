<template>
  <article class="panel">
    <header class="panel-header">
      <h3>Holdings</h3>
      <p class="meta"><strong>Snapshot</strong> · Stand: {{ asOfLabel }}</p>
    </header>
    <div class="table-wrap" :class="{ 'table-wrap--no-scroll': useCompactLayout }" data-test="holdings-table-wrap">
      <table class="holdings-table" :class="{ 'holdings-table--compact': useCompactLayout }">
        <colgroup>
          <col class="col-symbol" />
          <col class="col-name" />
          <col class="col-weight" />
          <col class="col-market-value" />
          <col class="col-pnl" />
          <col class="col-return" />
          <col class="col-sector" />
          <col class="col-country" />
          <col class="col-status" />
        </colgroup>
        <thead>
          <tr>
            <th scope="col" class="cell-symbol">Symbol</th>
            <th scope="col" class="cell-name">Name</th>
            <th scope="col" class="cell-number">Gewicht</th>
            <th scope="col" class="cell-number">Marktwert</th>
            <th scope="col" class="cell-number" title="Unrealisierter Gewinn/Verlust">P&amp;L</th>
            <th scope="col" class="cell-number" title="Unrealisierte Rendite">Rendite</th>
            <th scope="col" class="cell-sector">Sektor</th>
            <th scope="col" class="cell-country">Land</th>
            <th scope="col" class="cell-status" title="Datenstatus">Status</th>
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
            <td class="cell-symbol text-truncate" :title="formatNullableText(item.symbol)">
              {{ formatNullableText(item.symbol) }}
            </td>
            <td class="cell-name text-truncate" :title="holdingName(item)">
              {{ holdingName(item) }}
            </td>
            <td class="cell-number">{{ formatPercent(item.weight) }}</td>
            <td class="cell-number">{{ formatMoney(item.market_value, currency) }}</td>
            <td class="cell-number" :class="pnlClass(item.unrealized_pnl)">
              {{ formatSignedMoney(item.unrealized_pnl, currency) }}
            </td>
            <td class="cell-number" :class="pnlClass(item.unrealized_return_pct)">
              {{ formatPercentValue(item.unrealized_return_pct) }}
            </td>
            <td class="cell-sector text-truncate" :title="formatNullableText(item.sector)">
              {{ formatNullableText(item.sector) }}
            </td>
            <td class="cell-country text-truncate" :title="formatNullableText(item.country)">
              {{ formatNullableText(item.country) }}
            </td>
            <td class="cell-status">
              <span class="status-badge" :class="statusClass(item.data_status)" :title="mapHoldingDataStatus(item.data_status)">
                {{ mapHoldingDataStatus(item.data_status) }}
              </span>
              <p v-if="hasWarnings(item.warnings)" class="warning-hint" :title="formatWarnings(item.warnings)">
                {{ formatWarnings(item.warnings) }}
              </p>
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
const useCompactLayout = computed(() => sortedItems.value.length <= 3)

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

.table-wrap--no-scroll {
  overflow-x: hidden;
}

.holdings-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.col-symbol {
  width: 8%;
}

.col-name {
  width: auto;
}

.col-weight {
  width: 8%;
}

.col-market-value,
.col-pnl {
  width: 10%;
}

.col-return {
  width: 9%;
}

.col-sector {
  width: 11%;
}

.col-country {
  width: 6%;
}

.col-status {
  width: 12%;
}

.holdings-table--compact .col-symbol {
  width: 7%;
}

.holdings-table--compact .col-weight {
  width: 7%;
}

.holdings-table--compact .col-market-value,
.holdings-table--compact .col-pnl {
  width: 9%;
}

.holdings-table--compact .col-return {
  width: 8%;
}

.holdings-table--compact .col-sector {
  width: 10%;
}

.holdings-table--compact .col-country {
  width: 6%;
}

.holdings-table--compact .col-status {
  width: 14%;
}

th,
td {
  text-align: left;
  font-size: 0.8rem;
  padding: 0.42rem 0.36rem;
  border-bottom: 1px solid #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: middle;
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

.cell-number {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  max-width: 100%;
  border-radius: 999px;
  padding: 0.1rem 0.4rem;
  border: 1px solid #cbd5e1;
  font-size: 0.72rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-row {
  text-align: center;
  color: #64748b;
  font-style: italic;
}

@media (max-width: 760px) {
  .table-wrap--no-scroll {
    overflow-x: auto;
  }

  .holdings-table {
    min-width: 46rem;
  }
}
</style>
