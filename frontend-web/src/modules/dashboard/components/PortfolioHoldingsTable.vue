<template>
  <article class="panel">
    <header class="panel-header">
      <h3>Holdings</h3>
      <p class="meta"><strong>Snapshot</strong> · Stand: {{ asOfLabel }}</p>
    </header>
    <div class="table-wrap" :class="{ 'table-wrap--small': useSmallTableState }" data-test="holdings-table-wrap">
      <table class="holdings-table" :class="{ 'holdings-table--small': useSmallTableState }">
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
          <tr v-if="rows.length === 0" class="empty-state-row">
            <td colspan="9" class="empty-row">Keine Holdings vorhanden.</td>
          </tr>
          <tr
            v-for="row in rows"
            :key="row.key"
            :class="{ active: row.item.symbol && row.item.symbol === selectedSymbol }"
            @click="onSelect(row.item)"
          >
            <td class="cell-symbol text-truncate" :title="row.symbolLabel">
              {{ row.symbolLabel }}
            </td>
            <td class="cell-name text-truncate" :title="row.nameLabel">
              {{ row.nameLabel }}
            </td>
            <td class="cell-number" :title="row.weightLabel">{{ row.weightLabel }}</td>
            <td class="cell-number" :title="row.marketValueLabel">{{ row.marketValueLabel }}</td>
            <td class="cell-number" :class="pnlClass(row.item.unrealized_pnl)" :title="row.pnlLabel">
              {{ row.pnlLabel }}
            </td>
            <td class="cell-number" :class="pnlClass(row.item.unrealized_return_pct)" :title="row.returnLabel">
              {{ row.returnLabel }}
            </td>
            <td class="cell-sector text-truncate" :title="row.sectorLabel">
              {{ row.sectorLabel }}
            </td>
            <td class="cell-country text-truncate" :title="row.countryLabel">
              {{ row.countryLabel }}
            </td>
            <td class="cell-status" :title="row.statusTitle">
              <div class="status-stack" :aria-label="row.statusTitle">
                <span
                  class="status-badge"
                  :class="statusClass(row.item.data_status)"
                  :title="row.statusLabel"
                  data-test="status-badge"
                >
                  {{ row.statusLabel }}
                </span>
                <div
                  v-if="row.warningLabels.length > 0"
                  class="warning-summary"
                  :title="row.warningTitle"
                  data-test="warning-summary"
                >
                  <span class="warning-text">{{ row.primaryWarningLabel }}</span>
                  <span
                    v-if="row.hiddenWarningCount > 0"
                    class="warning-count"
                    :aria-label="`${row.hiddenWarningCount} weitere Warnungen: ${row.hiddenWarningsLabel}`"
                  >
                    +{{ row.hiddenWarningCount }}
                  </span>
                </div>
              </div>
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
const useSmallTableState = computed(() => sortedItems.value.length <= 3)

const rows = computed(() =>
  sortedItems.value.map((item) => {
    const warningLabels = warningDisplayLabels(item.warnings)
    const hiddenWarnings = warningLabels.slice(1)
    const statusLabel = mapHoldingDataStatus(item.data_status)
    const warningTitle = warningLabels.join(', ')

    return {
      item,
      key: `${item.portfolio_id}-${item.holding_id || item.symbol}`,
      symbolLabel: formatNullableText(item.symbol),
      nameLabel: holdingName(item),
      weightLabel: formatPercent(item.weight),
      marketValueLabel: formatMoney(item.market_value, currency.value),
      pnlLabel: formatSignedMoney(item.unrealized_pnl, currency.value),
      returnLabel: formatPercentValue(item.unrealized_return_pct),
      sectorLabel: formatNullableText(item.sector),
      countryLabel: formatNullableText(item.country),
      statusLabel,
      warningLabels,
      primaryWarningLabel: warningLabels[0] ?? '',
      warningTitle,
      statusTitle: warningTitle ? `${statusLabel}: ${warningTitle}` : statusLabel,
      hiddenWarningCount: hiddenWarnings.length,
      hiddenWarningsLabel: hiddenWarnings.join(', ')
    }
  })
)

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

function warningDisplayLabels(warnings: string[] | null | undefined) {
  return (warnings ?? [])
    .filter((warning) => warning.trim().length > 0)
    .map((warning) => mapPortfolioWarning(warning))
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
  scrollbar-gutter: stable;
}

.table-wrap--small {
  overflow-x: hidden;
}

.holdings-table {
  width: 100%;
  min-width: 82rem;
  border-collapse: collapse;
  table-layout: fixed;
}

.col-symbol {
  width: 7rem;
}

.col-name {
  width: auto;
}

.col-weight {
  width: 7.25rem;
}

.col-market-value {
  width: 9.75rem;
}

.col-pnl {
  width: 9.25rem;
}

.col-return {
  width: 8rem;
}

.col-sector {
  width: 10rem;
}

.col-country {
  width: 6.5rem;
}

.col-status {
  width: 14rem;
}

.holdings-table--small {
  min-width: 0;
}

.holdings-table--small .col-symbol {
  width: 8.5%;
}

.holdings-table--small .col-name {
  width: auto;
}

.holdings-table--small .col-weight {
  width: 8.5%;
}

.holdings-table--small .col-market-value {
  width: 11.5%;
}

.holdings-table--small .col-pnl {
  width: 10.5%;
}

.holdings-table--small .col-return {
  width: 9%;
}

.holdings-table--small .col-sector {
  width: 10.5%;
}

.holdings-table--small .col-country {
  width: 6.5%;
}

.holdings-table--small .col-status {
  width: 15.5%;
}

th,
td {
  text-align: left;
  font-size: 0.8rem;
  padding: 0.52rem 0.65rem;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: middle;
}

td {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

tbody tr:not(.empty-state-row) {
  cursor: pointer;
}

tbody tr:not(.empty-state-row):hover {
  background: #f8fafc;
}

tbody tr.active {
  background: #e0f2fe;
  box-shadow: inset 3px 0 0 #0284c7;
}

th {
  color: #475569;
  font-weight: 700;
  line-height: 1.15;
  white-space: normal;
  word-break: normal;
  overflow: visible;
  text-overflow: clip;
  position: sticky;
  top: 0;
  z-index: 1;
  background: #fff;
}

.cell-number {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.cell-symbol {
  color: #0f172a;
  font-weight: 700;
  letter-spacing: 0;
}

.cell-status {
  white-space: normal;
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
  justify-content: center;
  max-width: 100%;
  border-radius: 8px;
  padding: 0.16rem 0.52rem;
  border: 1px solid #cbd5e1;
  font-size: 0.74rem;
  line-height: 1.2;
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

.status-stack {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.24rem;
  min-width: 0;
  max-width: 100%;
}

.warning-summary {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  min-width: 0;
  max-width: 100%;
}

.warning-text {
  min-width: 0;
  color: #92400e;
  font-size: 0.73rem;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.warning-count {
  flex: 0 0 auto;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 0 0.32rem;
  background: #fef3c7;
  color: #92400e;
  font-size: 0.68rem;
  line-height: 1.15rem;
  font-variant-numeric: tabular-nums;
}

.empty-row {
  text-align: center;
  color: #64748b;
  font-style: italic;
}

@media (max-width: 760px) {
  .table-wrap--small {
    overflow-x: auto;
  }

  .holdings-table {
    min-width: 64rem;
  }

  .holdings-table--small {
    min-width: 48rem;
  }

  th,
  td {
    padding: 0.42rem 0.45rem;
  }
}
</style>
