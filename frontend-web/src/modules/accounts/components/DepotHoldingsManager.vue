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
        <template v-if="isSearchView">
          <h4>Position hinzufügen</h4>

          <div class="search-panel">
            <label>Instrument-Suche</label>
            <input class="input" v-model.trim="searchQuery" :placeholder="`Name / Symbol / ISIN / WKN (mind. ${MIN_SEARCH_LENGTH} Zeichen)`" />
            <p v-if="searchHint" class="muted">{{ searchHint }}</p>
            <LoadingState v-if="searching" />
            <ErrorState v-else-if="searchError" :message="searchError" />
            <EmptyState v-else-if="showEmptySearch">Keine Treffer gefunden.</EmptyState>

            <div v-else-if="searchResults.length" ref="searchListContainerRef">
              <ul class="search-list">
                <li v-for="item in searchResults" :key="item.symbol">
                  <button
                    class="result-item result-item--compact"
                    type="button"
                    :class="{ 'result-item--active': selectedInstrumentSymbol === item.symbol }"
                    @click="openInstrumentDetail(item)"
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
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="detail-header">
            <h4>Position bearbeiten: {{ detailHeading }}</h4>
            <div class="detail-actions" data-testid="detail-top-actions">
              <button class="btn" data-testid="detail-save-button" type="submit" form="holding-create-form" :disabled="saving">
                Holding hinzufügen
              </button>
              <button class="btn secondary" data-testid="detail-back-button" type="button" @click="backToSearch">← Zurück</button>
            </div>
          </div>
          <LoadingState v-if="profileLoading" />
          <ErrorState v-if="profileError" :message="profileError" />
          <form id="holding-create-form" class="holding-form" @submit.prevent="createHolding">
            <div class="grid three-col">
              <div v-if="hasValue(draftHolding.symbol)"><label>Symbol</label><div data-testid="holding-symbol" class="profile-description-block">{{ draftHolding.symbol }}</div></div>
              <div v-if="hasValue(draftHolding.isin)"><label>ISIN</label><div data-testid="holding-isin" class="profile-description-block">{{ draftHolding.isin }}</div></div>
              <div v-if="profileWkn"><label>WKN</label><div data-testid="holding-wkn" class="profile-description-block">{{ profileWkn }}</div></div>
              <div><label>Stückzahl</label><input data-testid="holding-quantity" class="input" v-model.number="draftHolding.quantity" type="number" min="0.000001" step="0.000001" required /></div>
              <div><label>Kaufkurs</label><input data-testid="holding-acquisition-price" class="input" v-model.number="draftHolding.acquisition_price" type="number" min="0.000001" step="0.000001" required /></div>
              <div v-if="hasValue(draftHolding.currency)"><label>Währung</label><div data-testid="holding-currency" class="profile-description-block">{{ draftHolding.currency }}</div></div>
              <div><label>Kaufdatum</label><input data-testid="holding-buy-date" class="input" v-model="draftHolding.buy_date" type="date" required /></div>
              <div v-if="hasValue(draftHolding.display_name)"><label>Name</label><div data-testid="holding-display-name" class="profile-description-block">{{ draftHolding.display_name }}</div></div>
              <div v-if="hasValue(draftHolding.company_name)"><label>Unternehmen</label><div data-testid="holding-company-name" class="profile-description-block">{{ draftHolding.company_name }}</div></div>
              <div v-if="hasValue(draftHolding.exchange)"><label>Börse</label><div data-testid="holding-exchange" class="profile-description-block">{{ draftHolding.exchange }}</div></div>
              <div v-if="profileQuoteType"><label>Quote-Type</label><div data-testid="holding-quote-type" class="profile-description-block">{{ profileQuoteType }}</div></div>
              <div v-if="profileAssetType"><label>Asset-Type</label><div data-testid="holding-asset-type" class="profile-description-block">{{ profileAssetType }}</div></div>
              <div class="wide"><label>Notiz</label><input data-testid="holding-notes" class="input" v-model.trim="draftHolding.notes" /></div>

              <div v-if="selectedProfile?.image" class="profile-logo-field">
                <label>Bild</label>
                <img
                  :src="selectedProfile.image"
                  :alt="`Logo ${selectedProfile.company_name || selectedProfile.symbol}`"
                  class="profile-image profile-image--inline"
                />
              </div>
              <div v-if="profileIndustry"><label>Industrie</label><div class="profile-description-block">{{ profileIndustry }}</div></div>
              <div v-if="profileWebsite"><label>Website</label><div class="profile-description-block"><a class="profile-link" :href="normalizeUrl(profileWebsite)" target="_blank" rel="noopener noreferrer">{{ profileWebsite }}</a></div></div>
              <div v-if="profileCeo"><label>CEO</label><div class="profile-description-block">{{ profileCeo }}</div></div>
              <div v-if="profileSector"><label>Sektor</label><div class="profile-description-block">{{ profileSector }}</div></div>
              <div v-if="profileCountry"><label>Land</label><div class="profile-description-block">{{ profileCountry }}</div></div>
              <div v-if="profilePhone"><label>Telefon</label><div class="profile-description-block">{{ profilePhone }}</div></div>
              <div v-if="profileAddressLine" class="wide"><label>Adresse</label><div class="profile-description-block">{{ profileAddressLine }}</div></div>
              <div v-if="profileDescription" class="wide">
                <label>Beschreibung</label>
                <div class="profile-description-block">{{ profileDescription }}</div>
              </div>
            </div>
          </form>
        </template>
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
import { useRoute, useRouter } from 'vue-router'
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
const route = useRoute()
const router = useRouter()
const searchListContainerRef = ref<HTMLElement | null>(null)

