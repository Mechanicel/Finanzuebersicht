<template>
  <section class="card">
    <h2>Personenliste</h2>
    <div class="grid" style="grid-template-columns: 1fr 1fr auto; align-items: end; margin-bottom: 1rem">
      <div><label>Vorname</label><input class="input" v-model.trim="form.firstName" /></div>
      <div><label>Nachname</label><input class="input" v-model.trim="form.lastName" /></div>
      <button class="btn" @click="savePerson">Person anlegen</button>
    </div>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" />
    <EmptyState v-else-if="!persons?.items.length">Noch keine Personen aus dem Gateway.</EmptyState>
    <table v-else class="table">
      <thead><tr><th>Name</th><th>ID</th><th></th></tr></thead>
      <tbody>
        <tr v-for="p in persons.items" :key="p.person_id">
          <td>{{ p.display_name }}</td>
          <td>{{ p.person_id }}</td>
          <td><RouterLink :to="`/persons/${p.person_id}`">Details</RouterLink></td>
        </tr>
      </tbody>
    </table>
    <p v-if="formError" class="error">{{ formError }}</p>
  </section>
</template>
<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { apiClient } from '../api/client'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'
import type { PersonListReadModel } from '../types/models'

const loading = ref(false)
const error = ref<string | null>(null)
const persons = ref<PersonListReadModel | null>(null)
const form = reactive({ firstName: '', lastName: '' })
const formError = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    persons.value = await apiClient.persons()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Fehler beim Laden'
  } finally {
    loading.value = false
  }
}

function savePerson() {
  formError.value = null
  if (!form.firstName || !form.lastName) {
    formError.value = 'Vorname und Nachname sind Pflichtfelder.'
    return
  }
  form.firstName = ''
  form.lastName = ''
}

onMounted(load)
</script>
