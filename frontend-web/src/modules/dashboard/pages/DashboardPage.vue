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
        <LoadingState v-if="loading" />
        <ErrorState v-else-if="error" :message="error" />
        <EmptyState v-else-if="!hasPersonContext">
          Das Analytics-Dashboard benötigt einen gültigen Personenkontext.
        </EmptyState>
        <EmptyState v-else-if="!dashboard">
          Für diese Person liegen aktuell keine Analytics-Daten vor.
        </EmptyState>

        <template v-else>
          <article class="card section-card">
            <h3>Überblick</h3>
            <div class="kpis">
              <div class="card kpi-card" v-for="(k, idx) in dashboard.kpis" :key="idx">
                <strong>{{ k.label }}</strong>
                <div>{{ k.value }}</div>
              </div>
            </div>
          </article>

          <article class="card section-card">
            <h3>Allokation</h3>
            <div v-if="hasAllocationData" class="chart-box">
              <SimplePieChart :labels="allocLabels" :values="allocValues" />
            </div>
            <EmptyState v-else>Keine Allokationsdaten verfügbar.</EmptyState>
          </article>

          <article class="card section-card">
            <h3>Zeitreihe</h3>
            <div v-if="hasTimeseriesData" class="chart-box">
              <SimpleLineChart :points="timeseriesPoints" />
            </div>
            <EmptyState v-else>Keine Zeitreihendaten verfügbar.</EmptyState>
          </article>

          <article class="card section-card">
            <h3>Kennzahlen</h3>
            <pre class="metrics-preview">{{ dashboard.metrics }}</pre>
          </article>

          <article class="card section-card depot-placeholder">
            <h3>Depot-Analyse</h3>
            <p>
              Dieser Bereich ist als Einstieg für die nächste Ausbaustufe reserviert. Hier werden künftig Depot-bezogene
              Analysen im Personenkontext ergänzt.
            </p>
            <span class="placeholder-badge">Platzhalter</span>
          </article>
        </template>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient } from '@/shared/api/client'
import { extractApiErrorMessage } from '@/shared/api/extractApiErrorMessage'
import type { DashboardReadModel } from '@/shared/model/types'
import LoadingState from '@/shared/ui/LoadingState.vue'
import ErrorState from '@/shared/ui/ErrorState.vue'
import EmptyState from '@/shared/ui/EmptyState.vue'
import SimpleLineChart from '@/shared/ui/SimpleLineChart.vue'
import SimplePieChart from '@/shared/ui/SimplePieChart.vue'

const route = useRoute()
const dashboard = ref<DashboardReadModel | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const personId = computed(() => (typeof route.query.personId === 'string' ? route.query.personId.trim() : ''))
const hasPersonContext = computed(() => personId.value.length > 0)
const backTarget = computed(() => (hasPersonContext.value ? `/persons/${personId.value}` : '/persons/select'))
const backLabel = computed(() => (hasPersonContext.value ? 'Zurück zum Personen-Hub' : 'Zur Personenliste'))

const timeseriesPoints = computed(() => dashboard.value?.timeseries?.points ?? [])
const allocLabels = computed(() => dashboard.value?.allocation?.labels ?? [])
const allocValues = computed(() => dashboard.value?.allocation?.values ?? [])
const hasTimeseriesData = computed(() => timeseriesPoints.value.length > 0)
const hasAllocationData = computed(() => allocLabels.value.length > 0 && allocValues.value.length > 0)

function mapDashboardError(rawError: unknown): string {
  if (axios.isAxiosError(rawError) && rawError.response?.status === 404) {
    return 'Für die ausgewählte Person konnten keine Analytics-Daten gefunden werden.'
  }

  const extracted = extractApiErrorMessage(rawError, 'Das Dashboard konnte nicht geladen werden.')
  if (extracted.includes('Request failed with status code')) {
    return 'Das Dashboard konnte aktuell nicht geladen werden. Bitte später erneut versuchen.'
  }
  return extracted
}

async function loadDashboard() {
  if (!hasPersonContext.value) {
    dashboard.value = null
    error.value = null
    return
  }

  loading.value = true
  error.value = null
  try {
    dashboard.value = await apiClient.dashboard(personId.value)
  } catch (rawError) {
    dashboard.value = null
    error.value = mapDashboardError(rawError)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadDashboard()
})

watch(
  () => route.query.personId,
  () => {
    void loadDashboard()
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

.section-card h3 {
  margin-top: 0;
}

.chart-box {
  height: 280px;
}

.kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}

.kpi-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.metrics-preview {
  margin: 0;
  white-space: pre-wrap;
}

.depot-placeholder p {
  margin-top: 0.35rem;
  margin-bottom: 0.75rem;
  color: #475569;
}

.placeholder-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  color: #334155;
  font-size: 0.8rem;
  font-weight: 600;
  background: #f1f5f9;
}
</style>
