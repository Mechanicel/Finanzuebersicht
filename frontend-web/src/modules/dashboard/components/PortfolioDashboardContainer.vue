<template>
  <section class="portfolio-cockpit">
    <header class="cockpit-header">
      <div>
        <p class="eyebrow">Portfolio-Cockpit</p>
        <h2>Portfolio Dashboard</h2>
      </div>
      <button class="btn flow-btn" type="button" @click="void loadAll()" :disabled="isReloading">Neu laden</button>
    </header>

    <LoadingState v-if="showGlobalLoading" />
    <ErrorState v-else-if="showGlobalError" :message="globalErrorMessage" />
    <EmptyState v-else-if="isEmpty && !hasAnyRenderableSection">
      Keine Portfolio-Daten für dieses Personenkonto verfügbar.
    </EmptyState>

    <template v-else>
      <PortfolioSummaryBar v-if="summary" :summary="summary" />
      <div v-else-if="isSectionLoading.summary" class="section-state">Summary wird geladen…</div>
      <div v-else-if="sectionErrors.summary" class="section-state section-state--error">
        <span>{{ sectionErrors.summary }}</span>
        <button class="btn flow-btn btn-small" type="button" @click="void loadSummary()">Erneut laden</button>
      </div>

      <section class="primary-grid top-row">
        <div>
          <PortfolioPerformancePanel v-if="performance" :performance="performance" :currency="summary?.currency" />
          <div v-else-if="isSectionLoading.performance" class="section-state">Performance wird geladen…</div>
          <div v-else-if="sectionErrors.performance" class="section-state section-state--error">
            <span>{{ sectionErrors.performance }}</span>
            <button class="btn flow-btn btn-small" type="button" @click="void loadPerformance()">Erneut laden</button>
          </div>
        </div>
        <div class="right-stack">
          <PortfolioRiskPanel v-if="risk" :risk="risk" />
          <div v-else-if="isSectionLoading.risk" class="section-state">Risiko wird geladen…</div>
          <div v-else-if="sectionErrors.risk" class="section-state section-state--error">
            <span>{{ sectionErrors.risk }}</span>
            <button class="btn flow-btn btn-small" type="button" @click="void loadRisk()">Erneut laden</button>
          </div>

          <PortfolioCoverageBanner v-if="coverage" :coverage="coverage" />
          <div v-else-if="isSectionLoading.coverage" class="section-state">Datenabdeckung wird geladen…</div>
          <div v-else-if="sectionErrors.coverage" class="section-state section-state--error">
            <span>{{ sectionErrors.coverage }}</span>
            <button class="btn flow-btn btn-small" type="button" @click="void loadCoverage()">Erneut laden</button>
          </div>
        </div>
      </section>

      <div class="workspace-grid" :class="{ 'workspace-grid--single': !holdings }">
        <PortfolioHoldingsTable
          v-if="holdings"
          :items="holdings.items"
          :currency="summary?.currency"
          :selected-symbol="selectedSymbol"
          :as-of="holdings.as_of"
          @select-holding="onSelectHolding"
        />
        <div v-else-if="isSectionLoading.holdings" class="section-state">Holdings werden geladen…</div>
        <div v-else-if="sectionErrors.holdings" class="section-state section-state--error">
          <span>{{ sectionErrors.holdings }}</span>
          <button class="btn flow-btn btn-small" type="button" @click="void loadHoldings()">Erneut laden</button>
        </div>
        <div class="workspace-right-stack">
          <PortfolioInstrumentDetailPanel :selected-holding="selectedHolding" :as-of="holdings?.as_of ?? summary?.as_of" />
          <section v-if="contributors" class="section-state section-state--compact">
            <div class="contributors-header">
              <div>
                <strong>Performance-Beiträge</strong>
                <p class="contributors-meta">
                  <strong>Zeitraum</strong>
                  <span>Stand: {{ contributorAsOfLabel }}</span>
                  <span>Zeitraum: {{ contributorRangeLabel }}</span>
                  <span v-if="contributorMethodologyLabel">Methodik: {{ contributorMethodologyLabel }}</span>
                </p>
              </div>
              <span>
                Top-Beiträger: {{ contributorCount }}
                ·
                Top-Belaster: {{ detractorCount }}
              </span>
            </div>
            <p v-if="contributorWarningsLabel" class="contributors-warning">Hinweise: {{ contributorWarningsLabel }}</p>
            <div v-if="hasContributorRows || hasDetractorRows" class="contributors-grid">
              <div v-if="hasContributorRows" class="contributors-list-block">
                <p class="contributors-list-title">Top-Beiträger</p>
                <ul class="contributors-list">
                  <li v-for="(item, index) in topContributorRows" :key="`contributor-${item.symbol ?? item.display_name ?? index}`">
                    <span class="contributors-name">{{ contributorName(item) }}</span>
                    <span class="contributors-value">{{ formatSignedPercentPoints(item.contribution_pct_points) }}</span>
                  </li>
                </ul>
              </div>
              <div v-if="hasDetractorRows" class="contributors-list-block">
                <p class="contributors-list-title">Top-Belaster</p>
                <ul class="contributors-list">
                  <li v-for="(item, index) in topDetractorRows" :key="`detractor-${item.symbol ?? item.display_name ?? index}`">
                    <span class="contributors-name">{{ contributorName(item) }}</span>
                    <span class="contributors-value">{{ formatSignedPercentPoints(item.contribution_pct_points) }}</span>
                  </li>
                </ul>
              </div>
            </div>
            <p v-else class="contributors-empty">Keine Beitragsdaten verfügbar.</p>
          </section>
          <div v-else-if="isSectionLoading.contributors" class="section-state">Performance-Beiträge werden geladen…</div>
          <div v-else-if="sectionErrors.contributors" class="section-state section-state--error">
            <span>{{ sectionErrors.contributors }}</span>
            <button class="btn flow-btn btn-small" type="button" @click="void loadContributors()">Erneut laden</button>
          </div>
        </div>
      </div>

      <PortfolioExposuresPanel v-if="exposures" :exposures="exposures" :currency="summary?.currency" />
      <div v-else-if="isSectionLoading.exposures" class="section-state">Exposures werden geladen…</div>
      <div v-else-if="sectionErrors.exposures" class="section-state section-state--error">
        <span>{{ sectionErrors.exposures }}</span>
        <button class="btn flow-btn btn-small" type="button" @click="void loadExposures()">Erneut laden</button>
      </div>

    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, watch, toRef, ref } from 'vue'
