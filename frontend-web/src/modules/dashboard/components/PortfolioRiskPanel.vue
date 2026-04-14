<template>
  <article class="panel">
    <header class="panel-heading">
      <div class="title-row">
        <h3>Portfolio Risk</h3>
        <span class="scope-badge">Zeitraum + Snapshot</span>
      </div>
      <p class="meta">
        <span>Stand: <strong>{{ asOfLabel }}</strong></span>
        <span>Zeitraum: <strong>{{ rangeLabel }}</strong></span>
        <span>Benchmark: <strong>{{ benchmarkSymbol }}</strong></span>
        <span v-if="methodologyLabel">Methodik: <strong>{{ methodologyLabel }}</strong></span>
      </p>
    </header>

    <div class="risk-board" data-testid="risk-metric-board">
      <section class="metric-block" data-testid="risk-block-core">
        <div class="block-heading">
          <h4>Kernrisiko</h4>
          <span>Primär</span>
        </div>

        <dl class="primary-grid" data-testid="risk-primary-grid">
          <div
            v-for="metric in primaryRiskMetrics"
            :key="metric.key"
            class="metric-card metric-card--primary"
            :class="{ 'is-missing': metric.isMissing }"
            :data-testid="`risk-primary-${metric.key}`"
          >
            <dt>{{ metric.label }}</dt>
            <dd>
              <strong class="metric-value metric-value--primary" :class="metric.tone">{{ metric.value }}</strong>
            </dd>
          </div>
        </dl>

        <dl v-if="coreSecondaryMetrics.length > 0" class="metric-strip" data-testid="risk-core-secondary">
          <div
            v-for="metric in coreSecondaryMetrics"
            :key="metric.key"
            class="metric-cell metric-cell--secondary"
            :data-testid="`risk-metric-${metric.key}`"
          >
            <dt>{{ metric.label }}</dt>
            <dd>
              <strong class="metric-value" :class="metric.tone">{{ metric.value }}</strong>
            </dd>
          </div>
        </dl>
      </section>

      <section class="metric-block" data-testid="risk-block-benchmark">
        <div class="block-heading">
          <h4>Benchmark-relativ</h4>
          <span>{{ benchmarkSymbol }}</span>
        </div>

        <dl v-if="benchmarkMetrics.length > 0" class="metric-grid metric-grid--dense">
          <div
            v-for="metric in benchmarkMetrics"
            :key="metric.key"
            class="metric-cell"
            :data-testid="`risk-metric-${metric.key}`"
          >
            <dt>{{ metric.label }}</dt>
            <dd>
              <strong class="metric-value" :class="metric.tone">{{ metric.value }}</strong>
            </dd>
          </div>
        </dl>
        <p v-else class="empty-state" data-testid="risk-benchmark-empty">Keine Benchmark-Daten verfügbar.</p>
      </section>

      <section class="metric-block" :class="{ 'metric-block--critical': isConcentrationCritical }" data-testid="risk-block-concentration">
        <div class="block-heading">
          <h4>Konzentration</h4>
          <span>Snapshot</span>
        </div>

        <dl class="metric-grid metric-grid--compact">
          <div
            v-for="metric in concentrationMetrics"
            :key="metric.key"
            class="metric-cell"
            :data-testid="`risk-metric-${metric.key}`"
          >
            <dt>{{ metric.label }}</dt>
            <dd>
              <strong class="metric-value" :class="metric.tone">{{ metric.value }}</strong>
            </dd>
          </div>
          <div class="metric-cell metric-cell--note" :class="concentrationTone" data-testid="risk-metric-concentration-note">
            <dt>Hinweis</dt>
            <dd>
              <strong class="metric-value" :class="concentrationTone">{{ concentrationNote }}</strong>
            </dd>
          </div>
        </dl>
      </section>

      <section v-if="behaviorMetrics.length > 0" class="metric-block" data-testid="risk-block-performance">
        <div class="block-heading">
          <h4>Performance-Verhalten</h4>
          <span>Tage</span>
        </div>

        <dl class="metric-grid metric-grid--compact">
          <div
            v-for="metric in behaviorMetrics"
            :key="metric.key"
            class="metric-cell"
            :data-testid="`risk-metric-${metric.key}`"
          >
            <dt>{{ metric.label }}</dt>
            <dd>
              <strong class="metric-value" :class="metric.tone">{{ metric.value }}</strong>
            </dd>
          </div>
        </dl>
      </section>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PortfolioRiskReadModel } from '@/shared/model/types'
import {
  formatDate,
  formatNullableText,
  formatNumber,
  formatPercent,
  formatRangeLabel,
  formatSignedPercentFromRatio,
  formatSignedPercentPoints,
  getStringMeta,
  mapConcentrationNote,
  mapPortfolioMethodology
} from '@/modules/dashboard/model/portfolioFormatting'

const props = defineProps<{
  risk: PortfolioRiskReadModel
}>()

