<template>
  <section class="card">
    <h2>Kontenverwaltung</h2>
    <div class="grid" style="grid-template-columns: 1fr auto; margin-bottom: 1rem">
      <div><label>Person-ID</label><input class="input" v-model.trim="personId" /></div>
      <button class="btn" @click="load">Konten laden</button>
    </div>
    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" />
    <EmptyState v-else-if="!items.length">Keine Konten für diese Person.</EmptyState>
    <table v-else class="table">
      <thead><tr><th>Name</th><th>Typ</th><th>Saldo</th></tr></thead>
      <tbody><tr v-for="a in items" :key="a.account_id"><td>{{ a.name }}</td><td>{{ a.type }}</td><td>{{ a.balance }}</td></tr></tbody>
    </table>
  </section>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { apiClient } from '../api/client'
import type { AccountReadModel } from '../types/models'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

const personId = ref('00000000-0000-0000-0000-000000000101')
const items = ref<AccountReadModel[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    items.value = await apiClient.accounts(personId.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Fehler'
  } finally {
    loading.value = false
  }
}
</script>
