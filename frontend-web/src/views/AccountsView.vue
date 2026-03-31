<template>
  <section class="card">
    <div class="view-header">
      <div class="view-header-copy">
        <p class="eyebrow">Personen-Hub · Schritt</p>
        <h2>Konten ansehen & bearbeiten</h2>
        <p v-if="personId">{{ subtitle }}</p>
        <p v-else>Diese Ansicht ist nur aus dem Personen-Hub sinnvoll nutzbar.</p>
      </div>
      <RouterLink class="btn flow-btn" :to="backTarget">{{ backLabel }}</RouterLink>
    </div>

    <p v-if="!personId" class="context-hint">
      Kein Personenkontext vorhanden. Bitte wähle zuerst eine Person aus und öffne danach den Schritt
      „Konten ansehen & bearbeiten“ im Personen-Hub.
    </p>

    <template v-else>
      <LoadingState v-if="loading" />
      <ErrorState v-else-if="errorMessage" :message="errorMessage" />

      <article v-else class="accounts-card">
        <p v-if="feedbackMessage" :class="feedbackType">{{ feedbackMessage }}</p>
        <h3>Konten der Person</h3>

        <div class="search-row">
          <label for="account-search">Konten suchen</label>
          <input
            id="account-search"
            v-model.trim="searchQuery"
            class="input"
            type="search"
            placeholder="Suche nach Label, Typ, IBAN, Konto-/Depotnummer"
          />
        </div>

        <EmptyState v-if="accounts.length === 0">Für diese Person sind aktuell keine Konten vorhanden.</EmptyState>
        <EmptyState v-else-if="filteredAccounts.length === 0">Keine Konten für die aktuelle Suche gefunden.</EmptyState>
        <div v-else class="account-list">
          <section v-for="account in filteredAccounts" :key="account.account_id" class="account-item">
            <div class="account-item-header">
              <div>
                <strong>{{ account.label }}</strong>
                <p class="muted">{{ accountTypeLabels[account.account_type] }} · {{ bankName(account.bank_id) }}</p>
              </div>
              <button
                v-if="editAccountId !== account.account_id"
                class="btn secondary"
                type="button"
                @click="startEdit(account)"
                :disabled="submitting"
              >
                Bearbeiten
              </button>
            </div>

            <dl v-if="editAccountId !== account.account_id" class="account-details">
              <div><dt>Saldo</dt><dd>{{ account.balance }} {{ account.currency }}</dd></div>
              <div><dt>IBAN</dt><dd>{{ account.iban || '—' }}</dd></div>
              <div><dt>Kontonummer</dt><dd>{{ account.account_number || '—' }}</dd></div>
              <div><dt>Depotnummer</dt><dd>{{ account.depot_number || '—' }}</dd></div>
              <div><dt>Eröffnungsdatum</dt><dd>{{ account.opening_date || '—' }}</dd></div>
              <div><dt>Zinssatz</dt><dd>{{ account.interest_rate || '—' }}</dd></div>
            </dl>

            <form v-else class="account-form edit-form" @submit.prevent="submitEdit(account.account_id)">
              <AccountFormFields v-model="editForm" :bank-options="bankOptions" />
              <p v-if="editError" class="error">{{ editError }}</p>

              <div class="edit-actions">
                <button class="btn" type="submit" :disabled="submitting">Speichern</button>
                <button class="btn secondary" type="button" @click="cancelEdit" :disabled="submitting">
                  Abbrechen
                </button>
                <button class="btn secondary" type="button" @click="requestDelete(account)">
                  Löschen
                </button>
                <button
                  v-if="account.account_type === 'depot'"
                  class="btn secondary"
                  type="button"
                  @click="openDepotHoldings(account)"
                >
                  Depot-Positionen öffnen
                </button>
              </div>
            </form>
          </section>
        </div>
      </article>
    </template>

    <div v-if="deleteCandidate" class="confirm-overlay" role="dialog" aria-modal="true">
      <article class="confirm-dialog">
        <h3>Konto löschen?</h3>
        <p>
          Soll das Konto <strong>{{ deleteCandidate.label }}</strong> wirklich gelöscht werden?
          Dieser Schritt kann nicht rückgängig gemacht werden.
        </p>
        <p v-if="deleteCandidate.account_type === 'depot'" class="muted">
          Hinweis: Falls ein gleichnamiges Portfolio existiert, bleiben dessen Holdings unverändert.
        </p>
        <div class="edit-actions">
          <button class="btn" type="button" @click="confirmDelete" :disabled="submitting">Löschen bestätigen</button>
          <button class="btn secondary" type="button" @click="cancelDelete" :disabled="submitting">Abbrechen</button>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '../api/client'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import LoadingState from '../components/LoadingState.vue'
import AccountFormFields from './AccountFormFields.vue'
import type { AccountFormState } from './accountForm'
import { accountTypeLabels, createEmptyAccountForm, createFormFromAccount, toUpdatePayload } from './accountForm'
import { extractApiErrorMessage } from './apiErrorMessage'
import type { AccountReadModel, BankReadModel, PersonReadModel } from '../types/models'

const route = useRoute()
const router = useRouter()
const personId = computed(() => (typeof route.query.personId === 'string' ? route.query.personId : ''))
const backTarget = computed(() => (personId.value ? `/persons/${personId.value}` : '/persons/select'))
const backLabel = computed(() => (personId.value ? 'Zurück zum Personen-Hub' : 'Zur Personenliste'))

