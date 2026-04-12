<template>
  <section class="coverage" :class="`coverage--${coverageTone}`" data-test="coverage-banner">
    <header class="coverage-header">
      <div>
        <p class="title">
          <strong>{{ titleLabel }}</strong>
          <span>{{ holdingsLabel }}</span>
        </p>
        <p class="meta">
          <strong>Snapshot</strong>
          <span>Stand: {{ asOfLabel }}</span>
        </p>
      </div>
      <span class="status-pill" :class="`status-pill--${coverageTone}`" data-test="coverage-status">
        {{ statusLabel }}
      </span>
    </header>

    <div class="indicator-row" data-test="coverage-indicators">
      <span v-if="!hasQualitySignal" class="indicator indicator--ok">Keine Datenlücken</span>
      <span
        v-for="indicator in problemIndicators"
        :key="indicator.key"
        class="indicator"
        :class="`indicator--${indicator.tone}`"
        :data-indicator="indicator.key"
      >
        <strong>{{ indicator.value }}</strong> {{ indicator.label }}
      </span>
      <span v-if="warningCount > 0" class="indicator indicator--warning" data-test="coverage-warning-count">
        <strong>{{ warningCount }}</strong> Hinweise
      </span>
    </div>

    <p v-if="warningSummary" class="warnings" data-test="coverage-warning-summary">Hinweise: {{ warningSummary }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PortfolioDataCoverageReadModel } from '@/shared/model/types'
import { formatDate, getStringMeta, mapCoverageWarning } from '@/modules/dashboard/model/portfolioFormatting'

const props = defineProps<{
  coverage: PortfolioDataCoverageReadModel
}>()

type CoverageTone = 'ok' | 'warning' | 'critical'

interface CoverageIndicator {
  key: string
  label: string
  value: number
  tone: Exclude<CoverageTone, 'ok'>
}

const asOfLabel = computed(() => formatDate(getStringMeta(props.coverage.meta, 'as_of', 'generated_at', 'updated_at') ?? props.coverage.as_of))
const totalHoldings = computed(() => props.coverage.total_holdings ?? 0)
const missingPrices = computed(() => props.coverage.missing_prices ?? 0)
const missingSectors = computed(() => props.coverage.missing_sectors ?? 0)
const missingCountries = computed(() => props.coverage.missing_countries ?? 0)
const missingCurrencies = computed(() => props.coverage.missing_currencies ?? 0)
const fallbackPrices = computed(() => props.coverage.fallback_acquisition_prices ?? 0)
const marketdataWarnings = computed(() => props.coverage.holdings_with_marketdata_warnings ?? 0)
const warningCount = computed(() => (props.coverage.warnings ?? []).length)

const problemIndicators = computed<CoverageIndicator[]>(() => {
  const indicators: CoverageIndicator[] = [
    { key: 'missing-prices', label: 'Preise fehlen', value: missingPrices.value, tone: 'critical' },
    { key: 'missing-sectors', label: 'Sektoren fehlen', value: missingSectors.value, tone: 'warning' },
    { key: 'missing-countries', label: 'Länder fehlen', value: missingCountries.value, tone: 'warning' },
    { key: 'missing-currencies', label: 'Währungen fehlen', value: missingCurrencies.value, tone: 'warning' },
    { key: 'fallback-prices', label: 'Preis-Fallbacks', value: fallbackPrices.value, tone: 'warning' },
    { key: 'marketdata-warnings', label: 'Marketdata-Warnungen', value: marketdataWarnings.value, tone: 'warning' }
  ]

  return indicators.filter((indicator) => indicator.value > 0)
})

const issueCount = computed(() => problemIndicators.value.reduce((sum, indicator) => sum + indicator.value, 0))
const hasQualitySignal = computed(() => issueCount.value > 0 || warningCount.value > 0)
const coverageTone = computed<CoverageTone>(() => {
  if (missingPrices.value > 0) return 'critical'
  if (hasQualitySignal.value) return 'warning'
  return 'ok'
})

const titleLabel = computed(() => (hasQualitySignal.value ? 'Datenqualität prüfen' : 'Datenabdeckung ok'))
const holdingsLabel = computed(() => `${totalHoldings.value} ${totalHoldings.value === 1 ? 'Holding' : 'Holdings'}`)
const statusLabel = computed(() => {
  if (!hasQualitySignal.value) return 'OK'

  if (issueCount.value > 0) {
    return `${issueCount.value} ${issueCount.value === 1 ? 'Signal' : 'Signale'}`
  }

  return `${warningCount.value} ${warningCount.value === 1 ? 'Hinweis' : 'Hinweise'}`
})

const warningSummary = computed(() => {
  const warnings = props.coverage.warnings ?? []
  const visibleWarnings = warnings.slice(0, 3).map((warning) => mapCoverageWarning(warning))
  const remaining = warnings.length - visibleWarnings.length

  if (remaining > 0) {
    visibleWarnings.push(`+${remaining} weitere`)
  }

  return visibleWarnings.join(' · ')
})
</script>

<style scoped>
.coverage {
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  border-radius: 8px;
  padding: 0.55rem 0.65rem;
  display: grid;
  gap: 0.4rem;
}

.coverage--warning {
  border-color: #f59e0b;
  background: #fffbeb;
}

.coverage--critical {
  border-color: #f87171;
  background: #fff1f2;
}

.coverage-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
}

p {
  margin: 0;
  color: #334155;
  font-size: 0.82rem;
}

.title {
  font-size: 0.84rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.meta {
  color: #64748b;
  font-size: 0.76rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: 0.12rem;
}

.indicator-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.28rem;
}

.indicator,
.status-pill {
  border-radius: 6px;
  font-weight: 700;
  white-space: nowrap;
}

.status-pill {
  border: 1px solid #cbd5e1;
  padding: 0.12rem 0.38rem;
  background: #fff;
  color: #334155;
  font-size: 0.75rem;
}

.status-pill--ok {
  border-color: #bbf7d0;
  background: #f0fdf4;
  color: #166534;
}

.status-pill--warning,
.indicator--warning {
  border-color: #fde68a;
  background: #fef3c7;
  color: #92400e;
}

.status-pill--critical,
.indicator--critical {
  border-color: #fecaca;
  background: #fee2e2;
  color: #991b1b;
}

.indicator {
  border: 1px solid #cbd5e1;
  padding: 0.12rem 0.34rem;
  color: #475569;
  background: #fff;
  font-size: 0.74rem;
}

.indicator--ok {
  border-color: #bbf7d0;
  background: #f0fdf4;
  color: #166534;
}

.warnings {
  color: #92400e;
  font-size: 0.76rem;
  line-height: 1.3;
}
</style>
