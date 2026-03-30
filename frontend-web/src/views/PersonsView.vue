<template>
  <section class="card">
    <div class="header-row">
      <div>
        <h2>Person suchen & auswählen</h2>
        <p class="subtitle">Suche serverseitig nach Vorname, Nachname oder E-Mail und öffne danach den Personen-Hub.</p>
      </div>
      <div class="header-actions">
        <RouterLink class="btn flow-btn" to="/">Zur Startseite</RouterLink>
        <RouterLink class="btn secondary" to="/persons/new">Neue Person anlegen</RouterLink>
      </div>
    </div>

    <div class="search-row">
      <div>
        <label for="person-search">Suchbegriff</label>
        <input
          id="person-search"
          class="input"
          v-model.trim="searchTerm"
          placeholder="z. B. Anna Muster oder anna@example.com"
          autocomplete="off"
        />
      </div>
      <p class="search-hint" aria-live="polite">
        <span v-if="isRefreshing">Suche läuft…</span>
        <span v-else>Live-Suche aktiv · {{ activeTerm ? `Ergebnisse für „${activeTerm}“` : 'Zeige alle Personen' }}</span>
      </p>
    </div>

    <LoadingState v-if="showInitialLoader" />
    <ErrorState v-else-if="error" :message="error" />
    <EmptyState v-else-if="persons && persons.items.length === 0">
      Keine Treffer für „{{ activeTerm || 'alle Personen' }}“.
    </EmptyState>
    <ul v-else-if="persons" class="person-list" aria-label="Gefundene Personen">
      <li v-for="p in persons.items" :key="p.person_id" class="person-item">
        <RouterLink :to="`/persons/${p.person_id}`" class="person-link">
          <div class="person-main">
            <strong>{{ p.first_name }} {{ p.last_name }}</strong>
            <span>{{ p.email || 'Keine E-Mail hinterlegt' }}</span>
          </div>
          <span class="person-meta">ID {{ p.person_id }}</span>
        </RouterLink>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { apiClient } from '../api/client'
import type { PersonListReadModel } from '../types/models'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import LoadingState from '../components/LoadingState.vue'

const isRefreshing = ref(false)
const error = ref<string | null>(null)
const persons = ref<PersonListReadModel | null>(null)
const searchTerm = ref('')
const activeTerm = ref('')
const debounceMs = 300
let debounceHandle: ReturnType<typeof setTimeout> | null = null

const showInitialLoader = ref(true)

async function fetchPersons(term: string) {
  const isFirstLoad = persons.value === null
  isRefreshing.value = !isFirstLoad
  error.value = null
  activeTerm.value = term

  try {
    persons.value = await apiClient.persons({ q: term || undefined, limit: 25, offset: 0 })
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Fehler beim Laden der Personen.'
  } finally {
    isRefreshing.value = false
    showInitialLoader.value = false
  }
}

function scheduleSearch(term: string) {
  if (debounceHandle) {
    clearTimeout(debounceHandle)
  }

  debounceHandle = setTimeout(() => {
    void fetchPersons(term)
  }, debounceMs)
}

watch(searchTerm, (value) => {
  scheduleSearch(value)
})

onMounted(() => {
  void fetchPersons('')
})

onBeforeUnmount(() => {
  if (debounceHandle) {
    clearTimeout(debounceHandle)
  }
})
</script>

<style scoped>
.header-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
  margin-bottom: 1rem;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.subtitle {
  margin-top: 0.35rem;
  color: #475569;
}

.search-row {
  display: grid;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.search-hint {
  margin: 0;
  color: #475569;
  font-size: 0.9rem;
}

.person-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.6rem;
}

.person-item {
  margin: 0;
}

.person-link {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  border: 1px solid #dbe4ef;
  border-radius: 0.75rem;
  padding: 0.85rem 1rem;
  text-decoration: none;
  color: inherit;
  background: #fff;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}

.person-link:hover {
  border-color: #1d4ed8;
  background: #f8fbff;
}

.person-link:focus-visible {
  outline: none;
  border-color: #1d4ed8;
  box-shadow: 0 0 0 3px rgba(29, 78, 216, 0.2);
}

.person-main {
  display: grid;
  gap: 0.15rem;
}

.person-main span {
  color: #475569;
}

.person-meta {
  color: #64748b;
  font-size: 0.85rem;
  white-space: nowrap;
}
</style>