import EmptyState from '@/shared/ui/EmptyState.vue'
import ErrorState from '@/shared/ui/ErrorState.vue'
import LoadingState from '@/shared/ui/LoadingState.vue'
import PortfolioSummaryBar from '@/modules/dashboard/components/PortfolioSummaryBar.vue'
import PortfolioPerformancePanel from '@/modules/dashboard/components/PortfolioPerformancePanel.vue'
import PortfolioRiskPanel from '@/modules/dashboard/components/PortfolioRiskPanel.vue'
import PortfolioExposuresPanel from '@/modules/dashboard/components/PortfolioExposuresPanel.vue'
import PortfolioHoldingsTable from '@/modules/dashboard/components/PortfolioHoldingsTable.vue'
import PortfolioCoverageBanner from '@/modules/dashboard/components/PortfolioCoverageBanner.vue'
import PortfolioInstrumentDetailPanel from '@/modules/dashboard/components/PortfolioInstrumentDetailPanel.vue'
import { usePortfolioDashboard } from '@/modules/dashboard/composables/usePortfolioDashboard'
import {
  formatDate,
  formatNullableText,
  formatRangeLabel,
  formatSignedPercentPoints,
  getStringMeta,
  mapPortfolioMethodology,
  mapPortfolioWarning
} from '@/modules/dashboard/model/portfolioFormatting'
import type { PortfolioContributorItem, PortfolioHoldingItem } from '@/shared/model/types'

