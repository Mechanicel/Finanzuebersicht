<template>
  <section class="card">
    <h2>Depot-/Holding-Erfassung</h2>
    <div class="grid" style="grid-template-columns: 1fr auto; margin-bottom: 1rem">
      <div><label>Person-ID</label><input class="input" v-model.trim="personId" /></div>
      <button class="btn" @click="load">Depots laden</button>
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
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient } from '../api/client'
import type { PortfolioReadModel } from '../types/models'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

const route = useRoute()
const personId = ref(typeof route.query.personId === 'string' ? route.query.personId : '00000000-0000-0000-0000-000000000101')
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
