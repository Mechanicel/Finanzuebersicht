<template>
  <article class="depot-holdings card nested">
    <div class="view-header-copy">
      <h3>{{ title }}</h3>
      <p class="muted">Positionen bleiben als Kauf-/Bestandsdaten im Portfolio-Service gespeichert.</p>
    </div>

    <p v-if="feedbackMessage" class="success">{{ feedbackMessage }}</p>
    <ErrorState v-if="errorMessage" :message="errorMessage" />

    <div class="context-panel">
      <p class="muted">Portfolio-Kontext: <strong>{{ portfolioDetail?.display_name || depotLabel }}</strong></p>
      <button class="btn secondary" type="button" @click="refreshPortfolio" :disabled="!selectedPortfolioId || loading">Holdings aktualisieren</button>
    </div>

    <div v-if="selectedPortfolioId" class="manager-grid">
      <section>
        <h4>Position hinzufügen</h4>
        <div>
          <label>Instrument-Suche</label>
          <input class="input" v-model.trim="searchQuery" :placeholder="`Name / Symbol / ISIN / WKN (mind. ${MIN_SEARCH_LENGTH} Zeichen)`" />
        </div>
        <p v-if="searchHint" class="muted">{{ searchHint }}</p>
        <LoadingState v-if="searching" />
        <ErrorState v-else-if="searchError" :message="searchError" />
        <EmptyState v-else-if="showEmptySearch">Keine Treffer gefunden.</EmptyState>

        <ul v-else-if="searchResults.length" class="search-list">
          <li v-for="item in searchResults" :key="`${item.symbol}-${item.isin || ''}`">
            <button class="btn secondary result-item" type="button" @click="selectInstrument(item)">
              <strong>{{ item.symbol }}</strong>
              <span>{{ item.display_name || item.company_name || 'Unbenanntes Instrument' }}</span>
              <small v-if="item.last_price != null">Letzter Preis: {{ item.last_price }} {{ item.currency || '' }}</small>
            </button>
          </li>
        </ul>

        <form class="holding-form" @submit.prevent="createHolding">
          <p class="muted">{{ selectedInstrument ? `Vorausgefüllt aus Suche: ${selectedInstrument.symbol}` : 'Ohne Suche möglich: Symbol direkt eintragen.' }}</p>
          <div class="grid three-col">
            <div><label>Symbol</label><input data-testid="holding-symbol" class="input" v-model.trim="draftHolding.symbol" required /></div>
            <div><label>ISIN</label><input data-testid="holding-isin" class="input" v-model.trim="draftHolding.isin" /></div>
            <div><label>WKN</label><input data-testid="holding-wkn" class="input" v-model.trim="draftHolding.wkn" /></div>
            <div><label>Stückzahl</label><input class="input" v-model.number="draftHolding.quantity" type="number" min="0.000001" step="0.000001" required /></div>
            <div><label>Kaufkurs</label><input data-testid="holding-acquisition-price" class="input" v-model.number="draftHolding.acquisition_price" type="number" min="0.000001" step="0.000001" required /></div>
            <div><label>Währung</label><input data-testid="holding-currency" class="input" v-model.trim="draftHolding.currency" maxlength="3" required /></div>
            <div><label>Kaufdatum</label><input class="input" v-model="draftHolding.buy_date" type="date" required /></div>
            <div><label>Name</label><input data-testid="holding-display-name" class="input" v-model.trim="draftHolding.display_name" /></div>
            <div><label>Unternehmen</label><input data-testid="holding-company-name" class="input" v-model.trim="draftHolding.company_name" /></div>
            <div><label>Börse</label><input data-testid="holding-exchange" class="input" v-model.trim="draftHolding.exchange" /></div>
            <div><label>Quote-Type</label><input data-testid="holding-quote-type" class="input" v-model.trim="draftHolding.quote_type" /></div>
            <div><label>Asset-Type</label><input data-testid="holding-asset-type" class="input" v-model.trim="draftHolding.asset_type" /></div>
            <div class="wide"><label>Notiz</label><input class="input" v-model.trim="draftHolding.notes" /></div>
          </div>
          <button class="btn" type="submit" :disabled="saving">Holding hinzufügen</button>
        </form>
      </section>

      <section>
        <h4>Vorhandene Positionen</h4>
        <LoadingState v-if="loading" />
        <EmptyState v-else-if="!portfolioDetail?.holdings.length">Keine Positionen vorhanden.</EmptyState>
        <ul v-else class="holding-list">
          <li v-for="holding in portfolioDetail.holdings" :key="holding.holding_id" class="holding-item">
            <template v-if="editHoldingId !== holding.holding_id">
              <p><strong>{{ holding.symbol }}</strong> · {{ holding.quantity }} @ {{ holding.acquisition_price }} {{ holding.currency }}</p>
              <p class="muted">Kaufdatum: {{ holding.buy_date }} · {{ holding.notes || 'keine Notiz' }}</p>
              <div class="row-actions">
                <button class="btn secondary" type="button" @click="startEdit(holding)">Bearbeiten</button>
                <button class="btn secondary" type="button" @click="removeHolding(holding.holding_id)">Löschen</button>
              </div>
            </template>

            <form v-else class="holding-form" @submit.prevent="saveEdit(holding.holding_id)">
              <div class="grid three-col">
                <div><label>Stückzahl</label><input class="input" v-model.number="editHolding.quantity" type="number" min="0.000001" step="0.000001" required /></div>
                <div><label>Kaufkurs</label><input class="input" v-model.number="editHolding.acquisition_price" type="number" min="0.000001" step="0.000001" required /></div>
                <div><label>Währung</label><input class="input" v-model.trim="editHolding.currency" maxlength="3" required /></div>
                <div><label>Kaufdatum</label><input class="input" v-model="editHolding.buy_date" type="date" required /></div>
                <div class="wide"><label>Notiz</label><input class="input" v-model.trim="editHolding.notes" /></div>
              </div>
              <div class="row-actions">
                <button class="btn" type="submit" :disabled="saving">Speichern</button>
                <button class="btn secondary" type="button" @click="cancelEdit">Abbrechen</button>
              </div>
            </form>
          </li>
        </ul>
      </section>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { apiClient } from '@/shared/api/client'