const props = defineProps<{ personId: string }>()

const personIdRef = toRef(props, 'personId')
const portfolioDashboard = usePortfolioDashboard(personIdRef)

const summary = computed(() => portfolioDashboard.dashboardSummary.value)
const performance = computed(() => portfolioDashboard.performance.value)
const exposures = computed(() => portfolioDashboard.exposures.value)
const holdings = computed(() => portfolioDashboard.holdings.value)
const risk = computed(() => portfolioDashboard.risk.value)
const coverage = computed(() => portfolioDashboard.coverage.value)
const contributors = computed(() => portfolioDashboard.contributors.value)

const isReloading = computed(() => portfolioDashboard.loading.value)
const error = computed(() => portfolioDashboard.error.value)
const isEmpty = computed(() => portfolioDashboard.isEmpty.value)
const isSectionLoading = computed(() => portfolioDashboard.loadingStates.value)
const sectionErrors = computed(() => portfolioDashboard.errors.value)

const loadAll = portfolioDashboard.loadAll
const loadSummary = portfolioDashboard.loadSummary
const loadPerformance = portfolioDashboard.loadPerformance
const loadExposures = portfolioDashboard.loadExposures
const loadHoldings = portfolioDashboard.loadHoldings
const loadRisk = portfolioDashboard.loadRisk
const loadContributors = portfolioDashboard.loadContributors
const loadCoverage = portfolioDashboard.loadCoverage

const hasAnyRenderableSection = computed(
  () => !!summary.value || !!performance.value || !!holdings.value || !!risk.value || !!coverage.value || !!exposures.value || !!contributors.value
)
const hasAnySectionLoading = computed(() => Object.values(isSectionLoading.value).some(Boolean))
const hasAnySectionError = computed(() => Object.values(sectionErrors.value).some((value) => Boolean(value)))
const showGlobalLoading = computed(() => !hasAnyRenderableSection.value && (isReloading.value || hasAnySectionLoading.value))
const globalErrorMessage = computed(() => error.value || 'Portfolio-Dashboard-Daten konnten nicht geladen werden.')
const showGlobalError = computed(() => !hasAnyRenderableSection.value && !showGlobalLoading.value && (Boolean(error.value) || hasAnySectionError.value))
const selectedSymbol = ref<string | null>(null)
const fallbackHolding = (items: PortfolioHoldingItem[]) => items.find((item) => item.symbol) ?? items[0] ?? null
const selectedHolding = computed<PortfolioHoldingItem | null>(() => {
  const items = holdings.value?.items ?? []
  if (!items.length) return null
  if (!selectedSymbol.value) return fallbackHolding(items)
  return items.find((item) => item.symbol === selectedSymbol.value) ?? fallbackHolding(items)
})
const topContributorRows = computed(() => (contributors.value?.top_contributors ?? []).slice(0, 5))
const topDetractorRows = computed(() => (contributors.value?.top_detractors ?? []).slice(0, 5))
const contributorCount = computed(() => contributors.value?.top_contributors?.length ?? 0)
const detractorCount = computed(() => contributors.value?.top_detractors?.length ?? 0)
const hasContributorRows = computed(() => topContributorRows.value.length > 0)
const hasDetractorRows = computed(() => topDetractorRows.value.length > 0)
const contributorAsOfLabel = computed(() =>
  formatDate(getStringMeta(contributors.value?.meta, 'as_of', 'generated_at', 'updated_at') ?? contributors.value?.as_of ?? summary.value?.as_of)
)
const contributorRangeLabel = computed(() =>
  formatRangeLabel(
    contributors.value?.range ?? getStringMeta(contributors.value?.meta, 'range') ?? performance.value?.range,
    contributors.value?.range_label ?? getStringMeta(contributors.value?.meta, 'range_label') ?? performance.value?.range_label
  )
)
const contributorMethodologyLabel = computed(() => {
  const methodology =
    contributors.value?.methodology ??
    getStringMeta(contributors.value?.meta, 'methodology', 'return_basis') ??
    contributors.value?.return_basis
  return methodology ? mapPortfolioMethodology(methodology) : ''
})
const contributorWarningsLabel = computed(() =>
  (contributors.value?.warnings ?? [])
    .filter((warning) => warning.trim().length > 0)
    .slice(0, 4)
    .map((warning) => mapPortfolioWarning(warning))
    .join(', ')
)

