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

      <template v-else>
        <p v-if="feedbackMessage" :class="feedbackType">{{ feedbackMessage }}</p>

        <article class="accounts-card">
          <h3>Neues Konto anlegen</h3>
          <p v-if="bankOptions.length === 0" class="empty-hint">
            Für diese Person ist aktuell keine Bank zugeordnet. Lege zuerst im Schritt „Bankzuordnung" eine
            Zuordnung an.
          </p>
          <form v-else class="account-form" @submit.prevent="submitCreate">
            <AccountFormFields :form="createForm" :bank-options="bankOptions" />
            <p v-if="createError" class="error">{{ createError }}</p>
            <button class="btn" type="submit" :disabled="submitting">Konto anlegen</button>
          </form>
        </article>

        <article class="accounts-card">
          <h3>Konten der Person</h3>
          <EmptyState v-if="accounts.length === 0">Für diese Person sind aktuell keine Konten vorhanden.</EmptyState>
          <div v-else class="account-list">
            <section v-for="account in accounts" :key="account.account_id" class="account-item">
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
                <div><dt>Deponummer</dt><dd>{{ account.depot_number || '—' }}</dd></div>
                <div><dt>Eröffnungsdatum</dt><dd>{{ account.opening_date || '—' }}</dd></div>
                <div><dt>Zinssatz</dt><dd>{{ account.interest_rate || '—' }}</dd></div>
              </dl>

              <form v-else class="account-form edit-form" @submit.prevent="submitEdit(account.account_id)">
                <AccountFormFields :form="editForm" :bank-options="bankOptions" />
                <p v-if="editError" class="error">{{ editError }}</p>
                <div class="edit-actions">
                  <button class="btn" type="submit" :disabled="submitting">Speichern</button>
                  <button class="btn secondary" type="button" @click="cancelEdit" :disabled="submitting">
                    Abbrechen
                  </button>
                </div>
              </form>
            </section>
          </div>
        </article>
      </template>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, defineComponent, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient } from '../api/client'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import LoadingState from '../components/LoadingState.vue'
import type { AccountFormState } from './accountForm'
import {
  accountTypeLabels,
  createEmptyAccountForm,
  createFormFromAccount,
  toCreatePayload,
  toUpdatePayload,
  visibleFieldsForAccountType
} from './accountForm'
import { extractApiErrorMessage } from './apiErrorMessage'
import type { AccountReadModel, BankReadModel, PersonReadModel } from '../types/models'

const route = useRoute()
const personId = computed(() => (typeof route.query.personId === 'string' ? route.query.personId : ''))
const backTarget = computed(() => (personId.value ? `/persons/${personId.value}` : '/persons/select'))
const backLabel = computed(() => (personId.value ? 'Zurück zum Personen-Hub' : 'Zur Personenliste'))

const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref<string | null>(null)
const feedbackMessage = ref('')
const feedbackType = ref<'success' | 'error'>('success')
const createError = ref('')
const editError = ref('')
const person = ref<PersonReadModel | null>(null)
const accounts = ref<AccountReadModel[]>([])
const banks = ref<BankReadModel[]>([])
const assignedBankIds = ref<string[]>([])
const createForm = ref<AccountFormState>(createEmptyAccountForm())
const editForm = ref<AccountFormState>(createEmptyAccountForm())
const editAccountId = ref('')

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

function bankName(bankId: string): string {
  return bankById.value.get(bankId)?.name ?? `Unbekannte Bank (${bankId})`
}

function showFeedback(type: 'success' | 'error', message: string) {
  feedbackType.value = type
  feedbackMessage.value = message
}

