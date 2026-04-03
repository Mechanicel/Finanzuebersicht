<template>
  <article class="depot-holdings card nested">
    <div class="view-header-copy">
      <h3>{{ title }}</h3>
      <p class="muted">Positionen bleiben als Kauf-/Bestandsdaten im Portfolio-Service gespeichert.</p>
    </div>

    <p v-if="feedbackMessage" ref="feedbackBannerRef" class="feedback-banner success" role="status">{{ feedbackMessage }}</p>
    <ErrorState v-if="errorMessage" :message="errorMessage" />

    <div class="context-panel">
      <p class="muted">Portfolio-Kontext: <strong>{{ portfolioDetail?.display_name || depotLabel }}</strong></p>
    </div>

    <div v-if="selectedPortfolioId" class="manager-grid">
      <section v-if="showAddSection">
        <h4>Position hinzufügen</h4>

        <div class="search-panel">
          <label>Instrument-Suche</label>
          <input class="input" v-model.trim="searchQuery" :placeholder="`Name / Symbol / ISIN / WKN (mind. ${MIN_SEARCH_LENGTH} Zeichen)`" />
          <p v-if="searchHint" class="muted">{{ searchHint }}</p>
          <LoadingState v-if="searching" />
          <ErrorState v-else-if="searchError" :message="searchError" />
          <EmptyState v-else-if="showEmptySearch">Keine Treffer gefunden.</EmptyState>

          <ul v-else-if="searchResults.length" class="search-list">
            <li v-for="item in searchResults" :key="item.symbol">
              <button
                class="result-item result-item--compact"
                type="button"
                :class="{ 'result-item--active': isSelectedResult(item) }"
                :disabled="profileLoading && selectingSymbol === item.symbol"
                @click="selectInstrument(item)"
              >
                <div class="result-row">
                  <strong class="result-symbol">{{ item.symbol }}</strong>
                  <span class="result-name">{{ item.display_name || item.company_name || 'Unbenanntes Instrument' }}</span>
                </div>
                <div class="result-row result-row--meta">
                  <small v-if="item.currency">{{ item.currency }}</small>
                  <small v-if="item.exchange">{{ item.exchange }}</small>
                  <small v-if="item.exchange_full_name">{{ item.exchange_full_name }}</small>
                </div>
                <small v-if="profileLoading && selectingSymbol === item.symbol" class="result-loading">Lade Profil…</small>
              </button>
            </li>
          </ul>
        </div>

        <div class="profile-panel">
          <h5>Profilübersicht</h5>
          <LoadingState v-if="profileLoading" />
          <ErrorState v-else-if="profileError" :message="profileError" />
          <p v-else-if="!selectedProfile" class="muted">Noch kein Profil geladen. Wähle einen Suchtreffer aus.</p>
          <div v-else class="profile-card">
            <div class="profile-main">
              <img
                v-if="selectedProfile.image"
                :src="selectedProfile.image"
                :alt="`Logo ${selectedProfile.company_name || selectedProfile.symbol}`"
                class="profile-image"
              />
              <dl class="profile-grid">
                <template v-for="entry in profileEntries" :key="entry.key">
                  <dt>{{ entry.label }}</dt>
                  <dd>
                    <a v-if="entry.isLink" :href="entry.href" target="_blank" rel="noopener noreferrer">{{ entry.value }}</a>
                    <template v-else>{{ entry.value }}</template>
                  </dd>
                </template>
              </dl>
            </div>
            <div v-if="profileDescription" class="profile-description">
              <h6>Beschreibung</h6>
              <p>{{ profileDescription }}</p>
            </div>
          </div>
        </div>

        <form class="holding-form" @submit.prevent="createHolding">
          <p class="muted">{{ selectedProfile ? `Vorausgefüllt aus Profil: ${selectedProfile.symbol}` : 'Ohne Suche möglich: Symbol direkt eintragen.' }}</p>
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

      <section v-if="showHoldingsSection">
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
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { apiClient } from '@/shared/api/client'
import type { HoldingCreatePayload, HoldingReadModel, InstrumentSearchItem, MarketdataProfile, PortfolioDetailReadModel, PortfolioReadModel } from '@/shared/model/types'
import ErrorState from '@/shared/ui/ErrorState.vue'
import LoadingState from '@/shared/ui/LoadingState.vue'
import EmptyState from '@/shared/ui/EmptyState.vue'

