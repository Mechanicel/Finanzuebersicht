<template>
  <section class="card">
    <div class="view-header">
      <div class="view-header-copy">
        <h2>Freibetragsverwaltung</h2>
        <p>Verwalte Freibeträge je zugeordneter Bank für die ausgewählte Person.</p>
      </div>
      <RouterLink class="btn flow-btn" :to="backTarget">{{ backLabel }}</RouterLink>
    </div>

    <p v-if="!personId" class="context-hint">
      Diese Ansicht funktioniert nur im Personenkontext. Bitte öffne sie aus dem Personen-Hub.
    </p>

    <template v-else>
      <LoadingState v-if="loading" />
      <ErrorState v-else-if="errorMessage" :message="errorMessage" />

      <template v-else>
        <p v-if="feedbackMessage" :class="feedbackType">{{ feedbackMessage }}</p>

        <article class="assignment-card">
          <div class="assignment-header">
            <h3>Freibeträge pro Bank</h3>
            <div class="year-select">
              <label for="tax-year">Steuerjahr</label>
              <select id="tax-year" class="input" v-model.number="selectedTaxYear">
                <option v-for="year in taxYearOptions" :key="year" :value="year">{{ year }}</option>
              </select>
            </div>
          </div>

          <div class="summary-grid">
            <p class="muted"><strong>Gesamtsumme:</strong> {{ summary.total_amount }} {{ summary.currency }}</p>
            <p class="muted"><strong>Jahreslimit:</strong> {{ summary.annual_limit }} {{ summary.currency }}</p>
            <p class="muted"><strong>Restbetrag:</strong> {{ summary.remaining_amount }} {{ summary.currency }}</p>
          </div>

          <p class="muted" v-if="person?.tax_profile">
            <strong>Steuerprofil:</strong>
            {{ person.tax_profile.tax_country }} / {{ person.tax_profile.filing_status }}
          </p>

          <EmptyState v-if="assignedBanks.length === 0">
            Dieser Person sind noch keine Banken zugeordnet. Bitte zuerst im Schritt „Bankzuordnung“ Banken zuweisen.
          </EmptyState>

          <ul v-else class="allowance-list">
            <li v-for="bank in assignedBanks" :key="bank.bank_id">
              <div>
                <strong>{{ bank.name }}</strong>
                <p class="muted">{{ bank.bic }}</p>
                <p class="muted">Aktuell: {{ currentAmount(bank.bank_id) }} EUR</p>
              </div>
              <div class="allowance-edit">
                <label :for="`allowance-${bank.bank_id}`">Neuer Freibetrag (EUR)</label>
                <input
                  :id="`allowance-${bank.bank_id}`"
                  class="input"
                  type="number"
                  min="0"
                  step="0.01"
                  v-model="formAmounts[bank.bank_id]"
                />
                <button class="btn" :disabled="submitting" @click="saveAllowance(bank.bank_id)">Speichern</button>
              </div>
            </li>
          </ul>
        </article>
      </template>
    </template>
  </section>
</template>

<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient } from '../api/client'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import LoadingState from '../components/LoadingState.vue'
import type {
  AllowanceSummaryReadModel,
  BankReadModel,
  PersonBankAssignmentReadModel,
  PersonReadModel,
  TaxAllowanceReadModel
} from '../types/models'
import { isValidAllowanceAmount, normalizeAllowanceInput } from './allowanceAmount'

const route = useRoute()
const personId = computed(() => (typeof route.query.personId === 'string' ? route.query.personId : ''))
const backTarget = computed(() => (personId.value ? `/persons/${personId.value}` : '/persons/select'))
const backLabel = computed(() => (personId.value ? 'Zurück zum Personen-Hub' : 'Zur Personenliste'))

const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref<string | null>(null)
const feedbackMessage = ref('')
const feedbackType = ref<'success' | 'error'>('success')