const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref<string | null>(null)
const feedbackMessage = ref('')
const feedbackType = ref<'success' | 'error'>('success')
const editError = ref('')
const searchQuery = ref('')
const person = ref<PersonReadModel | null>(null)
const accounts = ref<AccountReadModel[]>([])
const banks = ref<BankReadModel[]>([])
const assignedBankIds = ref<string[]>([])
const editForm = ref<AccountFormState>(createEmptyAccountForm())
const editAccountId = ref('')
const deleteCandidate = ref<AccountReadModel | null>(null)

const subtitle = computed(() => {
  const fullName = `${person.value?.first_name ?? ''} ${person.value?.last_name ?? ''}`.trim()
  if (fullName) {
    return `Kontenübersicht für ${fullName}`
  }
  return 'Kontenübersicht für die ausgewählte Person'
})

const bankById = computed(() => new Map(banks.value.map((bank) => [bank.bank_id, bank])))
const bankOptions = computed(() =>
  assignedBankIds.value
    .map((bankId) => bankById.value.get(bankId))
    .filter((bank): bank is BankReadModel => Boolean(bank))
)

const filteredAccounts = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) {
    return accounts.value
  }

  return accounts.value.filter((account) => {
    const searchable = [
      account.label,
      accountTypeLabels[account.account_type],
      account.account_type,
      account.iban ?? '',
      account.account_number ?? '',
      account.depot_number ?? ''
    ]
      .join(' ')
      .toLowerCase()

    return searchable.includes(query)
  })
})

function bankName(bankId: string): string {
  return bankById.value.get(bankId)?.name ?? `Unbekannte Bank (${bankId})`
}

function showFeedback(type: 'success' | 'error', message: string) {
  feedbackType.value = type
  feedbackMessage.value = message
}

function startEdit(account: AccountReadModel) {
  editAccountId.value = account.account_id
  editForm.value = createFormFromAccount(account)
  editError.value = ''
  feedbackMessage.value = ''
}

function cancelEdit() {
  editAccountId.value = ''
  editForm.value = createEmptyAccountForm(bankOptions.value[0]?.bank_id ?? '')
  editError.value = ''
}

function requestDelete(account: AccountReadModel) {
  deleteCandidate.value = account
}

function cancelDelete() {
  deleteCandidate.value = null
}

function openDepotHoldings(account: AccountReadModel) {
  if (!personId.value) {
    return
  }
  void router.push(`/accounts/depot-holdings?personId=${personId.value}&depotLabel=${encodeURIComponent(account.label)}&origin=manage`)
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
    accounts.value = []
    errorMessage.value = null
    banks.value = []
    assignedBankIds.value = []
    return
  }

  loading.value = true
  errorMessage.value = null
  feedbackMessage.value = ''
  editError.value = ''

  try {
    const [personDetail, accountList, assignmentResult, bankResult] = await Promise.all([
      apiClient.person(personId.value),
      apiClient.accounts(personId.value),
      apiClient.personBanks(personId.value),
      apiClient.banks()
    ])
    person.value = personDetail.person
    accounts.value = accountList
    assignedBankIds.value = assignmentResult.items.map((item) => item.bank_id)
    banks.value = bankResult.items
    if (editAccountId.value) {
      const edited = accounts.value.find((item) => item.account_id === editAccountId.value)
      if (edited) {
        editForm.value = createFormFromAccount(edited)
      } else {
        cancelEdit()
      }
    }
  } catch (e) {
    errorMessage.value = extractApiErrorMessage(e, 'Konten konnten nicht geladen werden.')
  } finally {
    loading.value = false
  }
}

async function submitEdit(accountId: string) {
  if (!personId.value) {
    return
  }

  const validationError = validateForm(editForm.value)
  if (validationError) {
    editError.value = validationError
    return
  }

  submitting.value = true
  editError.value = ''

  try {
    await apiClient.updateAccount(personId.value, accountId, toUpdatePayload(editForm.value))
    showFeedback('success', 'Konto wurde erfolgreich aktualisiert.')
    editAccountId.value = ''
    await loadData()
  } catch (e) {
    editError.value = extractApiErrorMessage(e, 'Konto konnte nicht aktualisiert werden.')
  } finally {
    submitting.value = false
  }
}

async function confirmDelete() {
  if (!personId.value || !deleteCandidate.value) {
    return
  }

  submitting.value = true
  try {
    await apiClient.deleteAccount(personId.value, deleteCandidate.value.account_id)
    showFeedback('success', 'Konto wurde gelöscht.')
    if (editAccountId.value === deleteCandidate.value.account_id) {
      cancelEdit()
    }
    deleteCandidate.value = null
    await loadData()
  } catch (e) {
    showFeedback('error', extractApiErrorMessage(e, 'Konto konnte nicht gelöscht werden.'))
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

.search-row {
  display: grid;
  gap: 0.4rem;
  margin-bottom: 1rem;
}

.account-form {
  display: grid;
  gap: 0.75rem;
}

.account-list {
  display: grid;
  gap: 0.75rem;
}

.account-item {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem;
}

.account-item-header {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: flex-start;
}

.account-item-header p {
  margin: 0.35rem 0 0;
}

.account-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.5rem;
  margin: 0.75rem 0 0;
}

.account-details div {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.5rem;
  background: #f8fafc;
}

.account-details dt {
  font-size: 0.8rem;
  color: #64748b;
}

.edit-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: grid;
  place-items: center;
  padding: 1rem;
}

.confirm-dialog {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  max-width: 520px;
  width: 100%;
  padding: 1rem;
}

.confirm-dialog h3 {
  margin-top: 0;
}
</style>
