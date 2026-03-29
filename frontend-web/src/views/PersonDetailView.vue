<template>
  <section class="grid">
    <article class="card">
      <h2>Person-Detail</h2>
      <p><strong>ID:</strong> {{ personId }}</p>
      <div class="grid" style="grid-template-columns: 1fr 1fr">
        <div><label>Anzeigename</label><input class="input" v-model.trim="form.displayName" /></div>
        <div><label>E-Mail</label><input class="input" v-model.trim="form.email" type="email" /></div>
      </div>
      <p v-if="formError" class="error">{{ formError }}</p>
      <button class="btn" @click="save">Änderungen speichern</button>
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
import { onMounted, reactive, ref } from 'vue'
import { apiClient } from '../api/client'
import type { AccountReadModel } from '../types/models'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

const props = defineProps<{ personId: string }>()
const personId = props.personId
const loading = ref(false)
const error = ref<string | null>(null)
const accounts = ref<AccountReadModel[]>([])
const form = reactive({ displayName: '', email: '' })
const formError = ref<string | null>(null)

async function load() {
  loading.value = true
  try {
    accounts.value = await apiClient.accounts(personId)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Fehler beim Laden'
  } finally {
    loading.value = false
  }
}
function save() {
  formError.value = form.displayName.length < 2 ? 'Anzeigename muss mindestens 2 Zeichen haben.' : null
}
onMounted(load)
</script>
