<template>
  <section class="alerts-panel" :class="{ 'alerts-panel--empty': alerts.length === 0 }" data-test="portfolio-alerts-panel">
    <header class="alerts-header">
      <div>
        <p class="eyebrow">Alerts / Board</p>
        <h3>Handlungsbedarf</h3>
      </div>
      <span class="alert-count" :class="{ 'alert-count--empty': alerts.length === 0 }" data-test="portfolio-alert-count">
        {{ countLabel }}
      </span>
    </header>

    <div v-if="alerts.length > 0" class="source-board" data-test="portfolio-alert-source-board">
      <span
        v-for="source in sourceSummaries"
        :key="source.key"
        class="source-chip"
        :class="`source-chip--${source.key}`"
        :data-source="source.key"
      >
        {{ source.label }} {{ source.count }}
      </span>
    </div>

    <ul v-if="alerts.length > 0" class="alert-list" data-test="portfolio-alert-list">
      <li
        v-for="alert in primaryAlerts"
        :key="alert.id"
        class="alert-row"
        :class="[`alert-row--${alert.severity}`, `alert-row--${sourceKey(alert)}`]"
        :data-alert-id="alert.id"
        :data-severity="alert.severity"
        :data-source="sourceKey(alert)"
        data-test="portfolio-alert"
      >
        <span class="severity-pill" :class="`severity-pill--${alert.severity}`">
          {{ severityLabel(alert.severity) }}
        </span>
        <span class="alert-copy">
          <span class="alert-title-line">
            <strong>{{ alert.title }}</strong>
            <span class="alert-source">{{ sourceLabel(alert) }}</span>
          </span>
          <span class="alert-detail">{{ alert.detail }}</span>
          <span class="alert-action">{{ actionHint(alert) }}</span>
        </span>
      </li>
    </ul>

    <div v-if="additionalAlerts.length > 0" class="more-alerts" data-test="portfolio-alert-more">
      <span class="more-label">weitere Hinweise</span>
      <span class="more-count">{{ additionalAlerts.length }}</span>
      <span class="more-detail">{{ additionalSummary }}</span>
    </div>

    <p v-if="alerts.length === 0" class="empty-text" data-test="portfolio-alert-empty">
      Keine Alerts aus Summary, Risk, Coverage oder Contributors.
    </p>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type {
  PortfolioContributorsReadModel,
  PortfolioDataCoverageReadModel,
  PortfolioRiskReadModel,
  PortfolioSummaryReadModel
} from '@/shared/model/types'
import {
  buildPortfolioAlerts,
  type PortfolioAlert,
  type PortfolioAlertSeverity
} from '@/modules/dashboard/model/portfolioAlerts'

type AlertSourceKey = 'risk' | 'coverage' | 'concentration' | 'summary'

interface SourceSummary {
  key: AlertSourceKey
  label: string
  count: number
}

const PRIMARY_ALERT_LIMIT = 3

const severityLabels: Record<PortfolioAlertSeverity, string> = {
  kritisch: 'Kritisch',
  warnung: 'Warnung',
  info: 'Info'
}

const sourceLabels: Record<AlertSourceKey, string> = {
  risk: 'Risk',
  coverage: 'Coverage',
  concentration: 'Konzentration',
  summary: 'Summary'
}

const sourceOrder: AlertSourceKey[] = ['risk', 'coverage', 'concentration', 'summary']

const props = withDefaults(
  defineProps<{
    summary?: PortfolioSummaryReadModel | null
    risk?: PortfolioRiskReadModel | null
    coverage?: PortfolioDataCoverageReadModel | null
    contributors?: PortfolioContributorsReadModel | null
    maxAlerts?: number
  }>(),
  {
    summary: null,
    risk: null,
    coverage: null,
    contributors: null,
    maxAlerts: 5
  }
)

const alerts = computed(() =>
  buildPortfolioAlerts(
    {
      summary: props.summary,
      risk: props.risk,
      coverage: props.coverage,
      contributors: props.contributors
    },
    props.maxAlerts
  )
)

const primaryAlerts = computed(() => alerts.value.slice(0, PRIMARY_ALERT_LIMIT))
const additionalAlerts = computed(() => alerts.value.slice(PRIMARY_ALERT_LIMIT))

const sourceSummaries = computed<SourceSummary[]>(() => {
  const counts = new Map<AlertSourceKey, number>()

  for (const alert of alerts.value) {
    const key = sourceKey(alert)
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }

  return sourceOrder
    .filter((key) => counts.has(key))
    .map((key) => ({
      key,
      label: sourceLabels[key],
      count: counts.get(key) ?? 0
    }))
})

const countLabel = computed(() => {
  if (alerts.value.length === 0) return '0 Alerts'
  if (additionalAlerts.value.length > 0) return `${primaryAlerts.value.length} von ${alerts.value.length} sichtbar`
  return `${alerts.value.length} ${alerts.value.length === 1 ? 'Alert' : 'Alerts'}`
})

const additionalSummary = computed(() => {
  const severityCounts = additionalAlerts.value.reduce<Record<PortfolioAlertSeverity, number>>(
    (counts, alert) => {
      counts[alert.severity] += 1
      return counts
    },
    { kritisch: 0, warnung: 0, info: 0 }
  )

  return (Object.keys(severityCounts) as PortfolioAlertSeverity[])
    .filter((severity) => severityCounts[severity] > 0)
    .map((severity) => `${severityCounts[severity]} ${severityLabels[severity].toLowerCase()}`)
    .join(', ')
})

