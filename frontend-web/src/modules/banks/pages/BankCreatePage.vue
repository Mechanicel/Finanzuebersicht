<template>
  <section class="card">
    <div class="view-header">
      <div class="view-header-copy">
        <h2>Neue Bank anlegen</h2>
        <p>Erfasse die Stammdaten der Bank. Nach dem Speichern steht die Bank sofort im System zur Verfügung.</p>
      </div>
      <RouterLink class="btn flow-btn" to="/">Zur Startseite</RouterLink>
    </div>

    <form class="grid form-grid" @submit.prevent="submit">
      <div>
        <label for="bank-name">Bankname</label>
        <input id="bank-name" class="input" v-model.trim="form.name" :disabled="isSubmitting" />
        <p v-if="errors.name" class="error-text">{{ errors.name }}</p>
      </div>

      <div>
        <label for="bank-bic">BIC</label>
        <input
          id="bank-bic"
          class="input"
          v-model.trim="form.bic"
          :disabled="isSubmitting"
          placeholder="DEUTDEFFXXX"
          style="text-transform: uppercase"
        />
        <p v-if="errors.bic" class="error-text">{{ errors.bic }}</p>
      </div>

      <div>
        <label for="bank-blz">BLZ</label>
        <input
          id="bank-blz"
          class="input"
          v-model.trim="form.blz"
          :disabled="isSubmitting"
          inputmode="numeric"
          placeholder="12345678"
        />
        <p v-if="errors.blz" class="error-text">{{ errors.blz }}</p>
      </div>

      <div>
        <label for="bank-country">Ländercode</label>
        <input
          id="bank-country"
          class="input"
          v-model.trim="form.country_code"
          :disabled="isSubmitting"
          placeholder="DE"
          maxlength="2"
          style="text-transform: uppercase"
        />
        <p v-if="errors.country_code" class="error-text">{{ errors.country_code }}</p>
      </div>

      <div class="actions">
        <button class="btn" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? 'Speichert…' : 'Bank anlegen' }}
        </button>
        <button class="btn secondary" type="button" :disabled="isSubmitting" @click="goHome">
          Zur Startseite
        </button>
      </div>
    </form>

    <p v-if="successMessage" class="success" role="status">{{ successMessage }}</p>
    <p v-if="errorMessage" class="error" role="alert">{{ errorMessage }}</p>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

import { apiClient } from '@/shared/api/client'
import type { BankCreatePayload } from '@/shared/model/types'

const router = useRouter()

const form = reactive<BankCreatePayload>({
  name: '',
  bic: '',
  blz: '',
  country_code: 'DE'
})

const errors = reactive<Record<string, string>>({})
const errorMessage = ref('')
const successMessage = ref('')
const isSubmitting = ref(false)

const bicPattern = /^[A-Z0-9]{8}([A-Z0-9]{3})?$/
const blzPattern = /^[0-9]{8}$/
const countryPattern = /^[A-Z]{2}$/

function clearMessages() {
  errorMessage.value = ''
  successMessage.value = ''
}

function clearFieldErrors() {
  Object.keys(errors).forEach((key) => delete errors[key])
}

function validateForm(): boolean {
  clearFieldErrors()

  form.bic = form.bic.toUpperCase()
  form.country_code = form.country_code.toUpperCase()

  if (!form.name) errors.name = 'Bitte einen Banknamen eingeben.'
  if (!bicPattern.test(form.bic)) errors.bic = 'Die BIC muss 8 oder 11 Zeichen lang sein.'
  if (!blzPattern.test(form.blz)) errors.blz = 'Die BLZ muss aus genau 8 Ziffern bestehen.'
  if (!countryPattern.test(form.country_code)) errors.country_code = 'Bitte einen zweistelligen Ländercode eingeben.'

  return Object.keys(errors).length === 0
}

function readableBackendError(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return 'Bitte prüfe die Eingaben und korrigiere die markierten Felder.'
  return 'Die Bank konnte nicht angelegt werden. Bitte versuche es erneut.'
}

async function submit() {
  clearMessages()
  if (!validateForm()) {
    errorMessage.value = 'Bitte korrigiere die Eingaben.'
    return
  }

  isSubmitting.value = true
  try {
    const created = await apiClient.createBank(form)
    successMessage.value = `Bank ${created.name} wurde erfolgreich angelegt.`
    form.name = ''
    form.bic = ''
    form.blz = ''
    form.country_code = 'DE'
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const detail = error.response?.data?.detail
      errorMessage.value = readableBackendError(detail)
    } else {
      errorMessage.value = 'Die Bank konnte nicht angelegt werden. Bitte versuche es erneut.'
    }
  } finally {
    isSubmitting.value = false
  }
}

function goHome() {
  void router.push('/')
}
</script>

<style scoped>
.form-grid {
  margin-top: 0.25rem;
}

.actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.error-text {
  margin: 0.25rem 0 0;
  font-size: 0.85rem;
  color: #b91c1c;
}

.success {
  margin-top: 1rem;
  color: #166534;
}
</style>
