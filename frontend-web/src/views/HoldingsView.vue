<template>
  <section class="card holdings-view">
    <div class="view-header">
      <div class="view-header-copy">
        <h2>Depot-/Holding-Erfassung</h2>
        <p>Portfolio wählen, Instrument suchen und Holding erfassen.</p>
      </div>
      <RouterLink class="btn flow-btn" :to="backTarget">{{ backLabel }}</RouterLink>
    </div>

    <p v-if="!hasPersonContext" class="context-hint">Bitte zuerst eine Person auswählen.</p>

    <div class="grid two-col">
      <div><label>Person-ID</label><input class="input" v-model.trim="personId" /></div>
      <button class="btn" @click="loadPortfolios" :disabled="!personId || loadingPortfolios">Depots laden</button>
    </div>

    <div class="grid two-col">
      <div><label>Neues Portfolio</label><input class="input" v-model.trim="newPortfolioName" placeholder="z. B. Langfrist-Depot" /></div>
      <button class="btn" @click="createPortfolio" :disabled="!canCreatePortfolio">Portfolio anlegen</button>
    </div>

    <LoadingState v-if="loadingPortfolios" />
    <ErrorState v-else-if="portfolioError" :message="portfolioError" />

    <template v-else>
      <div v-if="portfolios.length" class="grid two-col">
        <div>
          <label>Portfolio</label>
          <select class="input" v-model="selectedPortfolioId" @change="loadPortfolioDetail">
            <option v-for="portfolio in portfolios" :key="portfolio.portfolio_id" :value="portfolio.portfolio_id">{{ portfolio.display_name }}</option>
          </select>
        </div>
      </div>
      <EmptyState v-else>Keine Depots vorhanden.</EmptyState>
    </template>

    <article v-if="selectedPortfolioId" class="card nested">
      <h3>Holding hinzufügen</h3>
      <div class="grid two-col">
        <div><label>Instrument-Suche</label><input class="input" v-model.trim="searchQuery" placeholder="Name / Symbol / ISIN / WKN" /></div>
        <button class="btn" @click="searchInstrument" :disabled="searchQuery.length < 1 || searching">Suchen</button>
      </div>
      <LoadingState v-if="searching" />
      <ErrorState v-else-if="searchError" :message="searchError" />
      <p v-else-if="searched && !searchResults.length">Keine Treffer gefunden.</p>
      <ul v-else class="search-list">
        <li v-for="result in searchResults" :key="`${result.symbol}-${result.isin || ''}`">
          <button class="btn secondary" @click="selectInstrument(result)">{{ result.symbol }} · {{ result.display_name || result.company_name }} <small>({{ formatPrice(result.last_price, result.currency) }})</small></button>
        </li>
      </ul>

      <form v-if="selectedInstrument" class="holding-form" @submit.prevent="saveHolding">
        <p>Ausgewählt: <strong>{{ selectedInstrument.symbol }}</strong> – {{ selectedInstrument.display_name || selectedInstrument.company_name }}</p>
        <div class="grid three-col">
          <div><label>Stückzahl</label><input class="input" v-model.number="holdingForm.quantity" type="number" min="0.000001" step="0.000001" /></div>
          <div><label>Kaufkurs</label><input class="input" v-model.number="holdingForm.acquisition_price" type="number" min="0.000001" step="0.000001" /></div>
          <div><label>Währung</label><input class="input" v-model="holdingForm.currency" /></div>
          <div><label>Kaufdatum</label><input class="input" v-model="holdingForm.buy_date" type="date" /></div>
          <div class="wide"><label>Notiz</label><input class="input" v-model="holdingForm.notes" /></div>
        </div>
        <button class="btn" :disabled="saving">Holding speichern</button>
      </form>

      <ErrorState v-if="saveError" :message="saveError" />
    </article>

    <article v-if="portfolioDetail" class="card nested">
      <h3>Holdings im Portfolio</h3>
      <EmptyState v-if="!portfolioDetail.holdings.length">Noch keine Holdings gespeichert.</EmptyState>
      <ul v-else>
        <li v-for="holding in portfolioDetail.holdings" :key="holding.holding_id">
          {{ holding.symbol }} · {{ holding.quantity }} @ {{ holding.acquisition_price }} {{ holding.currency }} ({{ holding.buy_date }})
        </li>
      </ul>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient } from '../api/client'