function severityLabel(severity: PortfolioAlertSeverity): string {
  return severityLabels[severity]
}

function sourceKey(alert: PortfolioAlert): AlertSourceKey {
  if (
    alert.id.includes('concentration') ||
    alert.id === 'small-portfolio' ||
    alert.source.toLowerCase().includes('summary')
  ) {
    return 'concentration'
  }

  if (alert.source === 'Coverage') return 'coverage'
  if (alert.source === 'Risk') return 'risk'

  return 'summary'
}

function sourceLabel(alert: PortfolioAlert): string {
  return sourceLabels[sourceKey(alert)]
}

function actionHint(alert: PortfolioAlert): string {
  if (alert.id.includes('concentration') || alert.id === 'small-portfolio') return 'Konzentration pruefen'
  if (alert.source === 'Coverage' || alert.id.includes('quality')) return 'Datenquelle pruefen'
  if (alert.id === 'high-tracking-error') return 'Benchmark-Abweichung pruefen'
  if (alert.source === 'Risk') return 'Risikobudget pruefen'
  if (alert.id === 'negative-range-return') return 'Renditetreiber pruefen'
  return 'Hinweis pruefen'
}
</script>

<style scoped>
.alerts-panel {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #ffffff;
  padding: 0.65rem 0.75rem;
  display: grid;
  gap: 0.45rem;
}

.alerts-panel--empty {
  background: #f8fafc;
}

.alerts-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.eyebrow {
  margin: 0;
  color: #475569;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0;
  line-height: 1.2;
  text-transform: uppercase;
}

h3 {
  margin: 0.08rem 0 0;
  color: #0f172a;
  font-size: 1rem;
  line-height: 1.2;
}

.alert-count,
.severity-pill,
.alert-source,
.source-chip,
.more-label,
.more-count {
  border-radius: 6px;
  font-weight: 700;
  white-space: nowrap;
}

.alert-count {
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #334155;
  font-size: 0.76rem;
  padding: 0.14rem 0.42rem;
}

.alert-count--empty {
  border-color: #bbf7d0;
  background: #f0fdf4;
  color: #166534;
}

.source-board {
  display: flex;
  flex-wrap: wrap;
  gap: 0.28rem;
}

.source-chip {
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #334155;
  font-size: 0.68rem;
  line-height: 1.15;
  padding: 0.12rem 0.36rem;
}

.source-chip--risk {
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
}

.source-chip--coverage {
  border-color: #bbf7d0;
  background: #f0fdf4;
  color: #166534;
}

.source-chip--concentration {
  border-color: #fecaca;
  background: #fef2f2;
  color: #991b1b;
}

.source-chip--summary {
  border-color: #ddd6fe;
  background: #faf5ff;
  color: #6b21a8;
}

.alert-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0;
}

.alert-row {
  min-width: 0;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: start;
  gap: 0.46rem;
  border-left: 3px solid var(--alert-accent, #94a3b8);
  border-top: 1px solid #e2e8f0;
  padding: 0.36rem 0 0.36rem 0.46rem;
}

.alert-row:first-child {
  border-top: 0;
}

.alert-row:last-child {
  padding-bottom: 0;
}

.alert-row--kritisch {
  --alert-accent: #dc2626;
}

.alert-row--warnung {
  --alert-accent: #d97706;
}

.alert-row--info {
  --alert-accent: #2563eb;
}

.severity-pill {
  align-self: start;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #334155;
  font-size: 0.68rem;
  line-height: 1.1;
  padding: 0.12rem 0.34rem;
}

.severity-pill--kritisch {
  border-color: #fecaca;
  background: #fee2e2;
  color: #991b1b;
}

.severity-pill--warnung {
  border-color: #fde68a;
  background: #fef3c7;
  color: #92400e;
}

.severity-pill--info {
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
}

.alert-copy {
  min-width: 0;
  color: #334155;
  display: grid;
  gap: 0.06rem;
  font-size: 0.82rem;
  line-height: 1.22;
}

.alert-title-line {
  min-width: 0;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
}

.alert-copy strong {
  color: #0f172a;
  font-size: 0.84rem;
  min-width: 0;
}

.alert-detail {
  color: #334155;
}

.alert-action {
  color: #475569;
  font-size: 0.74rem;
  font-weight: 700;
}

.alert-source {
  color: #64748b;
  font-size: 0.68rem;
  line-height: 1.15;
}

.more-alerts {
  min-width: 0;
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr);
  align-items: center;
  gap: 0.35rem;
  border-top: 1px solid #e2e8f0;
  padding-top: 0.42rem;
  color: #475569;
  font-size: 0.78rem;
  line-height: 1.2;
}

.more-label {
  color: #334155;
}

.more-count {
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #334155;
  font-size: 0.68rem;
  line-height: 1;
  padding: 0.12rem 0.34rem;
}

.more-detail {
  min-width: 0;
  color: #64748b;
}

.empty-text {
  margin: 0;
  color: #166534;
  font-size: 0.84rem;
  line-height: 1.35;
}

@media (max-width: 620px) {
  .alert-title-line,
  .more-alerts {
    align-items: flex-start;
  }

  .alert-title-line {
    display: grid;
    gap: 0.08rem;
  }

  .more-alerts {
    grid-template-columns: auto auto;
  }

  .more-detail {
    grid-column: 1 / -1;
  }
}
</style>