type MetricTone = 'positive' | 'negative' | 'neutral'

interface RiskMetric {
  key: string
  label: string
  value: string
  tone: MetricTone
  isMissing?: boolean
}

const criticalConcentrationNotes = new Set(['single_position_dominates', 'very_high_top3_concentration'])

function hasMetricValue(value: number | null | undefined): value is number {
  return value != null && !Number.isNaN(value)
}

function signedTone(value: number | null | undefined): MetricTone {
  if (!hasMetricValue(value) || value === 0) {
    return 'neutral'
  }
  return value > 0 ? 'positive' : 'negative'
}

function displayMetric(
  key: string,
  label: string,
  value: number | null | undefined,
  formatter: (value: number | null | undefined) => string,
  tone: MetricTone = 'neutral'
): RiskMetric {
  const isMissing = !hasMetricValue(value)
  return {
    key,
    label,
    value: formatter(value),
    tone: isMissing ? 'neutral' : tone,
    isMissing
  }
}

function optionalMetric(
  key: string,
  label: string,
  value: number | null | undefined,
  formatter: (value: number) => string,
  tone: MetricTone = 'neutral'
): RiskMetric | null {
  if (!hasMetricValue(value)) {
    return null
  }
  return { key, label, value: formatter(value), tone }
}

function formatRatioPercent(value: number): string {
  return formatPercent(value)
}

function formatSignedRatioPercentPoints(value: number): string {
  return formatSignedPercentPoints(value * 100)
}

function presentMetrics(metrics: Array<RiskMetric | null>): RiskMetric[] {
  return metrics.filter((metric): metric is RiskMetric => metric != null)
}

const asOfLabel = computed(() => formatDate(getStringMeta(props.risk.meta, 'as_of', 'generated_at', 'updated_at') ?? props.risk.as_of))
const rangeLabel = computed(() =>
  formatRangeLabel(props.risk.range ?? getStringMeta(props.risk.meta, 'range'), props.risk.range_label ?? getStringMeta(props.risk.meta, 'range_label'))
)
const benchmarkSymbol = computed(() => formatNullableText(props.risk.benchmark_symbol))
const methodologyLabel = computed(() => {
  const parts = [props.risk.methodology, props.risk.benchmark_relation].filter(
    (part): part is string => typeof part === 'string' && part.trim().length > 0
  )
  return parts.map((part) => mapPortfolioMethodology(part)).join(' · ')
})

const primaryRiskMetrics = computed<RiskMetric[]>(() => [
  displayMetric('annualized-volatility', 'Ann. Volatilität', props.risk.annualized_volatility, formatPercent),
  displayMetric('max-drawdown', 'Max Drawdown', props.risk.max_drawdown, formatSignedPercentFromRatio, signedTone(props.risk.max_drawdown)),
  displayMetric('sharpe-ratio', 'Sharpe', props.risk.sharpe_ratio, (value) => formatNumber(value, 2), signedTone(props.risk.sharpe_ratio)),
  displayMetric('sortino-ratio', 'Sortino', props.risk.sortino_ratio, (value) => formatNumber(value, 2), signedTone(props.risk.sortino_ratio))
])

const coreSecondaryMetrics = computed(() =>
  presentMetrics([
    optionalMetric('portfolio-volatility', 'Tagesvolatilität', props.risk.portfolio_volatility, formatRatioPercent)
  ])
)

const benchmarkMetrics = computed(() =>
  presentMetrics([
    optionalMetric('annualized-tracking-error', 'Ann. Tracking Error', props.risk.annualized_tracking_error, formatRatioPercent),
    optionalMetric('information-ratio', 'Information Ratio', props.risk.information_ratio, (value) => formatNumber(value, 2), signedTone(props.risk.information_ratio)),
    optionalMetric('active-return', 'Active Return', props.risk.active_return, formatSignedRatioPercentPoints, signedTone(props.risk.active_return)),
    optionalMetric('beta', 'Beta', props.risk.beta, (value) => formatNumber(value, 2)),
    optionalMetric('correlation', 'Korrelation', props.risk.correlation, (value) => formatNumber(value, 2)),
    optionalMetric('tracking-error', 'Tracking Error', props.risk.tracking_error, formatRatioPercent),
    optionalMetric('aligned-points', 'Aligned Points', props.risk.aligned_points, (value) => formatNumber(value, 0))
  ])
)

const concentrationMetrics = computed(() =>
  presentMetrics([
    optionalMetric('top-position-weight', 'Top-Position', props.risk.top_position_weight, formatRatioPercent),
    optionalMetric('top3-weight', 'Top 3', props.risk.top3_weight, formatRatioPercent)
  ])
)

