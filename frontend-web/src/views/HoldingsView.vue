<template>
  <section class="card">
    <div class="view-header">
      <div class="view-header-copy">
        <h2>Depot-/Holding-Erfassung</h2>
        <p>Depots und Holdings zur aktuell ausgewählten Person laden.</p>
      </div>
      <RouterLink class="btn flow-btn" :to="backTarget">{{ backLabel }}</RouterLink>
    </div>
    <p v-if="!hasPersonContext" class="context-hint">
      Bitte zuerst eine Person auswählen und den Bereich aus dem Personen-Hub öffnen.
    </p>
    <div class="grid" style="grid-template-columns: 1fr auto; margin-bottom: 1rem">
      <div><label>Person-ID</label><input class="input" v-model.trim="personId" /></div>
      <button class="btn" @click="load" :disabled="!hasPersonContext">Depots laden</button>
    </div>
    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" />
    <EmptyState v-else-if="!portfolios.length">Keine Depots vorhanden.</EmptyState>
    <ul v-else>
      <li v-for="p in portfolios" :key="p.portfolio_id">{{ p.label }} · {{ p.total_value }} EUR</li>
    </ul>
  </section>
</template>
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient } from '../api/client'
import type { PortfolioReadModel } from '../types/models'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

const route = useRoute()
const personId = ref(typeof route.query.personId === 'string' ? route.query.personId : '00000000-0000-0000-0000-000000000101')
const hasPersonContext = typeof route.query.personId === 'string' && route.query.personId.length > 0
const backTarget = computed(() =>
  hasPersonContext ? `/persons/${route.query.personId as string}` : '/persons/select'
)
const backLabel = computed(() => (hasPersonContext ? 'Zurück zum Personen-Hub' : 'Zur Personenliste'))
const portfolios = ref<PortfolioReadModel[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    portfolios.value = await apiClient.portfolios(personId.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Fehler'
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