const props = withDefaults(
  defineProps<{ personId: string; depotLabel: string; title?: string; viewMode?: 'all' | 'holdings' | 'add' }>(),
  { viewMode: 'all' }
)

const title = computed(() => props.title ?? 'Depot-Positionen')
const showAddSection = computed(() => props.viewMode === 'all' || props.viewMode === 'add')
const showHoldingsSection = computed(() => props.viewMode === 'all' || props.viewMode === 'holdings')
const portfolios = ref<PortfolioReadModel[]>([])
const selectedPortfolioId = ref('')
const portfolioDetail = ref<PortfolioDetailReadModel | null>(null)
const loading = ref(false)
const saving = ref(false)
const searching = ref(false)
const profileLoading = ref(false)
const searchQuery = ref('')
const searchResults = ref<InstrumentSearchItem[]>([])
const selectedProfile = ref<MarketdataProfile | null>(null)
const selectingSymbol = ref<string | null>(null)
const searchError = ref<string | null>(null)
const profileError = ref<string | null>(null)
const searched = ref(false)
const errorMessage = ref<string | null>(null)
const feedbackMessage = ref('')
const feedbackBannerRef = ref<HTMLElement | null>(null)
const editHoldingId = ref('')
let activeSearchRequestId = 0
let activeProfileRequestId = 0

type HoldingDraftState = HoldingCreatePayload & {
  acquisition_price: number | null
  exchange?: string | null
  quote_type?: string | null
  asset_type?: string | null
}

const draftHolding = ref<HoldingDraftState>(createDefaultDraftHolding())
const editHolding = ref({ quantity: 1, acquisition_price: 0, currency: 'EUR', buy_date: new Date().toISOString().slice(0, 10), notes: '' })
const MIN_SEARCH_LENGTH = 2
const SEARCH_DEBOUNCE_MS = 1000
let searchDebounceHandle: ReturnType<typeof setTimeout> | null = null

const showEmptySearch = computed(() => searched.value && !searching.value && !searchError.value && searchResults.value.length === 0 && searchQuery.value.length >= MIN_SEARCH_LENGTH)
const searchHint = computed(() => {
  if (!searchQuery.value.length) return 'Suche startet beim Tippen.'
  if (searchQuery.value.length < MIN_SEARCH_LENGTH) return `Bitte mindestens ${MIN_SEARCH_LENGTH} Zeichen eingeben.`
  return null
})

const profileDescription = computed(() => {
  if (!selectedProfile.value) return null
  return hasValue(selectedProfile.value.description) ? String(selectedProfile.value.description) : null
})

const profileEntries = computed(() => {
  if (!selectedProfile.value) return []
  const profile = selectedProfile.value
  return [
    asProfileEntry('company_name', 'Name', profile.company_name),
    asProfileEntry('symbol', 'Symbol', profile.symbol),
    asProfileEntry('price', 'Kurs', formatPrice(profile.price, profile.currency)),
    asProfileEntry('exchange', 'Börse', formatExchange(profile.exchange, profile.exchange_full_name)),
    asProfileEntry('isin', 'ISIN', profile.isin),
    asProfileEntry('industry', 'Industrie', profile.industry),
    asProfileEntry('website', 'Website', profile.website, true),
    asProfileEntry('ceo', 'CEO', profile.ceo),
    asProfileEntry('sector', 'Sektor', profile.sector),
    asProfileEntry('country', 'Land', profile.country),
    asProfileEntry('phone', 'Telefon', profile.phone),
    asProfileEntry('address_line', 'Adresse', profile.address_line),
  ].filter((entry): entry is ProfileEntry => entry !== null)
})

interface ProfileEntry {
  key: string
  label: string
  value: string
  isLink: boolean
  href?: string
}

function cleanOptional(value?: string | null) {
  const trimmed = (value ?? '').trim()
  return trimmed.length > 0 ? trimmed : null
}

function createDefaultDraftHolding(): HoldingDraftState {
  return {
    symbol: '',
    quantity: 1,
    acquisition_price: null,
    currency: 'EUR',
    buy_date: new Date().toISOString().slice(0, 10),
    notes: null,
    exchange: null,
    quote_type: null,
    asset_type: null,
  }
}

