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
            <div class="detail-section">
              <h5>Instrument & Position</h5>
              <div class="grid three-col">
                <div v-if="hasValue(draftHolding.symbol)"><label>Symbol</label><div data-testid="holding-symbol" class="profile-description-block">{{ draftHolding.symbol }}</div></div>
                <div v-if="hasValue(draftHolding.isin)"><label>ISIN</label><div data-testid="holding-isin" class="profile-description-block">{{ draftHolding.isin }}</div></div>
                <div v-if="profileWkn"><label>WKN</label><div data-testid="holding-wkn" class="profile-description-block">{{ profileWkn }}</div></div>
                <div v-if="hasValue(draftHolding.display_name)"><label>Name</label><div data-testid="holding-display-name" class="profile-description-block">{{ draftHolding.display_name }}</div></div>
                <div v-if="hasValue(draftHolding.company_name)"><label>Unternehmen</label><div data-testid="holding-company-name" class="profile-description-block">{{ draftHolding.company_name }}</div></div>
                <div v-if="hasValue(draftHolding.exchange)"><label>Börse</label><div data-testid="holding-exchange" class="profile-description-block">{{ draftHolding.exchange }}</div></div>
                <div v-if="profileExchangeFullName"><label>Börsenplatz</label><div class="profile-description-block">{{ profileExchangeFullName }}</div></div>
                <div v-if="hasValue(draftHolding.currency)"><label>Währung</label><div data-testid="holding-currency" class="profile-description-block">{{ draftHolding.currency }}</div></div>
                <div><label>Stückzahl</label><input data-testid="holding-quantity" class="input" v-model.number="draftHolding.quantity" type="number" min="0.000001" step="0.000001" required /></div>
                <div><label>Kaufkurs</label><input data-testid="holding-acquisition-price" class="input" v-model.number="draftHolding.acquisition_price" type="number" min="0.000001" step="0.000001" required /></div>
                <div><label>Kaufdatum</label><input data-testid="holding-buy-date" class="input" v-model="draftHolding.buy_date" type="date" required /></div>
                <div class="wide"><label>Notiz</label><input data-testid="holding-notes" class="input" v-model.trim="draftHolding.notes" /></div>
              </div>
            </div>

            <div class="detail-section">
              <h5>Unternehmensprofil</h5>
              <div class="grid three-col">
                <div v-if="selectedProfile?.image" class="profile-logo-field">
                  <label>Bild</label>
                  <img
                    :src="selectedProfile.image"
                    :alt="`Logo ${selectedProfile.company_name || selectedProfile.symbol}`"
                    class="profile-image profile-image--inline"
                  />
                </div>
                <div v-if="profileIndustry"><label>Industrie</label><div class="profile-description-block">{{ profileIndustry }}</div></div>
                <div v-if="profileSector"><label>Sektor</label><div class="profile-description-block">{{ profileSector }}</div></div>
                <div v-if="profileQuoteType"><label>Quote-Type</label><div data-testid="holding-quote-type" class="profile-description-block">{{ profileQuoteType }}</div></div>
                <div v-if="profileAssetType"><label>Asset-Type</label><div data-testid="holding-asset-type" class="profile-description-block">{{ profileAssetType }}</div></div>
                <div v-if="profileWebsite"><label>Website</label><div class="profile-description-block"><a data-testid="holding-website-link" class="profile-link" :href="normalizeUrl(profileWebsite)" target="_blank" rel="noopener noreferrer">{{ profileWebsite }}</a></div></div>
                <div v-if="profileCeo"><label>CEO</label><div class="profile-description-block">{{ profileCeo }}</div></div>
                <div v-if="profileCountry"><label>Land</label><div class="profile-description-block">{{ profileCountry }}</div></div>
                <div v-if="profilePhone"><label>Telefon</label><div class="profile-description-block">{{ profilePhone }}</div></div>
                <div v-if="profileAddressLine" class="wide"><label>Adresse</label><div data-testid="holding-address" class="profile-description-block">{{ profileAddressLine }}</div></div>
              </div>
            </div>

            <div v-if="profileDescription" class="detail-section">
              <h5>Beschreibung</h5>
              <div data-testid="holding-description" class="profile-description-block profile-description-block--long">{{ profileDescription }}</div>
            </div>
          </form>
        </template>
      </section>

      <section v-if="showHoldingsSection">
        <div class="holdings-header">
          <h4>Vorhandene Positionen</h4>
          <p v-if="refreshLoading" class="muted">Tagespreise werden aktualisiert …</p>
        </div>
        <p v-if="refreshError" class="muted" data-testid="holdings-refresh-error">{{ refreshError }}</p>
        <section class="chart-card" data-testid="portfolio-chart-card">
          <PortfolioValueChart
            v-if="canRenderPortfolioChart"
            :points="portfolioChartPoints"
            :range="portfolioChartRange"
            :loading="chartLoading"
            :error="chartError || ''"
            @range-change="onPortfolioChartRangeChange"
          >
            <template #title>
              <h5 class="chart-title">Portfolio-Chart</h5>
            </template>
          </PortfolioValueChart>
          <p v-else class="muted" data-testid="portfolio-chart-currency-hint">
            Portfolio-Chart aktuell nur für einheitliche Depot-Währung verfügbar.
          </p>
          <p class="muted chart-meta" data-testid="portfolio-chart-meta">
            Stand: {{ chartLastUpdatedLabel }} · Range: {{ portfolioChartRange.toUpperCase() }}<span v-if="chartCacheHint"> · {{ chartCacheHint }}</span>
          </p>
        </section>
        <div v-if="holdingsForSummary.length" class="portfolio-summary" data-testid="portfolio-summary">
          <div class="summary-card">
            <p class="muted">Aktueller Gesamtwert</p>
            <p class="summary-value" data-testid="portfolio-summary-current-value">{{ formatCurrency(summaryMetrics.currentTotal, summaryMetrics.currency) }}</p>
            <p v-if="summaryMetrics.holdingsWithoutCurrentPrice > 0" class="muted">
              Teilweise auf Einstandswert geschätzt ({{ summaryMetrics.holdingsWithoutCurrentPrice }} ohne aktuellen Kurs).
            </p>
          </div>
          <div class="summary-card">
            <p class="muted">Investierter Wert</p>
            <p class="summary-value" data-testid="portfolio-summary-invested-value">{{ formatCurrency(summaryMetrics.investedTotal, summaryMetrics.currency) }}</p>
          </div>
          <div class="summary-card">
            <p class="muted">Gesamt Gewinn/Verlust</p>
            <p class="summary-value" :class="summaryMetrics.pnlClass" data-testid="portfolio-summary-pnl-value">
              {{ formatSignedCurrency(summaryMetrics.totalPnL, summaryMetrics.currency) }}
            </p>
          </div>
        </div>
        <div class="holding-filter">
          <label for="holding-filter-input">Position suchen</label>
          <input
            id="holding-filter-input"
            v-model.trim="holdingsFilterQuery"
            class="input"
            type="search"
            placeholder="Symbol, ISIN, Name oder Unternehmen"
          />
        </div>
        <LoadingState v-if="loading" />
        <EmptyState v-else-if="!portfolioDetail?.holdings.length">Keine Positionen vorhanden.</EmptyState>
        <EmptyState v-else-if="!filteredHoldings.length">Keine Positionen für den Suchbegriff gefunden.</EmptyState>
        <ul v-else class="holding-list">
          <li v-for="item in filteredHoldingsWithMetrics" :key="item.holding.holding_id" class="holding-item">
            <template v-if="editHoldingId !== item.holding.holding_id">
              <div class="holding-item-layout">
                <button
                  type="button"
                  class="holding-delete-button"
                  aria-label="Position löschen"
                  title="Position löschen"
                  @click.stop="removeHolding(item.holding.holding_id)"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" class="delete-icon">
                    <path d="M9 3h6l1 2h4v2H4V5h4l1-2Zm1 6h2v9h-2V9Zm4 0h2v9h-2V9ZM7 9h2v9H7V9Z" />
                  </svg>
                </button>
                <button
                  type="button"
                  class="holding-row-button"
                  :aria-label="`Position ${item.holding.symbol} bearbeiten`"
                  @click="startEdit(item.holding)"
                >
                  <p><strong>{{ item.holding.symbol }}</strong> · {{ item.holding.quantity }} Stück</p>
                  <div class="holding-metrics-grid">
                    <p data-testid="holding-acquisition-price-display"><span class="muted">Kaufkurs:</span> {{ formatCurrency(item.holding.acquisition_price, item.holding.currency) }}</p>
                    <p data-testid="holding-current-price-display"><span class="muted">Aktueller Kurs:</span> {{ item.currentPriceLabel }}</p>
                    <p data-testid="holding-pnl-display"><span class="muted">Gewinn/Verlust:</span> <span :class="item.pnlClass">{{ item.pnlLabel }}</span></p>
                    <p v-if="item.priceSourceLabel" data-testid="holding-price-source-display"><span class="muted">Preisquelle:</span> {{ item.priceSourceLabel }}</p>
                  </div>
                  <p class="muted">Kaufdatum: {{ item.holding.buy_date }} · {{ item.holding.notes || 'keine Notiz' }}</p>
                </button>
              </div>
            </template>

            <form v-else class="holding-form" @submit.prevent="saveEdit(item.holding.holding_id)">
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
import type {
  HoldingCreatePayload,
  InstrumentHistoryPoint,
  InstrumentHistoryRange,
  HoldingReadModel,
  InstrumentPriceRefreshResponse,
  InstrumentSearchItem,
  MarketdataProfile,
  PortfolioDetailReadModel,
  PortfolioReadModel
} from '@/shared/model/types'
import ErrorState from '@/shared/ui/ErrorState.vue'
import LoadingState from '@/shared/ui/LoadingState.vue'
import EmptyState from '@/shared/ui/EmptyState.vue'
import PortfolioValueChart from '@/shared/ui/PortfolioValueChart.vue'

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
const refreshLoading = ref(false)
const refreshError = ref<string | null>(null)
const currentPriceBySymbol = ref<Record<string, number>>({})
const refreshMetaBySymbol = ref<Record<string, InstrumentPriceRefreshResponse>>({})
const portfolioChartRange = ref<InstrumentHistoryRange>('3m')
const portfolioChartPoints = ref<Array<{ date: string; value: number }>>([])
const chartLoading = ref(false)
const chartError = ref<string | null>(null)
const chartLastUpdatedAt = ref<string | null>(null)
const chartCacheHint = ref<string | null>(null)
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
const holdingsFilterQuery = ref('')