function resetCreateForm() {
  const defaultBankId = bankOptions.value[0]?.bank_id ?? ''
  createForm.value = createEmptyAccountForm(defaultBankId)
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
    resetCreateForm()
    return
  }

  loading.value = true
  errorMessage.value = null
  feedbackMessage.value = ''
  createError.value = ''
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
    resetCreateForm()
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
  editError.value = ''

  try {
    await apiClient.createAccount(personId.value, toCreatePayload(createForm.value))
    showFeedback('success', 'Konto wurde erfolgreich angelegt.')
    await loadData()
  } catch (e) {
    createError.value = extractApiErrorMessage(e, 'Konto konnte nicht angelegt werden.')
  } finally {
    submitting.value = false
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
  createError.value = ''

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

const AccountFormFields = defineComponent({
  name: 'AccountFormFields',
  props: {
    form: { type: Object as () => AccountFormState, required: true },
    bankOptions: { type: Array as () => BankReadModel[], required: true }
  },
  setup(props) {
    const visibleFields = computed(() => new Set(visibleFieldsForAccountType(props.form.account_type)))
    return { accountTypeLabels, visibleFields }
  },
  template: `
    <div class="grid form-grid">
      <div>
        <label>Kontotyp</label>
        <select class="input" v-model="form.account_type">
          <option value="girokonto">{{ accountTypeLabels.girokonto }}</option>
          <option value="tagesgeldkonto">{{ accountTypeLabels.tagesgeldkonto }}</option>
          <option value="festgeldkonto">{{ accountTypeLabels.festgeldkonto }}</option>
          <option value="depot">{{ accountTypeLabels.depot }}</option>
        </select>
      </div>
      <div>
        <label>Bezeichnung</label>
        <input class="input" v-model="form.label" maxlength="120" placeholder="z. B. Giro Hauptkonto" />
      </div>
      <div>
        <label>Bank</label>
        <select class="input" v-model="form.bank_id">
          <option value="">Bitte auswählen</option>
          <option v-for="bank in bankOptions" :key="bank.bank_id" :value="bank.bank_id">
            {{ bank.name }} ({{ bank.bic }})
          </option>
        </select>
      </div>
      <div>
        <label>Saldo</label>
        <input class="input" v-model="form.balance" inputmode="decimal" placeholder="0.00" />
      </div>
      <div>
        <label>Währung</label>
        <input class="input" v-model="form.currency" maxlength="3" placeholder="EUR" />
      </div>

      <div v-if="visibleFields.has('account_number')">
        <label>Kontonummer</label>
        <input class="input" v-model="form.account_number" />
      </div>
      <div v-if="visibleFields.has('depot_number')">
        <label>Deponummer</label>
        <input class="input" v-model="form.depot_number" />
      </div>
      <div v-if="visibleFields.has('iban')">
        <label>IBAN</label>
        <input class="input" v-model="form.iban" />
      </div>
      <div v-if="visibleFields.has('opening_date')">
        <label>Eröffnungsdatum</label>
        <input class="input" v-model="form.opening_date" type="date" />
      </div>
      <div v-if="visibleFields.has('interest_rate')">
        <label>Zinssatz</label>
        <input class="input" v-model="form.interest_rate" inputmode="decimal" placeholder="z. B. 2.1500" />
      </div>
      <div v-if="visibleFields.has('payout_account_iban')">
        <label>Auszahlungskonto-IBAN</label>
        <input class="input" v-model="form.payout_account_iban" />
      </div>
      <div v-if="visibleFields.has('settlement_account_iban')">
        <label>Verrechnungskonto-IBAN</label>
        <input class="input" v-model="form.settlement_account_iban" />
      </div>
    </div>
  `
})

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

.form-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
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
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}

.account-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.5rem;
  margin: 0;
}

.account-details div {
  margin: 0;
}

.account-details dt {
  font-size: 0.8rem;
  color: #64748b;
}

.account-details dd {
  margin: 0.1rem 0 0;
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

.empty-hint {
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 0.65rem 0.75rem;
}

.edit-actions {
  display: flex;
  gap: 0.5rem;
}

.secondary {
  background: #334155;
}
</style>