type SearchViewSnapshot = {
  searchQuery: string
  searchResults: InstrumentSearchItem[]
  searched: boolean
  selectedInstrumentSymbol: string | null
  scrollTop: number
}

const viewStateByContext = new Map<string, SearchViewSnapshot>()

type HoldingDraftState = HoldingCreatePayload & {
  acquisition_price: number | null
  exchange?: string | null
}

const draftHolding = ref<HoldingDraftState>(createDefaultDraftHolding())
const editHolding = ref({ quantity: 1, acquisition_price: 0, currency: 'EUR', buy_date: new Date().toISOString().slice(0, 10), notes: '' })
const MIN_SEARCH_LENGTH = 2
const SEARCH_DEBOUNCE_MS = 1000
let searchDebounceHandle: ReturnType<typeof setTimeout> | null = null
const selectedInstrumentSymbol = ref<string | null>(null)

const showEmptySearch = computed(() => searched.value && !searching.value && !searchError.value && searchResults.value.length === 0 && searchQuery.value.length >= MIN_SEARCH_LENGTH)
const selectedSymbolFromRoute = computed(() => (typeof route.query.symbol === 'string' ? route.query.symbol : ''))
const selectedDetailSymbol = ref('')
const isSearchView = computed(() => !selectedDetailSymbol.value)
const detailHeading = computed(() => selectedProfile.value?.company_name || selectedDetailSymbol.value)
const stateKey = computed(() => `${props.personId}::${props.depotLabel}`)
const searchHint = computed(() => {
  if (!searchQuery.value.length) return 'Suche startet beim Tippen.'
  if (searchQuery.value.length < MIN_SEARCH_LENGTH) return `Bitte mindestens ${MIN_SEARCH_LENGTH} Zeichen eingeben.`
  return null
})

const profileIndustry = computed(() => asText(selectedProfile.value?.industry))
const profileWebsite = computed(() => asText(selectedProfile.value?.website))
const profileCeo = computed(() => asText(selectedProfile.value?.ceo))
const profileSector = computed(() => asText(selectedProfile.value?.sector))
const profileCountry = computed(() => asText(selectedProfile.value?.country))
const profilePhone = computed(() => asText(selectedProfile.value?.phone))
const profileDescription = computed(() => asText(selectedProfile.value?.description))
const profileWkn = computed(() => asText(selectedProfile.value?.wkn))
const profileQuoteType = computed(() => asText(selectedProfile.value?.quote_type))
const profileAssetType = computed(() => asText(selectedProfile.value?.asset_type))
const profileAddressLine = computed(() => {
  const profile = selectedProfile.value
  if (!profile) return null
  if (hasValue(profile.address_line)) return String(profile.address_line).trim()
  const street = asText(profile.address)
  const zip = asText(profile.zip)
  const city = asText(profile.city)
  if (street && zip && city) return `${street}, ${zip} ${city}`
  return null
})

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
  }
}

