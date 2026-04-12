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

    <section class="group primary-group">
      <h4>Kernrisiko <span>primär</span></h4>
      <div class="primary-grid">
        <div
          v-for="metric in primaryRiskMetrics"
          :key="metric.key"
          class="primary-metric"
          :data-testid="`risk-primary-${metric.key}`"
        >
          <span>{{ metric.label }}</span>
          <strong :class="metric.tone">{{ metric.value }}</strong>
        </div>
      </div>
      <ul v-if="coreSecondaryMetrics.length > 0" class="metric-list compact-list">
        <li v-for="metric in coreSecondaryMetrics" :key="metric.key" :data-testid="`risk-metric-${metric.key}`">
          <span>{{ metric.label }}</span>
          <strong :class="metric.tone">{{ metric.value }}</strong>
        </li>
      </ul>
    </section>

    <section class="group">
      <h4>Benchmark-relativ <span>{{ benchmarkSymbol }}</span></h4>
      <ul v-if="benchmarkMetrics.length > 0" class="metric-list">
        <li v-for="metric in benchmarkMetrics" :key="metric.key" :data-testid="`risk-metric-${metric.key}`">
          <span>{{ metric.label }}</span>
          <strong :class="metric.tone">{{ metric.value }}</strong>
        </li>
      </ul>
      <p v-else class="empty-line" data-testid="risk-benchmark-empty">Keine Benchmark-Daten verfügbar.</p>
    </section>

    <section class="group">
      <h4>Konzentration <span>Snapshot</span></h4>
      <ul class="metric-list">
        <li v-for="metric in concentrationMetrics" :key="metric.key" :data-testid="`risk-metric-${metric.key}`">
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
        </li>
        <li data-testid="risk-metric-concentration-note">
          <span>Hinweis</span>
          <strong>{{ concentrationNote }}</strong>
        </li>
      </ul>
    </section>

    <section v-if="behaviorMetrics.length > 0" class="group">
      <h4>Performance-Verhalten <span>Tage</span></h4>
      <ul class="metric-list">
        <li v-for="metric in behaviorMetrics" :key="metric.key" :data-testid="`risk-metric-${metric.key}`">
          <span>{{ metric.label }}</span>
          <strong :class="metric.tone">{{ metric.value }}</strong>
        </li>
      </ul>
    </section>
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
  tone?: MetricTone
}

function hasMetricValue(value: number | null | undefined): value is number {
  return value != null && !Number.isNaN(value)
}

function signedTone(value: number | null | undefined): MetricTone {
  if (!hasMetricValue(value) || value === 0) {
    return 'neutral'
  }
  return value > 0 ? 'positive' : 'negative'
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
  {
    key: 'annualized-volatility',
    label: 'Ann. Volatilität',
    value: formatPercent(props.risk.annualized_volatility),
    tone: 'neutral'
  },
  {
    key: 'max-drawdown',
    label: 'Max Drawdown',
    value: formatSignedPercentFromRatio(props.risk.max_drawdown),
    tone: signedTone(props.risk.max_drawdown)
  },
  {
    key: 'sharpe-ratio',
    label: 'Sharpe',
    value: formatNumber(props.risk.sharpe_ratio, 2),
    tone: signedTone(props.risk.sharpe_ratio)
  },
  {
    key: 'sortino-ratio',
    label: 'Sortino',
    value: formatNumber(props.risk.sortino_ratio, 2),
    tone: signedTone(props.risk.sortino_ratio)
  }
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

const concentrationNote = computed(() => {
  if (!props.risk.concentration_note || props.risk.concentration_note.trim().length === 0) {
    return 'n/a'
  }
  return mapConcentrationNote(props.risk.concentration_note)
})
</script>

<style scoped>
.panel {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.72rem;
  background: #fff;
}

h3 {
  margin: 0;
}

.panel-heading {
  margin-bottom: 0.45rem;
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
}

.meta {
  margin: 0.22rem 0 0;
  color: #64748b;
  font-size: 0.8rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.42rem;
}

.meta strong {
  color: #334155;
}

.group + .group {
  margin-top: 0.5rem;
}

h4 {
  margin: 0 0 0.24rem;
  font-size: 0.79rem;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

h4 span {
  margin-left: 0.25rem;
  color: #64748b;
  font-size: 0.72rem;
  letter-spacing: 0;
  text-transform: none;
}

.primary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.35rem 0.65rem;
}

.primary-metric {
  min-width: 0;
}

.primary-metric span {
  display: block;
  color: #64748b;
  font-size: 0.73rem;
  line-height: 1.2;
}

.primary-metric strong {
  display: block;
  margin-top: 0.08rem;
  color: #0f172a;
  font-size: 1rem;
  line-height: 1.18;
}

.metric-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.24rem 0.8rem;
}

.compact-list {
  margin-top: 0.34rem;
}

.metric-list li {
  min-width: 0;
  display: flex;
  justify-content: space-between;
  gap: 0.65rem;
  font-size: 0.84rem;
  line-height: 1.25;
}

.metric-list span {
  min-width: 0;
  color: #64748b;
}

strong {
  color: #0f172a;
  white-space: nowrap;
}

strong.positive {
  color: #166534;
}

strong.negative {
  color: #b91c1c;
}

strong.neutral {
  color: #0f172a;
}

.empty-line {
  margin: 0;
  color: #64748b;
  font-size: 0.84rem;
}

@media (max-width: 720px) {
  .primary-grid,
  .metric-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .metric-list {
    grid-template-columns: 1fr;
  }
}
</style>
