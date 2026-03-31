<template>
  <article class="depot-holdings card nested">
    <div class="view-header-copy">
      <h3>{{ title }}</h3>
      <p class="muted">Positionen bleiben als Kauf-/Bestandsdaten im Portfolio-Service gespeichert.</p>
    </div>

    <p v-if="feedbackMessage" class="success">{{ feedbackMessage }}</p>
    <ErrorState v-if="errorMessage" :message="errorMessage" />

    <div class="grid two-col">
      <div><label>Portfolio</label><select class="input" :value="selectedPortfolioId" @change="onPortfolioChange"><option value="">Bitte wählen</option><option v-for="portfolio in portfolios" :key="portfolio.portfolio_id" :value="portfolio.portfolio_id">{{ portfolio.display_name }}</option></select></div>
      <button class="btn secondary" type="button" @click="refreshPortfolio" :disabled="!selectedPortfolioId || loading">Holdings aktualisieren</button>
    </div>

    <div v-if="selectedPortfolioId" class="manager-grid">
      <section>
        <h4>Position hinzufügen</h4>
        <div class="grid two-col">
          <div><label>Instrument-Suche</label><input class="input" v-model.trim="searchQuery" placeholder="Name / Symbol / ISIN / WKN" /></div>
          <button class="btn" type="button" @click="searchInstrument" :disabled="searchQuery.length < 1 || searching">Suchen</button>
        </div>

        <ul v-if="searchResults.length" class="search-list">
          <li v-for="item in searchResults" :key="`${item.symbol}-${item.isin || ''}`">
            <button class="btn secondary" type="button" @click="selectInstrument(item)">{{ item.symbol }} · {{ item.display_name || item.company_name }}</button>
          </li>
        </ul>

        <form class="holding-form" @submit.prevent="createHolding">
          <p class="muted">{{ selectedInstrument ? `Vorausgefüllt aus Suche: ${selectedInstrument.symbol}` : 'Ohne Suche möglich: Symbol direkt eintragen.' }}</p>
          <div class="grid three-col">
            <div><label>Symbol</label><input class="input" v-model.trim="draftHolding.symbol" required /></div>
            <div><label>ISIN</label><input class="input" v-model.trim="draftHolding.isin" /></div>
            <div><label>WKN</label><input class="input" v-model.trim="draftHolding.wkn" /></div>
            <div><label>Stückzahl</label><input class="input" v-model.number="draftHolding.quantity" type="number" min="0.000001" step="0.000001" required /></div>
            <div><label>Kaufkurs</label><input class="input" v-model.number="draftHolding.acquisition_price" type="number" min="0.000001" step="0.000001" required /></div>
            <div><label>Währung</label><input class="input" v-model.trim="draftHolding.currency" maxlength="3" required /></div>
            <div><label>Kaufdatum</label><input class="input" v-model="draftHolding.buy_date" type="date" required /></div>
            <div><label>Name</label><input class="input" v-model.trim="draftHolding.display_name" /></div>
            <div><label>Unternehmen</label><input class="input" v-model.trim="draftHolding.company_name" /></div>
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
import { computed, onMounted, ref, watch } from 'vue'
import { apiClient } from '../api/client'
import type { HoldingCreatePayload, HoldingReadModel, InstrumentSearchItem, PortfolioDetailReadModel, PortfolioReadModel } from '../types/models'
import ErrorState from '../components/ErrorState.vue'
import LoadingState from '../components/LoadingState.vue'
import EmptyState from '../components/EmptyState.vue'

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
const errorMessage = ref<string | null>(null)
const feedbackMessage = ref('')
const editHoldingId = ref('')

const draftHolding = ref<HoldingCreatePayload>({ symbol: '', quantity: 1, acquisition_price: 0, currency: 'EUR', buy_date: new Date().toISOString().slice(0, 10), notes: null })
const editHolding = ref({ quantity: 1, acquisition_price: 0, currency: 'EUR', buy_date: new Date().toISOString().slice(0, 10), notes: '' })

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

function onPortfolioChange(event: Event) {
  selectedPortfolioId.value = (event.target as HTMLSelectElement).value
  void refreshPortfolio()
}

async function searchInstrument() {
  searching.value = true
  try {
    const result = await apiClient.searchInstruments(searchQuery.value)
    searchResults.value = result.items
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : 'Instrumentensuche fehlgeschlagen.'
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
    quantity: 1,
    acquisition_price: item.last_price ?? 1,
    currency: item.currency ?? 'EUR',
    buy_date: new Date().toISOString().slice(0, 10),
    notes: null,
  }
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
onMounted(() => { void load() })
</script>

<style scoped>
.nested { margin-top: .75rem; }
.two-col { grid-template-columns: 1fr auto; gap: .75rem; }
.three-col { grid-template-columns: repeat(3, 1fr); gap: .75rem; }
.wide { grid-column: span 3; }
.manager-grid { display: grid; gap: 1rem; }
.holding-list { list-style: none; padding: 0; display: grid; gap: .75rem; }
.holding-item { border: 1px solid #e2e8f0; border-radius: 8px; padding: .75rem; }
.row-actions { display: flex; gap: .5rem; margin-top: .5rem; }
.search-list { list-style: none; padding: 0; display: grid; gap: .5rem; margin-top: .5rem; }
</style>