function onSelectHolding(item: PortfolioHoldingItem) {
  selectedSymbol.value = item.symbol ?? null
}

function contributorName(item: PortfolioContributorItem) {
  return formatNullableText(item.display_name, '') || formatNullableText(item.symbol)
}

watch(
  () => holdings.value?.items,
  (items) => {
    if (!items || !items.length) {
      selectedSymbol.value = null
      return
    }
    const hasSelection = selectedSymbol.value && items.some((item) => item.symbol === selectedSymbol.value)
    if (!hasSelection) {
      selectedSymbol.value = fallbackHolding(items)?.symbol ?? null
    }
  },
  { immediate: true }
)

watch(
  personIdRef,
  (newPersonId) => {
    if (newPersonId) {
      void loadAll()
    }
  },
  { immediate: false }
)

onMounted(() => {
  if (props.personId) {
    void loadAll()
  }
})
</script>

<style scoped>
.portfolio-cockpit {
  display: grid;
  gap: 0.85rem;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  padding: 1rem;
  background: #f8fafc;
}

.cockpit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.eyebrow {
  margin: 0;
  color: #475569;
  font-weight: 600;
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

h2 {
  margin: 0.2rem 0 0;
  font-size: 1.25rem;
}

.workspace-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 0.8fr);
  gap: 0.75rem;
  align-items: start;
  grid-auto-rows: min-content;
}

.workspace-grid--single {
  grid-template-columns: minmax(0, 1fr);
}

.primary-grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  gap: 0.75rem;
}

.top-row {
  align-items: start;
  grid-auto-rows: min-content;
}


.top-row > *,
.workspace-grid > * {
  height: auto;
  align-self: start;
}
.right-stack {
  display: grid;
  gap: 0.55rem;
}

.workspace-right-stack {
  display: grid;
  gap: 0.5rem;
  align-items: start;
}

.section-state {
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  background: #ffffff;
  color: #334155;
  padding: 0.75rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.section-state--error {
  border-color: #fecaca;
  background: #fff1f2;
  color: #9f1239;
  justify-content: space-between;
}

.section-state--neutral {
  justify-content: space-between;
}

.section-state--compact {
  display: grid;
  gap: 0.45rem;
  padding: 0.65rem;
}

.contributors-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
  font-size: 0.82rem;
}

.contributors-meta {
  margin: 0.14rem 0 0;
  color: #64748b;
  font-size: 0.76rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.contributors-meta strong {
  color: #334155;
}

.contributors-warning,
.contributors-empty {
  margin: 0;
  font-size: 0.76rem;
  color: #92400e;
}

.contributors-empty {
  color: #64748b;
}

.contributors-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem;
}

.contributors-list-block {
  display: grid;
  gap: 0.2rem;
}

.contributors-list-title {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.contributors-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.16rem;
  font-size: 0.8rem;
}

.contributors-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.3rem;
}

.contributors-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.contributors-value {
  font-variant-numeric: tabular-nums;
  color: #0f172a;
}

.btn-small {
  font-size: 0.82rem;
  padding: 0.35rem 0.6rem;
}

@media (max-width: 900px) {
  .primary-grid,
  .workspace-grid {
    grid-template-columns: 1fr;
  }

  .contributors-grid {
    grid-template-columns: 1fr;
  }
}
</style>
