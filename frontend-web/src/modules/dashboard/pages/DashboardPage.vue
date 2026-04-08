<template>
  <section class="dashboard-layout">
    <article class="card page-shell">
      <div class="view-header page-header">
        <div class="view-header-copy">
          <p class="eyebrow">Personenbezogene Analytics</p>
          <h2>Analytics-Dashboard</h2>
          <p class="subtitle">
            Überblick, Allokation, Zeitreihen und Kennzahlen für den aktuellen Personenkontext.
          </p>
        </div>
        <RouterLink class="btn flow-btn" :to="backTarget">{{ backLabel }}</RouterLink>
      </div>

      <div class="context-row">
        <p class="context-label">Kontext</p>
        <p v-if="hasPersonContext" class="context-value">
          Person-ID: <code>{{ personId }}</code>
        </p>
        <p v-else class="context-hint">
          Kein Personenkontext gesetzt. Öffne das Dashboard über den Personen-Hub, damit die Analyse geladen werden kann.
        </p>
      </div>

      <div class="content-sections">
        <EmptyState v-if="!hasPersonContext">
          Das Analytics-Dashboard benötigt einen gültigen Personenkontext.
        </EmptyState>

        <template v-else>
          <DashboardOverviewSection
            :section="overviewSection"
            :meta-text="sectionMetaText(overviewSection)"
            :error-message="overviewError"
            @retry="void loadOverview()"
          />

          <DashboardAllocationSection
            :section="allocationSection"
            :meta-text="sectionMetaText(allocationSection)"
            :error-message="allocationError"
            @retry="void loadAllocation()"
          />

          <DashboardTimeseriesSection
            :section="timeseriesSection"
            :meta-text="sectionMetaText(timeseriesSection)"
            :error-message="timeseriesError"
            @retry="void loadTimeseries()"
          />

          <DashboardMetricsSection
            :section="metricsSection"
            :meta-text="sectionMetaText(metricsSection)"
            :error-message="metricsError"
            @retry="void loadMetrics()"
          />

          <DepotAnalysisWorkspace :person-id="personId" />
        </template>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import type {
  DashboardAllocationPayload,
  DashboardMetricsPayload,
  DashboardOverviewPayload,
  DashboardSectionReadModel,
  DashboardTimeseriesPayload
} from '@/shared/model/types'
import { extractApiErrorMessage } from '@/shared/api/extractApiErrorMessage'
import EmptyState from '@/shared/ui/EmptyState.vue'
import DepotAnalysisWorkspace from '@/modules/dashboard/components/DepotAnalysisWorkspace.vue'
import DashboardOverviewSection from '@/modules/dashboard/components/DashboardOverviewSection.vue'
import DashboardAllocationSection from '@/modules/dashboard/components/DashboardAllocationSection.vue'
import DashboardTimeseriesSection from '@/modules/dashboard/components/DashboardTimeseriesSection.vue'
import DashboardMetricsSection from '@/modules/dashboard/components/DashboardMetricsSection.vue'
import {
  fetchDashboardAllocation,
  fetchDashboardMetrics,
  fetchDashboardOverview,
  fetchDashboardTimeseries
} from '@/modules/dashboard/api/dashboardApi'

const route = useRoute()

const personId = computed(() => (typeof route.query.personId === 'string' ? route.query.personId.trim() : ''))
const hasPersonContext = computed(() => personId.value.length > 0)
const backTarget = computed(() => (hasPersonContext.value ? `/persons/${personId.value}` : '/persons/select'))
const backLabel = computed(() => (hasPersonContext.value ? 'Zurück zum Personen-Hub' : 'Zur Personenliste'))

const overviewSection = ref<DashboardSectionReadModel<DashboardOverviewPayload>>(buildPendingSection('overview', {}))
const allocationSection = ref<DashboardSectionReadModel<DashboardAllocationPayload>>(buildPendingSection('allocation', {}))
const timeseriesSection = ref<DashboardSectionReadModel<DashboardTimeseriesPayload>>(buildPendingSection('timeseries', {}))
const metricsSection = ref<DashboardSectionReadModel<DashboardMetricsPayload>>(buildPendingSection('metrics', {}))

const overviewError = ref('')
const allocationError = ref('')
const timeseriesError = ref('')
const metricsError = ref('')

function buildPendingSection<TPayload>(section: string, payload: TPayload): DashboardSectionReadModel<TPayload> {
  return {
    person_id: personId.value,
    section,
    state: 'pending',
    generated_at: null,
    stale_at: null,
    refresh_in_progress: false,
    warnings: [],
    payload
  }
}