function resetDraftHoldingForm() {
  draftHolding.value = createDefaultDraftHolding()
  selectedProfile.value = null
  searchQuery.value = ''
  searchResults.value = []
  searched.value = false
  searchError.value = null
  profileError.value = null
}

async function showSuccessFeedback(message: string) {
  feedbackMessage.value = message
  await nextTick()
  if (feedbackBannerRef.value && typeof feedbackBannerRef.value.scrollIntoView === 'function') {
    feedbackBannerRef.value.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
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

async function searchInstrument(requestId: number) {
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
    if (requestId !== activeSearchRequestId) return
    searchResults.value = result.items
  } catch (e) {
    if (requestId !== activeSearchRequestId) return
    searchError.value = e instanceof Error ? e.message : 'Instrumentensuche fehlgeschlagen.'
    searchResults.value = []
  } finally {
    if (requestId === activeSearchRequestId) {
      searching.value = false
    }
  }
}

function hasValue<T>(value: T | null | undefined) {
  if (value == null) return false
  if (typeof value === 'string') return value.trim().length > 0
  return true
}

function asProfileEntry(key: string, label: string, value: unknown, isLink = false): ProfileEntry | null {
  if (!hasValue(value)) return null
  const text = String(value).trim()
  if (!text) return null
  return {
    key,
    label,
    value: text,
    isLink,
    href: isLink ? normalizeUrl(text) : undefined,
  }
}

function normalizeUrl(url: string) {
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  return `https://${url}`
}

function formatPrice(price?: number | null, currency?: string | null) {
  if (typeof price !== 'number') return null
  const hasCurrency = hasValue(currency)
  return hasCurrency ? `${price} ${String(currency).trim()}` : `${price}`
}

function formatExchange(exchange?: string | null, exchangeFullName?: string | null) {
  const parts = [exchange, exchangeFullName].filter(hasValue).map((value) => String(value).trim())
  return parts.length ? parts.join(' · ') : null
}

function isSelectedResult(item: InstrumentSearchItem) {
  return selectedProfile.value?.symbol === item.symbol
}

function buildDraftHoldingFromProfile(profile: MarketdataProfile) {
  return {
    symbol: profile.symbol,
    isin: typeof profile.isin === 'string' ? profile.isin : null,
    wkn: null,
    display_name: typeof profile.company_name === 'string' ? profile.company_name : null,
    company_name: typeof profile.company_name === 'string' ? profile.company_name : null,
    exchange: typeof profile.exchange === 'string' ? profile.exchange : null,
    quote_type: null,
    asset_type: null,
    quantity: 1,
    acquisition_price: typeof profile.price === 'number' ? profile.price : null,
    currency: typeof profile.currency === 'string' ? profile.currency : 'EUR',
    buy_date: new Date().toISOString().slice(0, 10),
    notes: null,
  }
}

async function selectInstrument(item: InstrumentSearchItem) {
  selectingSymbol.value = item.symbol
  profileError.value = null
  const requestId = ++activeProfileRequestId
  profileLoading.value = true
  try {
    const profile = await apiClient.marketdataProfile(item.symbol)
    if (requestId !== activeProfileRequestId) return
    selectedProfile.value = profile
    draftHolding.value = buildDraftHoldingFromProfile(profile)
  } catch (e) {
    if (requestId !== activeProfileRequestId) return
    profileError.value = e instanceof Error ? e.message : 'Profil konnte nicht geladen werden.'
  } finally {
    if (requestId === activeProfileRequestId) {
      profileLoading.value = false
      selectingSymbol.value = null
    }
  }
}

function scheduleSearch() {
  if (searchDebounceHandle) clearTimeout(searchDebounceHandle)
  if (searchQuery.value.length < MIN_SEARCH_LENGTH) {
    activeSearchRequestId += 1
    searching.value = false
    searchError.value = null
    searchResults.value = []
    searched.value = false
    return
  }
  const requestId = ++activeSearchRequestId
  searchDebounceHandle = setTimeout(() => {
    void searchInstrument(requestId)
  }, SEARCH_DEBOUNCE_MS)
}

async function createHolding() {
  if (!selectedPortfolioId.value) return
  const acquisitionPrice = Number(draftHolding.value.acquisition_price)
  if (!Number.isFinite(acquisitionPrice) || acquisitionPrice <= 0) {
    errorMessage.value = 'Bitte einen gültigen Kaufkurs eingeben.'
    return
  }
  saving.value = true
  errorMessage.value = null
  feedbackMessage.value = ''
  try {
    await apiClient.addHolding(selectedPortfolioId.value, {
      symbol: draftHolding.value.symbol.trim().toUpperCase(),
      isin: cleanOptional(draftHolding.value.isin),
      wkn: cleanOptional(draftHolding.value.wkn),
      display_name: cleanOptional(draftHolding.value.display_name),
      company_name: cleanOptional(draftHolding.value.company_name),
      quantity: Number(draftHolding.value.quantity),
      acquisition_price: acquisitionPrice,
      currency: draftHolding.value.currency.trim().toUpperCase(),
      buy_date: draftHolding.value.buy_date,
      notes: cleanOptional(draftHolding.value.notes),
    })
    await showSuccessFeedback('Depotbestandteil wurde erfolgreich hinzugefügt.')
    resetDraftHoldingForm()
    await refreshPortfolio()
  } catch (e) {
    feedbackMessage.value = ''
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
  feedbackMessage.value = ''
  try {
    await apiClient.updateHolding(selectedPortfolioId.value, holdingId, {
      quantity: Number(editHolding.value.quantity),
      acquisition_price: Number(editHolding.value.acquisition_price),
      currency: editHolding.value.currency.trim().toUpperCase(),
      buy_date: editHolding.value.buy_date,
      notes: cleanOptional(editHolding.value.notes),
    })
    await showSuccessFeedback('Holding wurde aktualisiert.')
    editHoldingId.value = ''
    await refreshPortfolio()
  } catch (e) {
    feedbackMessage.value = ''
    errorMessage.value = e instanceof Error ? e.message : 'Holding konnte nicht aktualisiert werden.'
  } finally {
    saving.value = false
  }
}

async function removeHolding(holdingId: string) {
  if (!selectedPortfolioId.value) return
  saving.value = true
  errorMessage.value = null
  feedbackMessage.value = ''
  try {
    await apiClient.deleteHolding(selectedPortfolioId.value, holdingId)
    await showSuccessFeedback('Holding wurde gelöscht.')
    await refreshPortfolio()
  } catch (e) {
    feedbackMessage.value = ''
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
.search-list { list-style: none; padding: 0; display: grid; gap: .4rem; margin-top: .5rem; }
.result-item {
  width: 100%;
  text-align: left;
  display: grid;
  gap: .15rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #f8fafc;
  color: #0f172a;
}
.result-item--compact { padding: .4rem .55rem; min-height: 44px; }
.result-item--active {
  border-color: #2563eb;
  background: #eff6ff;
  box-shadow: 0 0 0 1px #bfdbfe inset;
}
.result-item:disabled { opacity: .75; cursor: wait; }
.result-row { display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; }
.result-row--meta { gap: .45rem; }
.result-symbol { font-size: .82rem; line-height: 1.1; }
.result-name { font-size: .84rem; font-weight: 500; }
.result-row--meta small {
  background: #e2e8f0;
  border-radius: 999px;
  padding: .05rem .38rem;
  line-height: 1.3;
}
.result-loading { color: #334155; }
.search-panel,
.profile-panel { border: 1px solid #e2e8f0; border-radius: 8px; padding: .75rem; margin-bottom: .75rem; }
.profile-card { display: grid; gap: .6rem; }
.profile-main { display: grid; grid-template-columns: auto 1fr; gap: .75rem; align-items: start; }
.profile-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .35rem .75rem; margin: 0; }
.profile-grid dt { font-weight: 600; color: #334155; font-size: .82rem; }
.profile-grid dd { margin: 0; white-space: pre-wrap; word-break: break-word; font-size: .85rem; }
.profile-image { width: 48px; height: 48px; object-fit: contain; border-radius: 6px; border: 1px solid #e2e8f0; background: #fff; }
.profile-description { border-top: 1px solid #e2e8f0; padding-top: .55rem; }
.profile-description h6 { margin: 0 0 .2rem; font-size: .82rem; color: #334155; }
.profile-description p { margin: 0; font-size: .85rem; line-height: 1.4; }
.feedback-banner {
  margin-top: .75rem;
  margin-bottom: .5rem;
  padding: .75rem 1rem;
  border-radius: 8px;
  border: 1px solid #86efac;
  background: #f0fdf4;
  color: #166534;
  font-weight: 600;
}
</style>
