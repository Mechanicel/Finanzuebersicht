<template>
  <section class="card">
    <div class="view-header">
      <div class="view-header-copy">
        <p class="eyebrow">Konten · Detailansicht</p>
        <h2>Konto bearbeiten</h2>
        <p v-if="account">{{ account.label }} · {{ accountTypeLabels[account.account_type] }}</p>
      </div>
      <button class="btn flow-btn" type="button" @click="goBack">← Zurück zur Kontenliste</button>
    </div>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="errorMessage" :message="errorMessage" />

    <article v-else-if="account" class="accounts-card">
      <p v-if="feedbackMessage" :class="feedbackType">{{ feedbackMessage }}</p>
      <form class="account-form" @submit.prevent="submitEdit">
        <AccountFormFields v-model="editForm" :bank-options="bankOptions" />
        <p v-if="editError" class="error">{{ editError }}</p>

        <div class="edit-actions">
          <button class="btn" type="submit" :disabled="submitting">Speichern</button>
          <button class="btn secondary" type="button" @click="resetForm" :disabled="submitting">Zurücksetzen</button>
          <button class="btn secondary" type="button" @click="requestDelete" :disabled="submitting">Löschen</button>
        </div>
      </form>

      <DepotHoldingsManager
        v-if="account.account_type === 'depot'"
        :person-id="personId"
        :depot-label="account.label"
        :title="`Depot-Positionen für ${account.label}`"
      />
    </article>

    <div v-if="deleteCandidate" class="confirm-overlay" role="dialog" aria-modal="true">
      <article class="confirm-dialog">
        <h3>Konto löschen?</h3>
        <p>Soll das Konto <strong>{{ deleteCandidate.label }}</strong> wirklich gelöscht werden?</p>
        <div class="edit-actions">
          <button class="btn" type="button" @click="confirmDelete" :disabled="submitting">Löschen bestätigen</button>
          <button class="btn secondary" type="button" @click="deleteCandidate = null" :disabled="submitting">Abbrechen</button>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '@/shared/api/client'
import AccountFormFields from '@/modules/accounts/components/AccountFormFields.vue'
import LoadingState from '@/shared/ui/LoadingState.vue'
import ErrorState from '@/shared/ui/ErrorState.vue'
import DepotHoldingsManager from '@/modules/accounts/components/DepotHoldingsManager.vue'
import type { AccountFormState } from '@/modules/accounts/model/accountForm'
import { accountTypeLabels, createEmptyAccountForm, createFormFromAccount, toUpdatePayload } from '@/modules/accounts/model/accountForm'
import { extractApiErrorMessage } from '@/shared/api/extractApiErrorMessage'
import type { AccountReadModel, BankReadModel } from '@/shared/model/types'

const route = useRoute()
const router = useRouter()

const personId = computed(() => (typeof route.query.personId === 'string' ? route.query.personId : ''))
const accountId = computed(() => (typeof route.params.accountId === 'string' ? route.params.accountId : ''))

const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref<string | null>(null)
const feedbackMessage = ref('')
const feedbackType = ref<'success' | 'error'>('success')
const editError = ref('')
const account = ref<AccountReadModel | null>(null)
const banks = ref<BankReadModel[]>([])
const assignedBankIds = ref<string[]>([])
const editForm = ref<AccountFormState>(createEmptyAccountForm())
const deleteCandidate = ref<AccountReadModel | null>(null)

const bankById = computed(() => new Map(banks.value.map((bank) => [bank.bank_id, bank])))
const bankOptions = computed(() =>
  assignedBankIds.value
    .map((bankId) => bankById.value.get(bankId))
    .filter((bank): bank is BankReadModel => Boolean(bank))
)

function goBack() {
  if (!personId.value) {
    void router.push('/persons/select')
    return
  }
  void router.push(`/accounts/manage?personId=${personId.value}`)
}

function showFeedback(type: 'success' | 'error', message: string) {
  feedbackType.value = type
  feedbackMessage.value = message
}

function validateForm(form: AccountFormState): string | null {
  if (!form.label.trim()) return 'Bitte gib eine Bezeichnung für das Konto an.'
  if (!form.bank_id) return 'Bitte wähle eine Bank aus.'
  if (!form.balance.trim()) return 'Bitte gib einen Saldo an.'
  if (!form.currency.trim()) return 'Bitte gib eine Währung an.'
  return null
}

function resetForm() {
  if (!account.value) return
  editForm.value = createFormFromAccount(account.value)
  editError.value = ''
}

async function loadData() {
  if (!personId.value || !accountId.value) {
    errorMessage.value = 'Konto-Kontext fehlt.'
    return
  }

  loading.value = true
  errorMessage.value = null
  feedbackMessage.value = ''

  try {
    const [accountList, assignmentResult, bankResult] = await Promise.all([
      apiClient.accounts(personId.value),
      apiClient.personBanks(personId.value),
      apiClient.banks()
    ])
    const selected = accountList.find((item) => item.account_id === accountId.value)
    if (!selected) {
      errorMessage.value = 'Das angefragte Konto wurde nicht gefunden.'
      account.value = null
      return
    }
    account.value = selected
    editForm.value = createFormFromAccount(selected)
    assignedBankIds.value = assignmentResult.items.map((item) => item.bank_id)
    banks.value = bankResult.items
  } catch (e) {
    errorMessage.value = extractApiErrorMessage(e, 'Kontodaten konnten nicht geladen werden.')
  } finally {
    loading.value = false
  }
}

async function submitEdit() {
  if (!personId.value || !accountId.value) return
  const validationError = validateForm(editForm.value)
  if (validationError) {
    editError.value = validationError
    return
  }

  submitting.value = true
  editError.value = ''
  try {
    await apiClient.updateAccount(personId.value, accountId.value, toUpdatePayload(editForm.value))
    showFeedback('success', 'Konto wurde erfolgreich aktualisiert.')
    await loadData()
  } catch (e) {
    editError.value = extractApiErrorMessage(e, 'Konto konnte nicht aktualisiert werden.')
  } finally {
    submitting.value = false
  }
}

function requestDelete() {
  if (account.value) {
    deleteCandidate.value = account.value
  }
}

async function confirmDelete() {
  if (!personId.value || !account.value) return
  submitting.value = true
  try {
    await apiClient.deleteAccount(personId.value, account.value.account_id)
    goBack()
  } catch (e) {
    showFeedback('error', extractApiErrorMessage(e, 'Konto konnte nicht gelöscht werden.'))
  } finally {
    deleteCandidate.value = null
    submitting.value = false
  }
}

watch(() => [personId.value, accountId.value], loadData)
onMounted(loadData)
</script>

<style scoped>
.eyebrow { margin: 0; color: #475569; font-weight: 600; }
.accounts-card { border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem; }
.account-form { display: grid; gap: .75rem; }
.edit-actions { display: flex; flex-wrap: wrap; gap: .5rem; }
.confirm-overlay { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.45); display: grid; place-items: center; padding: 1rem; }
.confirm-dialog { background: #fff; border-radius: 10px; border: 1px solid #e2e8f0; max-width: 520px; width: 100%; padding: 1rem; }
</style>
