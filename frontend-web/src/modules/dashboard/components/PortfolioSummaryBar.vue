<template>
  <section class="summary-section">
    <p class="summary-meta">
      <strong>Snapshot</strong>
      <span>Stand: {{ asOfLabel }}</span>
      <span v-if="returnBasisLabel">Methodik: {{ returnBasisLabel }}</span>
      <span class="health-pill" :class="`health-pill--${concentrationHealth.tone}`" data-test="summary-concentration-health">
        {{ concentrationHealth.label }}
      </span>
    </p>
    <div class="summary-grid" data-test="summary-grid">
      <article
        class="summary-card"
        v-for="item in kpis"
        :key="item.key"
        :class="[`summary-card--${item.tone}`, `summary-card--${item.layout}`]"
        :data-kpi="item.key"
        :data-layout-priority="item.priority"
        data-test="summary-kpi"
      >
        <p class="label">
          <span class="label-text">{{ item.label }}</span>
          <span v-if="item.signalLabel" class="signal" :class="`signal--${item.tone}`">{{ item.signalLabel }}</span>
        </p>
        <p class="value">{{ item.value }}</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PortfolioSummaryReadModel } from '@/shared/model/types'
import {
  formatMoney,
  formatNumber,
  formatPercent,
  formatPercentValue,
  formatSignedMoney,
  formatDate,
  mapPortfolioMethodology
} from '@/modules/dashboard/model/portfolioFormatting'

const props = defineProps<{
  summary: PortfolioSummaryReadModel
}>()

type HealthTone = 'ok' | 'warning' | 'critical' | 'unknown'
type KpiTone = 'neutral' | 'positive' | 'negative' | 'warning' | 'critical'
type KpiLayout = 'core' | 'count' | 'concentration'

interface KpiItem {
  key: string
  priority: number
  layout: KpiLayout
  label: string
  value: string
  tone: KpiTone
  signalLabel?: string
}

function hasNumber(value: number | null | undefined): value is number {
  return value != null && !Number.isNaN(value)
}

function trendTone(value: number | null | undefined): KpiTone {
  if (!hasNumber(value) || value === 0) return 'neutral'
  return value > 0 ? 'positive' : 'negative'
}

function concentrationTone(value: number | null | undefined, warningAt: number, criticalAt: number): HealthTone {
  if (!hasNumber(value)) return 'unknown'
  if (value >= criticalAt) return 'critical'
  if (value >= warningAt) return 'warning'
  return 'ok'
}

function kpiToneFromHealth(tone: HealthTone): KpiTone {
  if (tone === 'critical' || tone === 'warning') return tone
  return 'neutral'
}

function signalLabel(tone: HealthTone): string {
  if (tone === 'critical') return 'kritisch'
  if (tone === 'warning') return 'erhöht'
  return ''
}

const topPositionTone = computed(() => concentrationTone(props.summary.top_position_weight, 0.35, 0.5))
const top3Tone = computed(() => concentrationTone(props.summary.top3_weight, 0.65, 0.8))

const concentrationHealth = computed<{ tone: HealthTone; label: string }>(() => {
  if (topPositionTone.value === 'critical' || top3Tone.value === 'critical') {
    return { tone: 'critical', label: 'Konzentration kritisch' }
  }

  if (topPositionTone.value === 'warning' || top3Tone.value === 'warning') {
    return { tone: 'warning', label: 'Konzentration erhöht' }
  }

  if (topPositionTone.value === 'unknown' && top3Tone.value === 'unknown') {
    return { tone: 'unknown', label: 'Konzentration n/a' }
  }

  return { tone: 'ok', label: 'Konzentration ok' }
})

