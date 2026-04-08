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
            @click="openDetails(account)"
          >
            <section class="account-item" :class="{ 'account-item--depot': isDepotAccount(account) }">
              <template v-if="isDepotAccount(account)">
                <div class="account-item-header">
                  <div>
                    <strong>{{ account.label }}</strong>
                    <p class="muted">Depot · {{ bankName(account.bank_id) }}</p>
                  </div>
                  <span class="row-action-hint" aria-hidden="true">→</span>
                </div>
                <p class="depot-account-number">Depotnummer: {{ account.depot_number || '—' }}</p>
                <div class="depot-summary-grid">
                  <article class="summary-chip">
                    <p class="summary-chip-label">Positionen</p>
                    <p class="summary-chip-value">{{ depotSummaryFor(account.account_id).holdingsCount }}</p>
                  </article>
                  <article class="summary-chip">
                    <p class="summary-chip-label">Investiert</p>
                    <p class="summary-chip-value">
                      {{ formatCurrency(depotSummaryFor(account.account_id).investedTotal, depotSummaryFor(account.account_id).currency) }}
                    </p>
                  </article>
                  <article class="summary-chip">
                    <p class="summary-chip-label">Erster Kauf</p>
                    <p class="summary-chip-value">{{ formatDate(depotSummaryFor(account.account_id).firstBuyDate) }}</p>
                  </article>
                </div>
                <p v-if="showDepotEmptyState(account.account_id)" class="depot-empty-state">Noch keine Depot-Bestandteile</p>
              </template>
              <template v-else>
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
              </template>
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
import type { AccountReadModel, BankReadModel, PersonReadModel, PortfolioDetailReadModel, PortfolioReadModel } from '@/shared/model/types'

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
type DepotAccountSummary = {
  accountId: string
  accountLabel: string
  bankName: string
  depotNumber: string | null
  portfolioId: string | null
  hasPortfolio: boolean
  holdingsCount: number
  investedTotal: number
  currency: string
  firstBuyDate: string | null
}
const depotSummariesByAccountId = ref<Record<string, DepotAccountSummary>>({})

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

function isDepotAccount(account: AccountReadModel): boolean {
  return account.account_type === 'depot'
}

function depotSummaryFor(accountId: string): DepotAccountSummary {
  return depotSummariesByAccountId.value[accountId] ?? {
    accountId,
    accountLabel: '',
    bankName: '',
    depotNumber: null,
    portfolioId: null,
    hasPortfolio: false,
    holdingsCount: 0,
    investedTotal: 0,
    currency: 'EUR',
    firstBuyDate: null
  }
}

function showDepotEmptyState(accountId: string): boolean {
  const summary = depotSummaryFor(accountId)
  return !summary.hasPortfolio || summary.holdingsCount === 0
}

function formatCurrency(value: number, currency: string): string {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency, maximumFractionDigits: 2 }).format(value)
}

function formatDate(value: string | null): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('de-DE', { dateStyle: 'medium' }).format(date)
}

function openDetails(account: AccountReadModel) {
  if (!personId.value) return
  if (isDepotAccount(account)) {
    void router.push(`/accounts/manage/${account.account_id}?personId=${personId.value}&section=bestandteile`)
    return
  }
  void router.push(`/accounts/manage/${account.account_id}?personId=${personId.value}`)
}

function createDepotSummary(
  account: AccountReadModel,
  match: PortfolioReadModel | undefined,
  detail: PortfolioDetailReadModel | undefined
): DepotAccountSummary {
  const holdings = detail?.holdings ?? []
  return {
    accountId: account.account_id,
    accountLabel: account.label,
    bankName: bankName(account.bank_id),
    depotNumber: account.depot_number ?? null,
    portfolioId: match?.portfolio_id ?? null,
    hasPortfolio: Boolean(match),
    holdingsCount: holdings.length,
    investedTotal: holdings.reduce((sum, holding) => sum + (holding.quantity * holding.acquisition_price), 0),
    currency: holdings[0]?.currency ?? account.currency,
    firstBuyDate: holdings.length > 0 ? holdings.reduce((min, holding) => (holding.buy_date < min ? holding.buy_date : min), holdings[0].buy_date) : null
  }
}

async function loadData() {
  if (!personId.value) {
    person.value = null
    accounts.value = []
    errorMessage.value = null
    banks.value = []
    depotSummariesByAccountId.value = {}
    return
  }

  loading.value = true
  errorMessage.value = null

  try {
    const [personDetail, accountList, bankResult, portfolioList] = await Promise.all([
      apiClient.person(personId.value),
      apiClient.accounts(personId.value),
      apiClient.banks(),
      apiClient.portfolios(personId.value)
    ])
    person.value = personDetail.person
    accounts.value = accountList
    banks.value = bankResult.items

    const portfolioByDisplayName = new Map(portfolioList.items.map((portfolio) => [portfolio.display_name, portfolio]))
    const depotAccounts = accountList.filter((account) => isDepotAccount(account))
    const matchingPortfolios = depotAccounts
      .map((account) => portfolioByDisplayName.get(account.label))
      .filter((portfolio): portfolio is PortfolioReadModel => Boolean(portfolio))
    const uniquePortfolioIds = Array.from(new Set(matchingPortfolios.map((portfolio) => portfolio.portfolio_id)))
    const details = await Promise.all(uniquePortfolioIds.map(async (portfolioId) => apiClient.portfolio(portfolioId)))
    const detailByPortfolioId = new Map(details.map((detail) => [detail.portfolio_id, detail]))

    depotSummariesByAccountId.value = Object.fromEntries(
      depotAccounts.map((account) => {
        const match = portfolioByDisplayName.get(account.label)
        const detail = match ? detailByPortfolioId.get(match.portfolio_id) : undefined
        return [account.account_id, createDepotSummary(account, match, detail)]
      })
    )
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

.account-item--depot {
  border-color: #bfdbfe;
  background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 55%);
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

.depot-account-number {
  margin: 0.85rem 0 0;
  color: #334155;
  font-size: 0.95rem;
}

.depot-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.summary-chip {
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
  padding: 0.5rem 0.6rem;
}

.summary-chip-label {
  margin: 0;
  font-size: 0.75rem;
  color: #475569;
}

.summary-chip-value {
  margin: 0.2rem 0 0;
  font-weight: 600;
  color: #0f172a;
}

.depot-empty-state {
  margin: 0.75rem 0 0;
  color: #1e3a8a;
  font-weight: 600;
}

</style>
