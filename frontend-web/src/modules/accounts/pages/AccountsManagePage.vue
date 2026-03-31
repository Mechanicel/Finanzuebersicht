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
          <button
            v-for="account in filteredAccounts"
            :key="account.account_id"
            class="account-row-btn"
            type="button"
            @click="openDetails(account.account_id)"
          >
            <section class="account-item">
              <div class="account-item-header">
                <div>
                  <strong>{{ account.label }}</strong>
                  <p class="muted">{{ accountTypeLabels[account.account_type] }} · {{ bankName(account.bank_id) }}</p>
                </div>
                <span class="row-action-hint" aria-hidden="true">→</span>
              </div>
              <dl class="account-details">
                <div><dt>Saldo</dt><dd>{{ account.balance }} {{ account.currency }}</dd></div>
                <div><dt>IBAN</dt><dd>{{ account.iban || '—' }}</dd></div>
                <div><dt>Kontonummer</dt><dd>{{ account.account_number || '—' }}</dd></div>
                <div><dt>Depotnummer</dt><dd>{{ account.depot_number || '—' }}</dd></div>
              </dl>
            </section>
          </button>
        </div>
      </article>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '@/shared/api/client'
import EmptyState from '@/shared/ui/EmptyState.vue'
import ErrorState from '@/shared/ui/ErrorState.vue'
import LoadingState from '@/shared/ui/LoadingState.vue'
import { accountTypeLabels } from '@/modules/accounts/model/accountForm'
import { extractApiErrorMessage } from '@/shared/api/extractApiErrorMessage'
import type { AccountReadModel, BankReadModel, PersonReadModel } from '@/shared/model/types'

const route = useRoute()
const router = useRouter()
const personId = computed(() => (typeof route.query.personId === 'string' ? route.query.personId : ''))
const backTarget = computed(() => (personId.value ? `/persons/${personId.value}` : '/persons/select'))
const backLabel = computed(() => (personId.value ? 'Zurück zum Personen-Hub' : 'Zur Personenliste'))

const loading = ref(false)
const errorMessage = ref<string | null>(null)
const searchQuery = ref('')
const person = ref<PersonReadModel | null>(null)
const accounts = ref<AccountReadModel[]>([])
const banks = ref<BankReadModel[]>([])

const subtitle = computed(() => {
  const fullName = `${person.value?.first_name ?? ''} ${person.value?.last_name ?? ''}`.trim()
  if (fullName) {
    return `Kontenübersicht für ${fullName}`
  }
  return 'Kontenübersicht für die ausgewählte Person'
})

const bankById = computed(() => new Map(banks.value.map((bank) => [bank.bank_id, bank])))
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

function openDetails(accountId: string) {
  if (!personId.value) return
  void router.push(`/accounts/manage/${accountId}?personId=${personId.value}`)
}

async function loadData() {
  if (!personId.value) {
    person.value = null
    accounts.value = []
    errorMessage.value = null
    banks.value = []
    return
  }

  loading.value = true
  errorMessage.value = null

  try {
    const [personDetail, accountList, bankResult] = await Promise.all([
      apiClient.person(personId.value),
      apiClient.accounts(personId.value),
      apiClient.banks()
    ])
    person.value = personDetail.person
    accounts.value = accountList
    banks.value = bankResult.items
  } catch (e) {
    errorMessage.value = extractApiErrorMessage(e, 'Konten konnten nicht geladen werden.')
  } finally {
    loading.value = false
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
  width: 100%;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem;
  text-align: left;
}

.account-row-btn {
  border: none;
  padding: 0;
  background: transparent;
  border-radius: 8px;
}

.account-row-btn:focus-visible .account-item,
.account-row-btn:hover .account-item {
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
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

.row-action-hint {
  color: #1d4ed8;
  font-weight: 600;
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

</style>
