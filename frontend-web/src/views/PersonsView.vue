<template>
  <section class="card">
    <div class="header-row">
      <div>
        <h2>Person suchen & auswählen</h2>
        <p class="subtitle">Suche serverseitig nach Vorname, Nachname oder E-Mail und öffne danach den Personen-Hub.</p>
      </div>
      <RouterLink class="btn secondary" to="/persons/new">Neue Person anlegen</RouterLink>
    </div>

    <form class="search-row" @submit.prevent="searchPersons">
      <div>
        <label for="person-search">Suchbegriff</label>
        <input
          id="person-search"
          class="input"
          v-model.trim="searchTerm"
          placeholder="z. B. Anna Muster oder anna@example.com"
        />
      </div>
      <button class="btn" :disabled="loading">Suchen</button>
    </form>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" />
    <EmptyState v-else-if="persons && persons.items.length === 0">
      Keine Treffer für „{{ submittedTerm || 'alle Personen' }}“.
    </EmptyState>
    <table v-else-if="persons" class="table">
      <thead><tr><th>Name</th><th>E-Mail</th><th>ID</th><th></th></tr></thead>
      <tbody>
        <tr v-for="p in persons.items" :key="p.person_id">
          <td>{{ p.first_name }} {{ p.last_name }}</td>
          <td>{{ p.email || '—' }}</td>
          <td>{{ p.person_id }}</td>
          <td><RouterLink :to="`/persons/${p.person_id}`">Öffnen</RouterLink></td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiClient } from '../api/client'
import type { PersonListReadModel } from '../types/models'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import LoadingState from '../components/LoadingState.vue'

const loading = ref(false)
const error = ref<string | null>(null)
const persons = ref<PersonListReadModel | null>(null)
const searchTerm = ref('')
const submittedTerm = ref('')

async function searchPersons() {
  loading.value = true
  error.value = null
  submittedTerm.value = searchTerm.value

  try {
    persons.value = await apiClient.persons({ q: searchTerm.value || undefined, limit: 25, offset: 0 })
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Fehler beim Laden der Personen.'
  } finally {
    loading.value = false
  }
}

onMounted(searchPersons)
</script>

<style scoped>
.header-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
  margin-bottom: 1rem;
}

.subtitle {
  margin-top: 0.35rem;
  color: #475569;
}

.search-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.75rem;
  align-items: end;
  margin-bottom: 1rem;
}
</style>
