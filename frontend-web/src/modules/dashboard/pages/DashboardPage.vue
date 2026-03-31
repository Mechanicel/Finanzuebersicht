<template>
  <section class="grid">
    <article class="card">
      <div class="view-header">
        <div class="view-header-copy">
          <h2>Analytics-Dashboard</h2>
          <p>Kennzahlen und Auswertungen im Personenkontext abrufen.</p>
        </div>
        <RouterLink class="btn flow-btn" :to="backTarget">{{ backLabel }}</RouterLink>
      </div>
      <p v-if="!hasPersonContext" class="context-hint">
        Bitte zuerst eine Person auswählen und den Bereich aus dem Personen-Hub öffnen.
      </p>
      <div class="grid" style="grid-template-columns: 1fr auto">
        <div><label>Person-ID</label><input class="input" v-model.trim="personId" /></div>
        <button class="btn" @click="load" :disabled="!hasPersonContext">Dashboard laden</button>
      </div>
    </article>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" />
    <EmptyState v-else-if="!dashboard">Keine Dashboarddaten.</EmptyState>
    <template v-else>
      <article class="card">
        <h3>Kennzahlen</h3>
        <div class="kpis">
          <div class="card" v-for="(k,idx) in dashboard.kpis" :key="idx">
            <strong>{{ k.label }}</strong>
            <div>{{ k.value }}</div>
          </div>
        </div>
      </article>
      <article class="card">
        <h3>Zeitreihe</h3>
        <div style="height: 280px">
          <SimpleLineChart :points="timeseriesPoints" />
        </div>
      </article>
      <article class="card">
        <h3>Allocation</h3>
        <div style="height: 280px">
          <SimplePieChart :labels="allocLabels" :values="allocValues" />
        </div>
      </article>
      <article class="card">
        <h3>Forecast</h3>
        <pre>{{ dashboard.metrics }}</pre>
      </article>
    </template>
  </section>
</template>
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient } from '@/shared/api/client'
import type { DashboardReadModel } from '@/shared/model/types'
import LoadingState from '@/shared/ui/LoadingState.vue'
import ErrorState from '@/shared/ui/ErrorState.vue'
import EmptyState from '@/shared/ui/EmptyState.vue'
import SimpleLineChart from '@/shared/ui/SimpleLineChart.vue'
import SimplePieChart from '@/shared/ui/SimplePieChart.vue'

const route = useRoute()
const personId = ref(typeof route.query.personId === 'string' ? route.query.personId : '00000000-0000-0000-0000-000000000101')
const hasPersonContext = computed(() => typeof route.query.personId === 'string' && route.query.personId.length > 0)
const backTarget = computed(() => (hasPersonContext.value ? `/persons/${route.query.personId as string}` : '/persons/select'))
const backLabel = computed(() => (hasPersonContext.value ? 'Zurück zum Personen-Hub' : 'Zur Personenliste'))
const dashboard = ref<DashboardReadModel | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const timeseriesPoints = computed(() => dashboard.value?.timeseries?.points ?? [])
const allocLabels = computed(() => dashboard.value?.allocation?.labels ?? [])
const allocValues = computed(() => dashboard.value?.allocation?.values ?? [])

async function load() {
  loading.value = true
  error.value = null
  try {
    dashboard.value = await apiClient.dashboard(personId.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Fehler beim Laden des Dashboards'
  } finally {
    loading.value = false
  }
}
onMounted(() => {
  if (typeof route.query.personId === 'string') {
    void load()
  }
})
</script>

<style scoped>
.context-hint {
  margin-top: 0;
  margin-bottom: 0.75rem;
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 0.65rem 0.75rem;
}

</style>