import type { HoldingCreatePayload, HoldingReadModel, InstrumentSearchItem, PortfolioDetailReadModel, PortfolioReadModel } from '@/shared/model/types'
import ErrorState from '@/shared/ui/ErrorState.vue'
import LoadingState from '@/shared/ui/LoadingState.vue'
import EmptyState from '@/shared/ui/EmptyState.vue'

const props = defineProps<{ personId: string; depotLabel: string; title?: string }>()

const title = computed(() => props.title ?? 'Depot-Positionen')
const portfolios = ref<PortfolioReadModel[]>([])
const selectedPortfolioId = ref('')
const portfolioDetail = ref<PortfolioDetailReadModel | null>(null)
const loading = ref(false)
const saving = ref(false)
const searching = ref(false)
const searchQuery = ref('')
const searchResults = ref<InstrumentSearchItem[]>([])
const selectedInstrument = ref<InstrumentSearchItem | null>(null)
const searchError = ref<string | null>(null)
const searched = ref(false)
const errorMessage = ref<string | null>(null)
const feedbackMessage = ref('')
const editHoldingId = ref('')

type HoldingDraftState = HoldingCreatePayload & {
  exchange?: string | null
  quote_type?: string | null
  asset_type?: string | null
}

const draftHolding = ref<HoldingDraftState>({ symbol: '', quantity: 1, acquisition_price: 0, currency: 'EUR', buy_date: new Date().toISOString().slice(0, 10), notes: null, exchange: null, quote_type: null, asset_type: null })
const editHolding = ref({ quantity: 1, acquisition_price: 0, currency: 'EUR', buy_date: new Date().toISOString().slice(0, 10), notes: '' })
const MIN_SEARCH_LENGTH = 2
const SEARCH_DEBOUNCE_MS = 350
let searchDebounceHandle: ReturnType<typeof setTimeout> | null = null

const showEmptySearch = computed(() => searched.value && !searching.value && !searchError.value && searchResults.value.length === 0 && searchQuery.value.length >= MIN_SEARCH_LENGTH)
const searchHint = computed(() => {
  if (!searchQuery.value.length) return 'Suche startet beim Tippen.'
  if (searchQuery.value.length < MIN_SEARCH_LENGTH) return `Bitte mindestens ${MIN_SEARCH_LENGTH} Zeichen eingeben.`
  return null
})

function cleanOptional(value?: string | null) {
  const trimmed = (value ?? '').trim()
  return trimmed.length > 0 ? trimmed : null
}

async function resolvePortfolio() {
  const list = await apiClient.portfolios(props.personId)
  portfolios.value = list.items
  let match = list.items.find((item) => item.display_name === props.depotLabel)
  if (!match && props.depotLabel.trim()) {
    match = await apiClient.createPortfolio(props.personId, { display_name: props.depotLabel.trim() })
    portfolios.value = [...list.items, match]
  }
  selectedPortfolioId.value = match?.portfolio_id ?? list.items[0]?.portfolio_id ?? ''
}

