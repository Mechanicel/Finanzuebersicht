<template>
  <section class="card">
    <div class="view-header">
      <div class="view-header-copy">
        <h2>Neue Person anlegen</h2>
        <p>Erfasse eine neue Person. Nach erfolgreicher Anlage kannst du direkt in den Personen-Hub wechseln.</p>
      </div>
      <RouterLink class="btn flow-btn" to="/">Zur Startseite</RouterLink>
    </div>

    <div class="grid" style="grid-template-columns: 1fr 1fr 1fr auto; align-items: end; margin-bottom: 1rem">
      <div><label>Vorname</label><input class="input" v-model.trim="form.firstName" /></div>
      <div><label>Nachname</label><input class="input" v-model.trim="form.lastName" /></div>
      <div><label>E-Mail</label><input class="input" v-model.trim="form.email" type="email" /></div>
      <button class="btn" @click="savePerson" :disabled="submitting">Person anlegen</button>
    </div>

    <p v-if="formError" class="error">{{ formError }}</p>
    <div v-if="createdPersonId" class="success-box">
      <p>Person wurde erfolgreich angelegt.</p>
      <RouterLink class="btn" :to="`/persons/${createdPersonId}`">Zum Personen-Hub</RouterLink>
    </div>
  </section>
</template>

<script setup lang="ts">
import axios from 'axios'
import { reactive, ref } from 'vue'
import { apiClient } from '../api/client'

const submitting = ref(false)
const formError = ref<string | null>(null)
const createdPersonId = ref<string | null>(null)
const form = reactive({ firstName: '', lastName: '', email: '' })

async function savePerson() {
  formError.value = null
  createdPersonId.value = null

  if (!form.firstName || !form.lastName) {
    formError.value = 'Vorname und Nachname sind Pflichtfelder.'
    return
  }

  submitting.value = true
  try {
    const person = await apiClient.createPerson({
      first_name: form.firstName,
      last_name: form.lastName,
      email: form.email || undefined
    })
    createdPersonId.value = person.person_id
    form.firstName = ''
    form.lastName = ''
    form.email = ''
  } catch (e) {
    if (axios.isAxiosError(e)) {
      formError.value = e.response?.data?.detail ?? 'Person konnte nicht angelegt werden.'
      return
    }
    formError.value = e instanceof Error ? e.message : 'Person konnte nicht angelegt werden.'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.success-box {
  margin-top: 1rem;
  padding: 0.75rem;
  border-radius: 8px;
  background: #ecfdf3;
  border: 1px solid #86efac;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.success-box p {
  margin: 0;
  color: #166534;
}
</style>