type SearchViewSnapshot = {
  searchQuery: string
  searchResults: InstrumentSearchItem[]
  searched: boolean
  selectedInstrumentSymbol: string | null
  scrollTop: number
}

const viewStateByContext = new Map<string, SearchViewSnapshot>()

type HoldingDraftState = Omit<HoldingCreatePayload, 'acquisition_price'> & {
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
const profileExchangeFullName = computed(() => asText(selectedProfile.value?.exchange_full_name))
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
const filteredHoldings = computed(() => {
  const holdings = portfolioDetail.value?.holdings ?? []
  const query = holdingsFilterQuery.value.trim().toLowerCase()
  if (!query) return holdings
  return holdings.filter((holding) => {
    const searchableValues = [holding.symbol, holding.isin, holding.display_name, holding.company_name]
    return searchableValues.some((value) => typeof value === 'string' && value.toLowerCase().includes(query))
  })
})
const holdingsForSummary = computed(() => portfolioDetail.value?.holdings ?? [])
const holdingsCurrencies = computed(() => Array.from(new Set(holdingsForSummary.value.map((holding) => holding.currency).filter((currency) => typeof currency === 'string' && currency.trim().length > 0))))
const canRenderPortfolioChart = computed(() => holdingsForSummary.value.length > 0 && holdingsCurrencies.value.length <= 1)
const chartLastUpdatedLabel = computed(() => {
  if (!chartLastUpdatedAt.value) return '—'
  const date = new Date(chartLastUpdatedAt.value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('de-DE', { dateStyle: 'short', timeStyle: 'short' }).format(date)
})

type HoldingMetrics = {
  holding: HoldingReadModel
  currentPrice: number | null
  pnlAbsolute: number | null
  pnlPercent: number | null
  pnlClass: string
  currentPriceLabel: string
  pnlLabel: string
  priceSourceLabel: string | null
}

const filteredHoldingsWithMetrics = computed<HoldingMetrics[]>(() => {
  return filteredHoldings.value.map((holding) => {
    const currentPrice = getCurrentPriceForHolding(holding)
    const invested = holding.quantity * holding.acquisition_price
    const currentValue = holding.quantity * (currentPrice ?? holding.acquisition_price)
    const pnlAbsolute = currentValue - invested
    const pnlPercent = invested === 0 ? null : (pnlAbsolute / invested) * 100
    const pnlClass = pnlAbsolute >= 0 ? 'metric-positive' : 'metric-negative'
    const currentPriceLabel = currentPrice == null ? formatCurrency(holding.acquisition_price, holding.currency) : formatCurrency(currentPrice, holding.currency)
    const pnlLabel = `${formatSignedCurrency(pnlAbsolute, holding.currency)}${pnlPercent == null ? '' : ` (${formatSignedPercent(pnlPercent)})`}`
    const priceSource = refreshMetaBySymbol.value[normalizeSymbol(holding.symbol)]?.price_source
    const priceSourceLabel = priceSource === 'cache_today'
      ? 'Cache (heute)'
      : priceSource === 'yfinance_1d_1m'
        ? 'Live (yfinance)'
        : null
    return { holding, currentPrice, pnlAbsolute, pnlPercent, pnlClass, currentPriceLabel, pnlLabel, priceSourceLabel }
  })
})

const summaryMetrics = computed(() => {
  const holdings = holdingsForSummary.value
  const currency = holdings[0]?.currency ?? 'EUR'
  const investedTotal = holdings.reduce((sum, holding) => sum + (holding.quantity * holding.acquisition_price), 0)
  const currentTotal = holdings.reduce((sum, holding) => {
    const currentPrice = getCurrentPriceForHolding(holding)
    return sum + (holding.quantity * (currentPrice ?? holding.acquisition_price))
  }, 0)
  const holdingsWithoutCurrentPrice = holdings.filter((holding) => getCurrentPriceForHolding(holding) == null).length
  const totalPnL = currentTotal - investedTotal
  return {
    currency,
    investedTotal,
    currentTotal,
    holdingsWithoutCurrentPrice,
    totalPnL,
    pnlClass: totalPnL >= 0 ? 'metric-positive' : 'metric-negative',
  }
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
    await refreshHoldingsAndChart()
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

async function refreshHoldingsAndChart() {
  await refreshHoldingPrices()
  await loadPortfolioChartData()
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

function hasFiniteCurrentPrice(holding: HoldingReadModel) {
  return typeof holding.current_price === 'number' && Number.isFinite(holding.current_price)
}

function normalizeSymbol(symbol: string) {
  return symbol.trim().toUpperCase()
}

function getCurrentPriceForHolding(holding: HoldingReadModel) {
  const symbol = normalizeSymbol(holding.symbol)
  const cachedPrice = currentPriceBySymbol.value[symbol]
  if (typeof cachedPrice === 'number' && Number.isFinite(cachedPrice)) return cachedPrice
  return hasFiniteCurrentPrice(holding) ? Number(holding.current_price) : null
}

function formatCurrency(value: number, currency: string) {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency, maximumFractionDigits: 2 }).format(value)
}

function formatSignedCurrency(value: number, currency: string) {
  const amount = formatCurrency(Math.abs(value), currency)
  if (value > 0) return `+${amount}`
  if (value < 0) return `-${amount}`
  return amount
}

function formatSignedPercent(value: number) {
  const amount = new Intl.NumberFormat('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Math.abs(value))
  if (value > 0) return `+${amount} %`
  if (value < 0) return `-${amount} %`
  return `${amount} %`
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
  const confirmed = window.confirm('Position wirklich löschen?')
  if (!confirmed) return
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

async function refreshHoldingPrices() {
  if (!selectedPortfolioId.value) return
  const symbols = Array.from(new Set(holdingsForSummary.value.map((holding) => normalizeSymbol(holding.symbol)).filter(Boolean)))
  if (!symbols.length) return
  refreshLoading.value = true
  refreshError.value = null
  const failedSymbols: string[] = []
  try {
    const results = await Promise.allSettled(symbols.map((symbol) => apiClient.refreshInstrumentPrice(symbol)))
    results.forEach((result, index) => {
      const symbol = symbols[index]
      if (result.status === 'fulfilled') {
        currentPriceBySymbol.value = { ...currentPriceBySymbol.value, [symbol]: result.value.current_price }
        refreshMetaBySymbol.value = { ...refreshMetaBySymbol.value, [symbol]: result.value }
      } else {
        failedSymbols.push(symbol)
      }
    })
    if (failedSymbols.length > 0) {
      refreshError.value = `Kurs-Refresh fehlgeschlagen für: ${failedSymbols.join(', ')}`
    }
  } catch (e) {
    refreshError.value = e instanceof Error ? e.message : 'Kurs-Aktualisierung konnte nicht ausgelöst werden.'
  } finally {
    refreshLoading.value = false
  }
}

function buildPortfolioSeriesByHistory(
  holdings: HoldingReadModel[],
  historyBySymbol: Record<string, InstrumentHistoryPoint[]>
) {
  const allDates = new Set<string>()
  Object.values(historyBySymbol).forEach((points) => {
    points.forEach((point) => allDates.add(point.date))
  })
  const sortedDates = Array.from(allDates).sort((a, b) => a.localeCompare(b))
  const lastKnownCloseBySymbol: Record<string, number | null> = {}
  const firstKnownDateBySymbol: Record<string, string | null> = {}
  Object.entries(historyBySymbol).forEach(([symbol, points]) => {
    firstKnownDateBySymbol[symbol] = points[0]?.date ?? null
    lastKnownCloseBySymbol[symbol] = null
  })

  return sortedDates.map((date) => {
    let totalValue = 0
    holdings.forEach((holding) => {
      if (holding.buy_date > date) return
      const symbol = normalizeSymbol(holding.symbol)
      const points = historyBySymbol[symbol] ?? []
      const currentPoint = points.find((point) => point.date === date)
      if (currentPoint) {
        lastKnownCloseBySymbol[symbol] = currentPoint.close
      }
      const firstKnownDate = firstKnownDateBySymbol[symbol]
      if (!firstKnownDate || date < firstKnownDate) return
      const effectiveClose = lastKnownCloseBySymbol[symbol]
      if (typeof effectiveClose !== 'number' || !Number.isFinite(effectiveClose)) return
      totalValue += holding.quantity * effectiveClose
    })
    return { date, value: totalValue }
  })
}

async function loadPortfolioChartData() {
  chartError.value = null
  chartLastUpdatedAt.value = null
  chartCacheHint.value = null
  if (!canRenderPortfolioChart.value) {
    portfolioChartPoints.value = []
    return
  }
  const symbols = Array.from(new Set(holdingsForSummary.value.map((holding) => normalizeSymbol(holding.symbol)).filter(Boolean)))
  if (!symbols.length) {
    portfolioChartPoints.value = []
    return
  }
  chartLoading.value = true
  try {
    const results = await Promise.allSettled(symbols.map((symbol) => apiClient.instrumentHistory(symbol, portfolioChartRange.value)))
    const historyBySymbol: Record<string, InstrumentHistoryPoint[]> = {}
    let cachePresentCount = 0
    let latestUpdatedAt: string | null = null

    results.forEach((result, index) => {
      if (result.status !== 'fulfilled') return
      const symbol = symbols[index]
      historyBySymbol[symbol] = result.value.points ?? []
      if (result.value.cache_present) cachePresentCount += 1
      if (!latestUpdatedAt || result.value.updated_at > latestUpdatedAt) {
        latestUpdatedAt = result.value.updated_at
      }
    })

    if (!Object.keys(historyBySymbol).length) {
      portfolioChartPoints.value = []
      chartError.value = 'Kursverlauf konnte nicht geladen werden.'
      return
    }

    portfolioChartPoints.value = buildPortfolioSeriesByHistory(holdingsForSummary.value, historyBySymbol)
    chartLastUpdatedAt.value = latestUpdatedAt
    chartCacheHint.value = cachePresentCount > 0 ? `Cache-Hits: ${cachePresentCount}/${symbols.length}` : null
  } catch (e) {
    chartError.value = e instanceof Error ? e.message : 'Kursverlauf konnte nicht geladen werden.'
    portfolioChartPoints.value = []
  } finally {
    chartLoading.value = false
  }
}

async function onPortfolioChartRangeChange(nextRange: InstrumentHistoryRange) {
  if (nextRange === portfolioChartRange.value) return
  portfolioChartRange.value = nextRange
  await loadPortfolioChartData()
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
.holdings-header { display: flex; align-items: center; justify-content: space-between; gap: .75rem; flex-wrap: wrap; }
.chart-card {
  margin: .6rem 0 .8rem;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  padding: .7rem;
  background: #f8fbff;
}
.chart-title { margin: 0; font-size: .95rem; }
.chart-meta { margin-top: .35rem; }
.portfolio-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: .65rem;
  margin: .7rem 0;
}
.summary-card {
  border: 1px solid #dbeafe;
  border-radius: 8px;
  padding: .7rem;
  background: #f8fbff;
}
.summary-value { margin: .2rem 0; font-weight: 700; font-size: 1rem; }
.holding-list { list-style: none; padding: 0; display: grid; gap: .75rem; }
.holding-item { border: 1px solid #e2e8f0; border-radius: 8px; padding: .75rem; }
.holding-item-layout { display: grid; grid-template-columns: auto 1fr; align-items: stretch; gap: .6rem; }
.holding-row-button {
  width: 100%;
  text-align: left;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  color: inherit;
  padding: .7rem .75rem;
  cursor: pointer;
  transition: border-color .15s ease, box-shadow .15s ease, background-color .15s ease;
}
.holding-row-button:hover {
  border-color: #93c5fd;
  background: #f8fafc;
}
.holding-metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: .25rem .5rem;
  margin: .25rem 0;
  font-size: .92rem;
}
.metric-positive { color: #15803d; font-weight: 600; }
.metric-negative { color: #b91c1c; font-weight: 600; }
.metric-neutral { color: #475569; font-weight: 500; }
.holding-row-button:focus-visible {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 2px #bfdbfe;
}
.holding-delete-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  color: #475569;
  cursor: pointer;
  transition: color .15s ease, border-color .15s ease, background-color .15s ease;
}
.holding-delete-button:hover {
  color: #dc2626;
  border-color: #fca5a5;
  background: #fef2f2;
}
.holding-delete-button:focus-visible {
  outline: none;
  color: #dc2626;
  border-color: #ef4444;
  box-shadow: 0 0 0 2px #fecaca;
}
.delete-icon { width: 1.1rem; height: 1.1rem; fill: currentColor; }
.row-actions { display: flex; gap: .5rem; margin-top: .5rem; }
.holding-filter { margin-bottom: .6rem; display: grid; gap: .3rem; }
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
.detail-section { margin-bottom: 1rem; }
.detail-section h5 { margin: 0 0 .5rem; font-size: .95rem; }
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
.profile-description-block--long { max-height: 260px; overflow: auto; }
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
@media (max-width: 780px) {
  .holdings-header { align-items: flex-start; }
}
</style>
