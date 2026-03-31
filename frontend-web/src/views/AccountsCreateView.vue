<template>
  <section class="card">
    <div class="view-header">
      <div class="view-header-copy">
        <p class="eyebrow">Personen-Hub · Schritt</p>
        <h2>Konto hinzufügen</h2>
        <p v-if="personId">{{ subtitle }}</p>
        <p v-else>Diese Ansicht ist nur aus dem Personen-Hub sinnvoll nutzbar.</p>
      </div>
      <RouterLink class="btn flow-btn" :to="backTarget">{{ backLabel }}</RouterLink>
    </div>

    <p v-if="!personId" class="context-hint">
      Kein Personenkontext vorhanden. Bitte wähle zuerst eine Person aus und öffne danach den Schritt
      „Konto hinzufügen“ im Personen-Hub.
    </p>

    <template v-else>
      <LoadingState v-if="loading" />
      <ErrorState v-else-if="errorMessage" :message="errorMessage" />

      <article v-else class="accounts-card">
        <h3>Neues Konto oder Depot anlegen</h3>
        <p class="muted">Wähle als Kontotyp entweder ein normales Konto oder ein Depot.</p>
        <p v-if="bankOptions.length === 0" class="empty-hint">
          Für diese Person ist aktuell keine Bank zugeordnet. Lege zuerst im Schritt „Bankzuordnung" eine
          Zuordnung an.
        </p>
        <form v-else class="account-form" @submit.prevent="submitCreate">
          <AccountFormFields v-model="createForm" :bank-options="bankOptions" />
          <p v-if="createError" class="error">{{ createError }}</p>
          <button class="btn" type="submit" :disabled="submitting">
            {{ createForm.account_type === 'depot' ? 'Depot anlegen & weiter zu Positionen' : 'Konto anlegen' }}
          </button>
        </form>
      </article>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '../api/client'
import ErrorState from '../components/ErrorState.vue'
import LoadingState from '../components/LoadingState.vue'
import AccountFormFields from './AccountFormFields.vue'
import type { AccountFormState } from './accountForm'
import { createEmptyAccountForm, toCreatePayload } from './accountForm'
import { extractApiErrorMessage } from './apiErrorMessage'
import type { BankReadModel, PersonReadModel } from '../types/models'

const route = useRoute()
const router = useRouter()
const personId = computed(() => (typeof route.query.personId === 'string' ? route.query.personId : ''))
const backTarget = computed(() => (personId.value ? `/persons/${personId.value}` : '/persons/select'))
const backLabel = computed(() => (personId.value ? 'Zurück zum Personen-Hub' : 'Zur Personenliste'))

const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref<string | null>(null)
const createError = ref('')
const person = ref<PersonReadModel | null>(null)
const banks = ref<BankReadModel[]>([])
const assignedBankIds = ref<string[]>([])
const createForm = ref<AccountFormState>(createEmptyAccountForm())

const subtitle = computed(() => {
  const fullName = `${person.value?.first_name ?? ''} ${person.value?.last_name ?? ''}`.trim()
  if (fullName) {
    return `Konto-Anlage für ${fullName}`
  }
  return 'Konto-Anlage für die ausgewählte Person'
})

const bankById = computed(() => new Map(banks.value.map((bank) => [bank.bank_id, bank])))
const bankOptions = computed(() =>
  assignedBankIds.value
    .map((bankId) => bankById.value.get(bankId))
    .filter((bank): bank is BankReadModel => Boolean(bank))
)

function resetCreateForm() {
  const defaultBankId = bankOptions.value[0]?.bank_id ?? ''
  createForm.value = createEmptyAccountForm(defaultBankId)
}

function validateForm(form: AccountFormState): string | null {
  if (!form.label.trim()) {
    return 'Bitte gib eine Bezeichnung für das Konto an.'
  }
  if (!form.bank_id) {
    return 'Bitte wähle eine Bank aus.'
  }
  if (!form.balance.trim()) {
    return 'Bitte gib einen Saldo an.'
  }
  if (!form.currency.trim()) {
    return 'Bitte gib eine Währung an.'
  }
  return null
}

async function loadData() {
  if (!personId.value) {
    person.value = null
    errorMessage.value = null
    banks.value = []
    assignedBankIds.value = []
    resetCreateForm()
    return
  }

  loading.value = true
  errorMessage.value = null
  createError.value = ''

  try {
    const [personDetail, assignmentResult, bankResult] = await Promise.all([
      apiClient.person(personId.value),
      apiClient.personBanks(personId.value),
      apiClient.banks()
    ])
    person.value = personDetail.person
    assignedBankIds.value = assignmentResult.items.map((item) => item.bank_id)
    banks.value = bankResult.items
    resetCreateForm()
  } catch (e) {
    errorMessage.value = extractApiErrorMessage(e, 'Kontodaten konnten nicht geladen werden.')
  } finally {
    loading.value = false
  }
}

async function submitCreate() {
  if (!personId.value || bankOptions.value.length === 0) {
    return
  }

  const validationError = validateForm(createForm.value)
  if (validationError) {
    createError.value = validationError
    return
  }

  submitting.value = true
  createError.value = ''

  try {
    const savedLabel = createForm.value.label.trim()
    await apiClient.createAccount(personId.value, toCreatePayload(createForm.value))
    if (createForm.value.account_type === 'depot') {
      await router.push(`/accounts/depot-holdings?personId=${personId.value}&depotLabel=${encodeURIComponent(savedLabel)}&origin=create`)
      return
    }
    await router.push(`/persons/${personId.value}`)
  } catch (e) {
    createError.value = extractApiErrorMessage(e, 'Konto konnte nicht angelegt werden.')
  } finally {
    submitting.value = false
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

.accounts-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.accounts-card h3 {
  margin-top: 0;
}

.account-form {
  display: grid;
  gap: 0.75rem;
}
</style>