function resetSections() {
  overviewSection.value = buildPendingSection('overview', {})
  allocationSection.value = buildPendingSection('allocation', {})
  timeseriesSection.value = buildPendingSection('timeseries', {})
  metricsSection.value = buildPendingSection('metrics', {})
  overviewError.value = ''
  allocationError.value = ''
  timeseriesError.value = ''
  metricsError.value = ''
}

function sectionMetaText(section: DashboardSectionReadModel<unknown>): string {
  const generatedText = section.generated_at
    ? `Stand: ${new Date(section.generated_at).toLocaleString('de-DE')}`
    : section.state === 'pending'
      ? 'Lade Section …'
      : 'Noch kein Datenstand verfügbar'

  return section.stale_at
    ? `${generatedText} · Cache gültig bis ${new Date(section.stale_at).toLocaleString('de-DE')}`
    : generatedText
}

function mapSectionError(rawError: unknown, fallback: string): string {
  if (axios.isAxiosError(rawError)) {
    if (rawError.response?.status === 404) {
      return 'Für diese Section liegen aktuell keine Analytics-Daten vor.'
    }

    const code = rawError.code?.toUpperCase()
    if (code === 'ECONNABORTED' || code === 'ETIMEDOUT' || code === 'ERR_NETWORK') {
      return 'Die Section konnte nicht rechtzeitig geladen werden. Bitte erneut versuchen.'
    }

    if (rawError.message.toLowerCase().includes('timeout')) {
      return 'Zeitüberschreitung beim Laden der Section. Bitte erneut versuchen.'
    }
  }

  const extracted = extractApiErrorMessage(rawError, fallback)
  if (extracted.includes('Request failed with status code') || extracted.includes('timeout of')) {
    return fallback
  }
  return extracted
}

async function loadOverview() {
  if (!hasPersonContext.value) {
    return
  }

  overviewSection.value = { ...overviewSection.value, state: 'pending' }
  overviewError.value = ''
  try {
    overviewSection.value = await fetchDashboardOverview(personId.value)
  } catch (error) {
    overviewSection.value = { ...overviewSection.value, state: 'error' }
    overviewError.value = mapSectionError(error, 'Die Überblicks-Section konnte nicht geladen werden.')
  }
}

async function loadAllocation() {
  if (!hasPersonContext.value) {
    return
  }

  allocationSection.value = { ...allocationSection.value, state: 'pending' }
  allocationError.value = ''
  try {
    allocationSection.value = await fetchDashboardAllocation(personId.value)
  } catch (error) {
    allocationSection.value = { ...allocationSection.value, state: 'error' }
    allocationError.value = mapSectionError(error, 'Die Allokations-Section konnte nicht geladen werden.')
  }
}

async function loadTimeseries() {
  if (!hasPersonContext.value) {
    return
  }

  timeseriesSection.value = { ...timeseriesSection.value, state: 'pending' }
  timeseriesError.value = ''
  try {
    timeseriesSection.value = await fetchDashboardTimeseries(personId.value)
  } catch (error) {
    timeseriesSection.value = { ...timeseriesSection.value, state: 'error' }
    timeseriesError.value = mapSectionError(error, 'Die Zeitreihen-Section konnte nicht geladen werden.')
  }
}

async function loadMetrics() {
  if (!hasPersonContext.value) {
    return
  }

  metricsSection.value = { ...metricsSection.value, state: 'pending' }
  metricsError.value = ''
  try {
    metricsSection.value = await fetchDashboardMetrics(personId.value)
  } catch (error) {
    metricsSection.value = { ...metricsSection.value, state: 'error' }
    metricsError.value = mapSectionError(error, 'Die Kennzahlen-Section konnte nicht geladen werden.')
  }
}

function loadAllSections() {
  if (!hasPersonContext.value) {
    resetSections()
    return
  }

  resetSections()
  void Promise.allSettled([loadOverview(), loadAllocation(), loadTimeseries(), loadMetrics()])
}

onMounted(() => {
  loadAllSections()
})

watch(
  () => route.query.personId,
  () => {
    loadAllSections()
  }
)
</script>

<style scoped>
.dashboard-layout {
  grid-template-columns: 1fr;
}

.page-shell {
  padding: 1.25rem;
}

.page-header {
  margin-bottom: 1rem;
}

.eyebrow {
  margin: 0;
  color: #475569;
  font-weight: 600;
}

.subtitle {
  margin-top: 0.45rem;
  margin-bottom: 0;
  color: #475569;
}

.context-row {
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  border-radius: 10px;
  padding: 0.8rem 1rem;
  margin-bottom: 1rem;
}

.context-label {
  margin: 0 0 0.35rem;
  font-size: 0.85rem;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.context-value {
  margin: 0;
  color: #0f172a;
}

.context-hint {
  margin: 0;
  color: #92400e;
}

.content-sections {
  display: grid;
  gap: 1rem;
}
</style>
