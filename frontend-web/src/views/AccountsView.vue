<template>
  <section class="card">
    <div class="view-header">
      <div class="view-header-copy">
        <p class="eyebrow">Personen-Hub · Schritt</p>
        <h2>Konten verwalten</h2>
        <p v-if="personId">{{ subtitle }}</p>
        <p v-else>Diese Ansicht ist nur aus dem Personen-Hub sinnvoll nutzbar.</p>
      </div>
      <RouterLink class="btn flow-btn" :to="backTarget">{{ backLabel }}</RouterLink>
    </div>

    <p v-if="!personId" class="context-hint">
      Kein Personenkontext vorhanden. Bitte wähle zuerst eine Person aus und öffne danach den Schritt
      „Konten verwalten“ im Personen-Hub.
    </p>

    <template v-else>
      <LoadingState v-if="loading" />
      <ErrorState v-else-if="errorMessage" :message="errorMessage" />
      <EmptyState v-else-if="accounts.length === 0">
        Für diese Person sind aktuell keine Konten vorhanden.
      </EmptyState>

      <article v-else class="accounts-card">
        <h3>Gefundene Konten</h3>
        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Typ</th>
              <th>Saldo</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="account in accounts" :key="account.account_id">
              <td>{{ account.label }}</td>
              <td>{{ account.account_type }}</td>
              <td>{{ account.balance }}</td>
            </tr>
          </tbody>
        </table>
      </article>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient } from '../api/client'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import LoadingState from '../components/LoadingState.vue'
import type { AccountReadModel, PersonReadModel } from '../types/models'

const route = useRoute()
const personId = computed(() => (typeof route.query.personId === 'string' ? route.query.personId : ''))
const backTarget = computed(() => (personId.value ? `/persons/${personId.value}` : '/persons/select'))
const backLabel = computed(() => (personId.value ? 'Zurück zum Personen-Hub' : 'Zur Personenliste'))

const loading = ref(false)
const errorMessage = ref<string | null>(null)
const person = ref<PersonReadModel | null>(null)
const accounts = ref<AccountReadModel[]>([])

const subtitle = computed(() => {
  const fullName = `${person.value?.first_name ?? ''} ${person.value?.last_name ?? ''}`.trim()
  if (fullName) {
    return `Kontenübersicht für ${fullName}`
  }
  return 'Kontenübersicht für die ausgewählte Person'
})

async function loadData() {
  if (!personId.value) {
    person.value = null
    accounts.value = []
    errorMessage.value = null
    return
  }

  loading.value = true
  errorMessage.value = null

  try {
    const [personDetail, accountList] = await Promise.all([
      apiClient.person(personId.value),
      apiClient.accounts(personId.value)
    ])
    person.value = personDetail.person
    accounts.value = accountList
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : 'Konten konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

watch(personId, loadData)
onMounted(loadData)
</script>

<style scoped>
.eyebrow {
  margin: 0;
  color: #475569;
  font-weight: 600;
}

.context-hint {
  margin-top: 0;
  margin-bottom: 0;
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 0.65rem 0.75rem;
}

.accounts-card h3 {
  margin-top: 0;
}
</style>