const assignments = ref<PersonBankAssignmentReadModel[]>([])
const banks = ref<BankReadModel[]>([])
const person = ref<PersonReadModel | null>(null)
const allowances = ref<TaxAllowanceReadModel[]>([])
const selectedTaxYear = ref(new Date().getFullYear())
const summary = ref<AllowanceSummaryReadModel>({
  person_id: '',
  tax_year: selectedTaxYear.value,
  banks: [],
  total_amount: '0.00',
  annual_limit: '0.00',
  remaining_amount: '0.00',
  currency: 'EUR'
})
const formAmounts = ref<Record<string, string | number | null | undefined>>({})
const taxYearOptions = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = new Set([currentYear - 1, currentYear, currentYear + 1, selectedTaxYear.value])
  return [...years].sort((a, b) => b - a)
})

const assignedBanks = computed(() => {
  const assignedIds = new Set(assignments.value.map((item) => item.bank_id))
  return banks.value.filter((bank) => assignedIds.has(bank.bank_id))
})

function showFeedback(type: 'success' | 'error', message: string) {
  feedbackType.value = type
  feedbackMessage.value = message
}

function currentAmount(bankId: string) {
  return allowances.value.find((item) => item.bank_id === bankId)?.amount ?? '0.00'
}

function initializeFormValues() {
  const nextValues: Record<string, string> = {}
  for (const bank of assignedBanks.value) {
    nextValues[bank.bank_id] = currentAmount(bank.bank_id)
  }
  formAmounts.value = nextValues
}

async function loadData() {
  if (!personId.value) {
    return
  }

  loading.value = true
  errorMessage.value = null
  feedbackMessage.value = ''

  try {
    const [personDetail, personBanks, bankList, allowanceList, allowanceSummary] = await Promise.all([
      apiClient.person(personId.value),
      apiClient.personBanks(personId.value),
      apiClient.banks(),
      apiClient.allowances(personId.value, selectedTaxYear.value),
      apiClient.allowanceSummary(personId.value, selectedTaxYear.value)
    ])
    person.value = personDetail.person
    assignments.value = personBanks.items
    banks.value = bankList.items
    allowances.value = allowanceList.items
    summary.value = allowanceSummary
    initializeFormValues()
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : 'Freibeträge konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function saveAllowance(bankId: string) {
  if (!personId.value) {
    return
  }
  const amount = normalizeAllowanceInput(formAmounts.value[bankId])
  formAmounts.value[bankId] = amount

  if (!isValidAllowanceAmount(amount)) {
    showFeedback('error', 'Bitte einen gültigen Betrag mit maximal zwei Nachkommastellen eingeben.')
    return
  }

  submitting.value = true
  try {
    await apiClient.setAllowance(personId.value, bankId, {
      tax_year: selectedTaxYear.value,
      amount,
      currency: summary.value.currency || 'EUR'
    })
    showFeedback('success', 'Freibetrag wurde gespeichert.')
    await loadData()
  } catch (e) {
    if (axios.isAxiosError(e)) {
      const detail = e.response?.data?.detail
      if (typeof detail === 'string') {
        showFeedback('error', detail)
        return
      }
      if (detail && typeof detail === 'object' && 'message' in detail && typeof detail.message === 'string') {
        showFeedback('error', detail.message)
        return
      }
      if (typeof e.response?.data?.message === 'string') {
        showFeedback('error', e.response.data.message)
        return
      }
      if (e.response?.status === 409) {
        showFeedback('error', 'Freibeträge dürfen nur für bereits zugeordnete Banken gesetzt werden.')
        return
      }
      showFeedback('error', e.message)
      return
    }
    showFeedback('error', e instanceof Error ? e.message : 'Freibetrag konnte nicht gespeichert werden.')
  } finally {
    submitting.value = false
  }
}

onMounted(loadData)
watch(personId, loadData)
watch(selectedTaxYear, loadData)
</script>

<style scoped>
.assignment-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.year-select {
  display: grid;
  gap: 0.25rem;
}

.summary-grid {
  display: grid;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
}

.context-hint {
  margin-top: 0;
  margin-bottom: 0.75rem;
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 0.65rem 0.75rem;
}

.assignment-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem;
}

.allowance-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.75rem;
}

.allowance-list li {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem;
}

.allowance-edit {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.5rem;
  align-items: end;
}

.allowance-edit label {
  grid-column: 1 / -1;
}

.muted {
  margin: 0.25rem 0 0;
  color: #64748b;
  font-size: 0.875rem;
}

.success {
  color: #166534;
}

.error {
  color: #991b1b;
}
</style>