const behaviorMetrics = computed(() =>
  presentMetrics([
    optionalMetric('best-day-return', 'Bester Tag', props.risk.best_day_return, formatSignedPercentFromRatio, signedTone(props.risk.best_day_return)),
    optionalMetric('worst-day-return', 'Schlechtester Tag', props.risk.worst_day_return, formatSignedPercentFromRatio, signedTone(props.risk.worst_day_return))
  ])
)

const rawConcentrationNote = computed(() => {
  if (typeof props.risk.concentration_note !== 'string') {
    return null
  }
  const normalized = props.risk.concentration_note.trim()
  return normalized.length > 0 ? normalized : null
})

const isConcentrationCritical = computed(() => rawConcentrationNote.value != null && criticalConcentrationNotes.has(rawConcentrationNote.value))
const concentrationTone = computed<MetricTone>(() => (isConcentrationCritical.value ? 'negative' : 'neutral'))

const concentrationNote = computed(() => mapConcentrationNote(rawConcentrationNote.value))
</script>

<style scoped>
.panel {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem;
  background: #fff;
}

h3 {
  margin: 0;
}

.panel-heading {
  display: grid;
  gap: 0.24rem;
  margin-bottom: 0.6rem;
}

.title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}

.scope-badge {
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  padding: 0.08rem 0.4rem;
  color: #475569;
  font-size: 0.72rem;
  font-weight: 700;
  line-height: 1.25;
}

.meta {
  margin: 0;
  color: #64748b;
  font-size: 0.8rem;
  line-height: 1.35;
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem 0.5rem;
}

.meta strong {
  color: #334155;
}

.risk-board {
  display: grid;
  gap: 0.62rem;
}

.metric-block {
  min-width: 0;
  border-top: 1px solid #e2e8f0;
  padding-top: 0.56rem;
}

.metric-block:first-child {
  border-top: 0;
  padding-top: 0;
}

.metric-block--critical {
  border-top-color: #fecaca;
}

.block-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.55rem;
  margin-bottom: 0.35rem;
}

h4 {
  margin: 0;
  color: #475569;
  font-size: 0.76rem;
  line-height: 1.2;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.block-heading span {
  min-width: 0;
  color: #64748b;
  font-size: 0.72rem;
  font-weight: 700;
  line-height: 1.2;
  text-align: right;
  overflow-wrap: anywhere;
}

.primary-grid,
.metric-grid,
.metric-strip {
  display: grid;
  padding: 0;
  margin: 0;
}

.primary-grid {
  grid-template-columns: repeat(auto-fit, minmax(104px, 1fr));
  gap: 0.36rem;
}

.metric-grid {
  grid-template-columns: repeat(auto-fit, minmax(116px, 1fr));
  gap: 0.34rem;
}

.metric-grid--dense {
  grid-template-columns: repeat(auto-fit, minmax(108px, 1fr));
}

.metric-grid--compact {
  grid-template-columns: repeat(auto-fit, minmax(118px, 1fr));
}

.metric-strip {
  grid-template-columns: repeat(auto-fit, minmax(118px, 1fr));
  gap: 0.34rem;
  margin-top: 0.38rem;
}

.metric-card,
.metric-cell {
  min-width: 0;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
}

.metric-card--primary {
  min-height: 4.6rem;
  padding: 0.54rem 0.58rem;
  display: grid;
  align-content: space-between;
  gap: 0.4rem;
}

.metric-cell {
  min-height: 3.55rem;
  padding: 0.4rem 0.48rem;
  display: grid;
  align-content: start;
  gap: 0.16rem;
}

.metric-cell--secondary,
.metric-cell--note {
  background: #f8fafc;
}

.metric-cell--note {
  grid-column: span 2;
}

.metric-cell--note.negative {
  border-color: #fecaca;
  background: #fff5f5;
}

dt {
  min-width: 0;
  color: #64748b;
  font-size: 0.72rem;
  font-weight: 700;
  line-height: 1.2;
  overflow-wrap: anywhere;
  hyphens: auto;
}

dd {
  min-width: 0;
  margin: 0;
}

.metric-value {
  display: block;
  color: #0f172a;
  font-size: 0.92rem;
  font-weight: 700;
  line-height: 1.12;
  overflow-wrap: anywhere;
}

.metric-value--primary {
  font-size: 1.12rem;
  line-height: 1.05;
}

.metric-value.positive {
  color: #166534;
}

.metric-value.negative {
  color: #b91c1c;
}

.metric-value.neutral {
  color: #0f172a;
}

.is-missing {
  border-style: dashed;
  background: #f8fafc;
}

.is-missing .metric-value {
  color: #64748b;
  font-weight: 700;
}

.empty-state {
  margin: 0;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  padding: 0.45rem 0.5rem;
  color: #64748b;
  font-size: 0.82rem;
  line-height: 1.3;
  background: #f8fafc;
}

@media (max-width: 520px) {
  .primary-grid,
  .metric-grid,
  .metric-strip {
    grid-template-columns: 1fr;
  }

  .metric-cell--note {
    grid-column: auto;
  }
}
</style>