import type { HoldingCreatePayload, InstrumentSearchItem, PortfolioDetailReadModel, PortfolioReadModel } from '../types/models'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

const route = useRoute()
const personId = ref(typeof route.query.personId === 'string' ? route.query.personId : '')
const hasPersonContext = computed(() => typeof route.query.personId === 'string' && route.query.personId.length > 0)
const backTarget = computed(() => hasPersonContext.value ? `/persons/${route.query.personId as string}` : '/persons/select')
const backLabel = computed(() => (hasPersonContext.value ? 'Zurück zum Personen-Hub' : 'Zur Personenliste'))

const portfolios = ref<PortfolioReadModel[]>([])
const selectedPortfolioId = ref('')
const portfolioDetail = ref<PortfolioDetailReadModel | null>(null)
const loadingPortfolios = ref(false)
const portfolioError = ref<string | null>(null)
const newPortfolioName = ref('')

const searchQuery = ref('')
const searchResults = ref<InstrumentSearchItem[]>([])
const selectedInstrument = ref<InstrumentSearchItem | null>(null)
const searchError = ref<string | null>(null)
const searching = ref(false)
const searched = ref(false)

const holdingForm = ref<HoldingCreatePayload>({ symbol: '', quantity: 1, acquisition_price: 0, currency: 'EUR', buy_date: '', notes: null })
const saving = ref(false)
const saveError = ref<string | null>(null)

const canCreatePortfolio = computed(() => personId.value.length > 0 && newPortfolioName.value.trim().length > 0)

function formatPrice(price?: number | null, currency?: string | null) {
  if (price == null) return 'kein Kurs'
  return `${price} ${currency ?? ''}`.trim()
}

async function loadPortfolios() {
  loadingPortfolios.value = true
  portfolioError.value = null
  try {
    const response = await apiClient.portfolios(personId.value)
    portfolios.value = response.items
    selectedPortfolioId.value = response.items[0]?.portfolio_id ?? ''
    if (selectedPortfolioId.value) await loadPortfolioDetail()
  } catch (e) {
    portfolioError.value = e instanceof Error ? e.message : 'Fehler beim Laden der Portfolios'
  } finally { loadingPortfolios.value = false }
}

async function createPortfolio() {
  if (!canCreatePortfolio.value) return
  await apiClient.createPortfolio(personId.value, { display_name: newPortfolioName.value })
  newPortfolioName.value = ''
  await loadPortfolios()
}

async function loadPortfolioDetail() {
  if (!selectedPortfolioId.value) return
  portfolioDetail.value = await apiClient.portfolio(selectedPortfolioId.value)
}

async function searchInstrument() {
  searching.value = true
  searchError.value = null
  searched.value = true
  try {
    const result = await apiClient.searchInstruments(searchQuery.value)
    searchResults.value = result.items
  } catch (e) {
    searchError.value = e instanceof Error ? e.message : 'Fehler bei der Suche'
    searchResults.value = []
  } finally { searching.value = false }
}

function selectInstrument(item: InstrumentSearchItem) {
  selectedInstrument.value = item
  holdingForm.value = {
    symbol: item.symbol,
    isin: item.isin,
    wkn: item.wkn,
    company_name: item.company_name,
    display_name: item.display_name,
    quantity: 1,
    acquisition_price: item.last_price ?? 0,
    currency: item.currency ?? 'EUR',
    buy_date: new Date().toISOString().slice(0, 10),
    notes: null
  }
}

async function saveHolding() {
  if (!selectedPortfolioId.value || !selectedInstrument.value) return
  saving.value = true
  saveError.value = null
  try {
    await apiClient.addHolding(selectedPortfolioId.value, holdingForm.value)
    await loadPortfolioDetail()
  } catch (e) {
    saveError.value = e instanceof Error ? e.message : 'Fehler beim Speichern der Holding'
  } finally { saving.value = false }
}

onMounted(async () => { if (personId.value) await loadPortfolios() })
</script>

<style scoped>
.holdings-view { display: grid; gap: 1rem; }
.two-col { grid-template-columns: 1fr auto; gap: .75rem; }
.three-col { grid-template-columns: repeat(3, 1fr); gap: .75rem; }
.nested { margin-top: .5rem; }
.search-list { list-style: none; padding: 0; display: grid; gap: .5rem; }
.wide { grid-column: span 2; }
</style>
