<template>
  <section class="grid">
    <article class="card">
      <h2>Person-Detail</h2>
      <p><strong>ID:</strong> {{ personId }}</p>
      <div class="grid" style="grid-template-columns: 1fr 1fr 1fr">
        <div><label>Vorname</label><input class="input" v-model.trim="form.firstName" /></div>
        <div><label>Nachname</label><input class="input" v-model.trim="form.lastName" /></div>
        <div><label>E-Mail</label><input class="input" v-model.trim="form.email" type="email" /></div>
      </div>
      <p v-if="formError" class="error">{{ formError }}</p>
      <div style="display: flex; gap: 0.5rem; margin-top: 1rem">
        <button class="btn" @click="save" :disabled="submitting">Änderungen speichern</button>
        <button class="btn" @click="deleteCurrent" :disabled="submitting" style="background: #dc2626">Person löschen</button>
      </div>
    </article>
    <article class="card">
      <h3>Konten</h3>
      <LoadingState v-if="loading" />
      <ErrorState v-else-if="error" :message="error" />
      <EmptyState v-else-if="!accounts.length">Keine Konten gefunden.</EmptyState>
      <ul v-else>
        <li v-for="a in accounts" :key="a.account_id">{{ a.name }} · {{ a.type }} · {{ a.balance }} EUR</li>
      </ul>
    </article>
  </section>
</template>
<script setup lang="ts">
import axios from 'axios'
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '../api/client'
import type { AccountReadModel } from '../types/models'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

const props = defineProps<{ personId: string }>()
const personId = props.personId
const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const error = ref<string | null>(null)
const accounts = ref<AccountReadModel[]>([])
const form = reactive({ firstName: '', lastName: '', email: '' })
const formError = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    const [personDetail, accountList] = await Promise.all([apiClient.person(personId), apiClient.accounts(personId)])
    form.firstName = personDetail.person.first_name
    form.lastName = personDetail.person.last_name
    form.email = personDetail.person.email ?? ''
    accounts.value = accountList
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Fehler beim Laden'
  } finally {
    loading.value = false
  }
}

async function save() {
  formError.value = null
  if (!form.firstName || !form.lastName) {
    formError.value = 'Vorname und Nachname sind Pflichtfelder.'
    return
  }

  submitting.value = true
  try {
    await apiClient.updatePerson(personId, {
      first_name: form.firstName,
      last_name: form.lastName,
      email: form.email || undefined
    })
  } catch (e) {
    if (axios.isAxiosError(e)) {
      formError.value = e.response?.data?.detail ?? 'Speichern fehlgeschlagen.'
      return
    }
    formError.value = e instanceof Error ? e.message : 'Speichern fehlgeschlagen.'
  } finally {
    submitting.value = false
  }
}

async function deleteCurrent() {
  formError.value = null
  submitting.value = true
  try {
    await apiClient.deletePerson(personId)
    await router.push('/persons')
  } catch (e) {
    formError.value = e instanceof Error ? e.message : 'Löschen fehlgeschlagen.'
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>