async function load() {
  if (!props.personId) return
  loading.value = true
  errorMessage.value = null
  try {
    await resolvePortfolio()
    await refreshPortfolio()
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : 'Depot-Positionen konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function refreshPortfolio() {
  if (!selectedPortfolioId.value) {
    portfolioDetail.value = null
    return
  }
  portfolioDetail.value = await apiClient.portfolio(selectedPortfolioId.value)
}

async function searchInstrument() {
  if (searchQuery.value.length < MIN_SEARCH_LENGTH) {
    searchResults.value = []
    searched.value = false
    searchError.value = null
    return
  }
  searching.value = true
  searchError.value = null
  searched.value = true
  try {
    const result = await apiClient.searchInstruments(searchQuery.value)
    searchResults.value = result.items
  } catch (e) {
    searchError.value = e instanceof Error ? e.message : 'Instrumentensuche fehlgeschlagen.'
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

function selectInstrument(item: InstrumentSearchItem) {
  selectedInstrument.value = item
  draftHolding.value = {
    symbol: item.symbol,
    isin: item.isin,
    wkn: item.wkn,
    display_name: item.display_name,
    company_name: item.company_name,
    exchange: item.exchange,
    quote_type: item.quote_type,
    asset_type: item.asset_type,
    quantity: 1,
    acquisition_price: item.last_price ?? 0,
    currency: item.currency ?? 'EUR',
    buy_date: new Date().toISOString().slice(0, 10),
    notes: null,
  }
}

function scheduleSearch() {
  if (searchDebounceHandle) clearTimeout(searchDebounceHandle)
  if (searchQuery.value.length < MIN_SEARCH_LENGTH) {
    searching.value = false
    searchError.value = null
    searchResults.value = []
    searched.value = false
    return
  }
  searchDebounceHandle = setTimeout(() => {
    void searchInstrument()
  }, SEARCH_DEBOUNCE_MS)
}

async function createHolding() {
  if (!selectedPortfolioId.value) return
  saving.value = true
  errorMessage.value = null
  try {
    await apiClient.addHolding(selectedPortfolioId.value, {
      symbol: draftHolding.value.symbol.trim().toUpperCase(),
      isin: cleanOptional(draftHolding.value.isin),
      wkn: cleanOptional(draftHolding.value.wkn),
      display_name: cleanOptional(draftHolding.value.display_name),
      company_name: cleanOptional(draftHolding.value.company_name),
      quantity: Number(draftHolding.value.quantity),
      acquisition_price: Number(draftHolding.value.acquisition_price),
      currency: draftHolding.value.currency.trim().toUpperCase(),
      buy_date: draftHolding.value.buy_date,
      notes: cleanOptional(draftHolding.value.notes),
    })
    feedbackMessage.value = 'Holding wurde hinzugefügt.'
    selectedInstrument.value = null
    await refreshPortfolio()
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : 'Holding konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

function startEdit(holding: HoldingReadModel) {
  editHoldingId.value = holding.holding_id
  editHolding.value = {
    quantity: holding.quantity,
    acquisition_price: holding.acquisition_price,
    currency: holding.currency,
    buy_date: holding.buy_date,
    notes: holding.notes ?? '',
  }
}

function cancelEdit() {
  editHoldingId.value = ''
}

async function saveEdit(holdingId: string) {
  if (!selectedPortfolioId.value) return
  saving.value = true
  errorMessage.value = null
  try {
    await apiClient.updateHolding(selectedPortfolioId.value, holdingId, {
      quantity: Number(editHolding.value.quantity),
      acquisition_price: Number(editHolding.value.acquisition_price),
      currency: editHolding.value.currency.trim().toUpperCase(),
      buy_date: editHolding.value.buy_date,
      notes: cleanOptional(editHolding.value.notes),
    })
    feedbackMessage.value = 'Holding wurde aktualisiert.'
    editHoldingId.value = ''
    await refreshPortfolio()
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : 'Holding konnte nicht aktualisiert werden.'
  } finally {
    saving.value = false
  }
}

async function removeHolding(holdingId: string) {
  if (!selectedPortfolioId.value) return
  saving.value = true
  errorMessage.value = null
  try {
    await apiClient.deleteHolding(selectedPortfolioId.value, holdingId)
    feedbackMessage.value = 'Holding wurde gelöscht.'
    await refreshPortfolio()
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : 'Holding konnte nicht gelöscht werden.'
  } finally {
    saving.value = false
  }
}

watch(() => [props.personId, props.depotLabel], () => { void load() })
watch(searchQuery, () => {
  searchError.value = null
  scheduleSearch()
})
onMounted(() => { void load() })
onBeforeUnmount(() => {
  if (searchDebounceHandle) clearTimeout(searchDebounceHandle)
})
</script>

<style scoped>
.nested { margin-top: .75rem; }
.three-col { grid-template-columns: repeat(3, 1fr); gap: .75rem; }
.wide { grid-column: span 3; }
.context-panel { display: flex; align-items: center; justify-content: space-between; gap: .75rem; margin-top: .75rem; }
.manager-grid { display: grid; gap: 1rem; }
.holding-list { list-style: none; padding: 0; display: grid; gap: .75rem; }
.holding-item { border: 1px solid #e2e8f0; border-radius: 8px; padding: .75rem; }
.row-actions { display: flex; gap: .5rem; margin-top: .5rem; }
.search-list { list-style: none; padding: 0; display: grid; gap: .5rem; margin-top: .5rem; }
.result-item { width: 100%; text-align: left; display: grid; gap: .2rem; }
</style>