function resetDraftHoldingForm() {
  draftHolding.value = createDefaultDraftHolding()
  selectedProfile.value = null
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

function asText(value: unknown) {
  if (!hasValue(value)) return null
  const text = String(value).trim()
  return text.length ? text : null
}

function normalizeUrl(url: string) {
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  return `https://${url}`
}

function buildDraftHoldingFromProfile(profile: MarketdataProfile) {
  return {
    symbol: profile.symbol,
    isin: typeof profile.isin === 'string' ? profile.isin : null,
    wkn: typeof profile.wkn === 'string' ? profile.wkn : null,
    display_name: typeof profile.company_name === 'string' ? profile.company_name : null,
    company_name: typeof profile.company_name === 'string' ? profile.company_name : null,
    exchange: typeof profile.exchange === 'string' ? profile.exchange : null,
    quantity: 1,
    acquisition_price: typeof profile.price === 'number' ? profile.price : null,
    currency: typeof profile.currency === 'string' ? profile.currency : 'EUR',
    buy_date: new Date().toISOString().slice(0, 10),
    notes: null,
  }
}

function preserveSearchScroll() {
  if (!searchListContainerRef.value) return
  const snapshot = viewStateByContext.get(stateKey.value)
  if (!snapshot) return
  snapshot.scrollTop = searchListContainerRef.value.scrollTop
}

async function openInstrumentDetail(item: InstrumentSearchItem) {
  preserveSearchScroll()
  selectedDetailSymbol.value = item.symbol
  selectedInstrumentSymbol.value = item.symbol
  void fetchInstrumentProfile(item.symbol)
  await router.push({
    query: {
      ...route.query,
      symbol: item.symbol,
      instrumentName: item.display_name || item.company_name || '',
    },
  })
}

async function fetchInstrumentProfile(symbol: string) {
  selectingSymbol.value = symbol
  profileError.value = null
  const requestId = ++activeProfileRequestId
  profileLoading.value = true
  try {
    const profile = await apiClient.marketdataProfile(symbol)
    if (requestId !== activeProfileRequestId) return
    selectedProfile.value = profile
    draftHolding.value = buildDraftHoldingFromProfile(profile)
    selectedInstrumentSymbol.value = symbol
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

async function backToSearch() {
  selectedDetailSymbol.value = ''
  await router.push({ query: { ...route.query, symbol: undefined, instrumentName: undefined } })
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
    await backToSearch()
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
watch([searchQuery, searchResults, searched, selectedInstrumentSymbol], () => {
  viewStateByContext.set(stateKey.value, {
    searchQuery: searchQuery.value,
    searchResults: [...searchResults.value],
    searched: searched.value,
    selectedInstrumentSymbol: selectedInstrumentSymbol.value,
    scrollTop: searchListContainerRef.value?.scrollTop ?? 0,
  })
}, { deep: true })
watch(selectedSymbolFromRoute, (symbol) => {
  selectedDetailSymbol.value = symbol
  if (!selectedDetailSymbol.value) {
    profileError.value = null
    profileLoading.value = false
    nextTick(() => {
      const snapshot = viewStateByContext.get(stateKey.value)
      if (!snapshot || !searchListContainerRef.value) return
      searchListContainerRef.value.scrollTop = snapshot.scrollTop
    })
    return
  }
  if (selectedProfile.value?.symbol === selectedDetailSymbol.value || selectingSymbol.value === selectedDetailSymbol.value) {
    return
  }
  void fetchInstrumentProfile(selectedDetailSymbol.value)
}, { immediate: true })
onMounted(() => { void load() })
onMounted(() => {
  const snapshot = viewStateByContext.get(stateKey.value)
  if (!snapshot) return
  searchQuery.value = snapshot.searchQuery
  searchResults.value = [...snapshot.searchResults]
  searched.value = snapshot.searched
  selectedInstrumentSymbol.value = snapshot.selectedInstrumentSymbol
})
onBeforeUnmount(() => {
  if (searchDebounceHandle) clearTimeout(searchDebounceHandle)
  preserveSearchScroll()
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
.search-panel { border: 1px solid #e2e8f0; border-radius: 8px; padding: .75rem; margin-bottom: .75rem; }
.detail-header { display: flex; justify-content: space-between; align-items: flex-start; gap: .75rem; margin-bottom: .75rem; }
.detail-actions { display: flex; justify-content: flex-end; gap: .5rem; }
.profile-image { width: 48px; height: 48px; object-fit: contain; border-radius: 6px; border: 1px solid #e2e8f0; background: #fff; }
.profile-image--inline { display: block; margin-top: .35rem; }
.profile-logo-field { display: flex; flex-direction: column; justify-content: flex-start; }
.profile-link { color: #1d4ed8; text-decoration: underline; word-break: break-all; }
.profile-description-block {
  margin-top: .35rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #f8fafc;
  padding: .6rem .7rem;
  font-size: .9rem;
  line-height: 1.45;
  white-space: pre-wrap;
}
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