const kpis = computed(() => {
  const currency = props.summary.currency || 'EUR'
  return [
    {
      key: 'market-value',
      priority: 1,
      layout: 'core',
      label: 'Marktwert',
      value: formatMoney(props.summary.market_value, currency),
      tone: 'neutral'
    },
    {
      key: 'invested-value',
      priority: 2,
      layout: 'core',
      label: 'Investierter Wert',
      value: formatMoney(props.summary.invested_value, currency),
      tone: 'neutral'
    },
    {
      key: 'unrealized-pnl',
      priority: 3,
      layout: 'core',
      label: 'Unreal. P&L',
      value: formatSignedMoney(props.summary.unrealized_pnl, currency),
      tone: trendTone(props.summary.unrealized_pnl)
    },
    {
      key: 'unrealized-return',
      priority: 4,
      layout: 'core',
      label: 'Unreal. Rendite',
      value: formatPercentValue(props.summary.unrealized_return_pct),
      tone: trendTone(props.summary.unrealized_return_pct)
    },
    {
      key: 'holdings',
      priority: 5,
      layout: 'count',
      label: 'Holdings',
      value: formatNumber(props.summary.holdings_count, 0),
      tone: 'neutral'
    },
    {
      key: 'portfolios',
      priority: 6,
      layout: 'count',
      label: 'Portfolios',
      value: formatNumber(props.summary.portfolios_count, 0),
      tone: 'neutral'
    },
    {
      key: 'top-position',
      priority: 7,
      layout: 'concentration',
      label: 'Top Position',
      value: formatPercent(props.summary.top_position_weight),
      tone: kpiToneFromHealth(topPositionTone.value),
      signalLabel: signalLabel(topPositionTone.value)
    },
    {
      key: 'top3-concentration',
      priority: 8,
      layout: 'concentration',
      label: 'Top 3 Konzentration',
      value: formatPercent(props.summary.top3_weight),
      tone: kpiToneFromHealth(top3Tone.value),
      signalLabel: signalLabel(top3Tone.value)
    }
  ] satisfies KpiItem[]
})

const asOfLabel = computed(() => formatDate(props.summary.as_of))
const returnBasisLabel = computed(() => (props.summary.return_basis ? mapPortfolioMethodology(props.summary.return_basis) : ''))
</script>

<style scoped>
.summary-section {
  display: grid;
  gap: 0.35rem;
}

.summary-meta {
  margin: 0;
  color: #64748b;
  font-size: 0.8rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  align-items: center;
}

.summary-meta strong {
  color: #334155;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 0.55rem;
  grid-auto-flow: row;
}

.summary-card {
  min-width: 0;
  min-height: 4.6rem;
  grid-column: span 2;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.5rem 0.6rem;
  background: #fff;
  display: grid;
  grid-template-rows: auto 1fr;
  align-content: start;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.summary-card--positive .value {
  color: #047857;
}

.summary-card--negative .value {
  color: #b91c1c;
}

.summary-card--warning {
  border-color: #f59e0b;
  background: #fffbeb;
  box-shadow: inset 0 0 0 1px rgba(245, 158, 11, 0.18), 0 1px 2px rgba(146, 64, 14, 0.06);
}

.summary-card--critical {
  border-color: #f87171;
  background: #fff1f2;
  box-shadow: inset 0 0 0 1px rgba(248, 113, 113, 0.22), 0 1px 2px rgba(153, 27, 27, 0.08);
}

.summary-card--concentration.summary-card--warning .value {
  color: #92400e;
}

.summary-card--concentration.summary-card--critical .value {
  color: #991b1b;
}

.label {
  margin: 0;
  font-size: 0.74rem;
  color: #64748b;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.35rem;
  min-height: 1.1rem;
}

.label-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.value {
  margin: 0.22rem 0 0;
  font-size: 1.02rem;
  font-weight: 700;
  color: #0f172a;
  overflow-wrap: anywhere;
  font-variant-numeric: tabular-nums;
}

.signal,
.health-pill {
  border-radius: 6px;
  font-weight: 700;
  white-space: nowrap;
}

.signal {
  padding: 0.06rem 0.28rem;
  background: #fef3c7;
  color: #92400e;
  font-size: 0.68rem;
  justify-self: end;
  line-height: 1.05;
}

.signal--critical {
  background: #fee2e2;
  color: #991b1b;
}

.health-pill {
  padding: 0.1rem 0.35rem;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #334155;
}

.health-pill--ok {
  border-color: #bbf7d0;
  background: #f0fdf4;
  color: #166534;
}

.health-pill--warning {
  border-color: #fde68a;
  background: #fffbeb;
  color: #92400e;
}

.health-pill--critical {
  border-color: #fecaca;
  background: #fff1f2;
  color: #991b1b;
}

.health-pill--unknown {
  color: #64748b;
}

/* Grid contract: wide 6/2, desktop 4/4, tablet pairs, phone single column. */
@media (min-width: 1180px) {
  .summary-grid {
    grid-template-columns: repeat(12, minmax(0, 1fr));
  }

  .summary-card {
    grid-column: span 2;
  }

  .summary-card--concentration {
    grid-column: span 6;
  }
}

@media (max-width: 820px) {
  .summary-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 540px) {
  .summary-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .summary-card {
    grid-column: 1 / -1;
  }
}
</style>
