import { computed, ref, unref, type Ref } from 'vue'
import { extractApiErrorMessage } from '@/shared/api/extractApiErrorMessage'
import {
  fetchPortfolioContributors,
  fetchPortfolioDataCoverage,
  fetchPortfolioExposures,
  fetchPortfolioHoldings,
  fetchPortfolioPerformance,
  fetchPortfolioRisk,
  fetchPortfolioSummary
} from '@/modules/dashboard/api/portfolioDashboardApi'
import type {
  PortfolioContributorsReadModel,
  PortfolioDataCoverageReadModel,
  PortfolioExposuresReadModel,
  PortfolioHoldingsReadModel,
  PortfolioPerformanceReadModel,
  PortfolioRiskReadModel,
  PortfolioSummaryReadModel
} from '@/shared/model/types'

type MaybeRef<T> = T | Ref<T>

export function usePortfolioDashboard(personId: MaybeRef<string>) {
  const currentPersonId = () => unref(personId)
  const summary = ref<PortfolioSummaryReadModel | null>(null)
  const performance = ref<PortfolioPerformanceReadModel | null>(null)
  const exposures = ref<PortfolioExposuresReadModel | null>(null)
  const holdings = ref<PortfolioHoldingsReadModel | null>(null)
  const risk = ref<PortfolioRiskReadModel | null>(null)
  const contributors = ref<PortfolioContributorsReadModel | null>(null)
  const coverage = ref<PortfolioDataCoverageReadModel | null>(null)

  const loading = ref(false)
  const loadingStates = ref({
    summary: false,
    performance: false,
    exposures: false,
    holdings: false,
    risk: false,
    contributors: false,
    coverage: false
  })

  const error = ref('')
  const errors = ref({
    summary: '',
    performance: '',
    exposures: '',
    holdings: '',
    risk: '',
    contributors: '',
    coverage: ''
  })

  function normalizeError(rawError: unknown, fallbackMessage: string): string {
    return extractApiErrorMessage(rawError, fallbackMessage)
  }

  function clearErrors() {
    error.value = ''
    errors.value = {
      summary: '',
      performance: '',
      exposures: '',
      holdings: '',
      risk: '',
      contributors: '',
      coverage: ''
    }
  }

  async function loadSummary() {
    loadingStates.value.summary = true
    errors.value.summary = ''
    try {
      summary.value = await fetchPortfolioSummary(currentPersonId())
      return summary.value
    } catch (rawError) {
      const message = normalizeError(rawError, 'Portfolio Summary konnte nicht geladen werden.')
      errors.value.summary = message
      throw rawError
    } finally {
      loadingStates.value.summary = false
    }
  }

  async function loadPerformance() {
    loadingStates.value.performance = true
    errors.value.performance = ''
    try {
      performance.value = await fetchPortfolioPerformance(currentPersonId())
      return performance.value
    } catch (rawError) {
      const message = normalizeError(rawError, 'Portfolio Performance konnte nicht geladen werden.')
      errors.value.performance = message
      throw rawError
    } finally {
      loadingStates.value.performance = false
    }
  }

  async function loadExposures() {
    loadingStates.value.exposures = true
    errors.value.exposures = ''
    try {
      exposures.value = await fetchPortfolioExposures(currentPersonId())
      return exposures.value
    } catch (rawError) {
      const message = normalizeError(rawError, 'Portfolio Exposures konnten nicht geladen werden.')
      errors.value.exposures = message
      throw rawError
    } finally {
      loadingStates.value.exposures = false
    }
  }

  async function loadHoldings() {
    loadingStates.value.holdings = true
    errors.value.holdings = ''
    try {
      holdings.value = await fetchPortfolioHoldings(currentPersonId())
      return holdings.value
    } catch (rawError) {
      const message = normalizeError(rawError, 'Portfolio Holdings konnten nicht geladen werden.')
      errors.value.holdings = message
      throw rawError
    } finally {
      loadingStates.value.holdings = false
    }
  }

  async function loadRisk() {
    loadingStates.value.risk = true
    errors.value.risk = ''
    try {
      risk.value = await fetchPortfolioRisk(currentPersonId())
      return risk.value
    } catch (rawError) {
      const message = normalizeError(rawError, 'Portfolio Risk konnte nicht geladen werden.')
      errors.value.risk = message
      throw rawError
    } finally {
      loadingStates.value.risk = false
    }
  }

  async function loadContributors() {
    loadingStates.value.contributors = true
    errors.value.contributors = ''
    try {
      contributors.value = await fetchPortfolioContributors(currentPersonId())
      return contributors.value
    } catch (rawError) {
      const message = normalizeError(rawError, 'Portfolio Contributors konnten nicht geladen werden.')
      errors.value.contributors = message
      throw rawError
    } finally {
      loadingStates.value.contributors = false
    }
  }

  async function loadCoverage() {
    loadingStates.value.coverage = true
    errors.value.coverage = ''
    try {
      coverage.value = await fetchPortfolioDataCoverage(currentPersonId())
      return coverage.value
    } catch (rawError) {
      const message = normalizeError(rawError, 'Portfolio Data Coverage konnte nicht geladen werden.')
      errors.value.coverage = message
      throw rawError
    } finally {
      loadingStates.value.coverage = false
    }
  }

  async function loadInitial() {
    return Promise.allSettled([loadSummary(), loadHoldings(), loadCoverage()])
  }

  async function loadSecondary() {
    return Promise.allSettled([loadPerformance(), loadRisk(), loadExposures()])
  }

  async function loadAll() {
    loading.value = true
    clearErrors()

    const initialResults = await loadInitial()
    const secondaryResults = await loadSecondary()
    const results = [...initialResults, ...secondaryResults]

    const firstError = results.find((result) => result.status === 'rejected')
    if (firstError) {
      error.value = normalizeError(
        firstError.reason,
        'Portfolio-Dashboard-Daten konnten nicht vollständig geladen werden.'
      )
    }

    loading.value = false
    return results
  }

  const hasData = computed(
    () =>
      !!summary.value ||
      !!performance.value ||
      !!exposures.value ||
      !!holdings.value ||
      !!risk.value ||
      !!contributors.value ||
      !!coverage.value
  )

  const hasCoverageWarnings = computed(() => (coverage.value?.warnings?.length ?? 0) > 0)

  const topHoldings = computed(() => {
    const items = holdings.value?.items ?? []
    return [...items].sort((left, right) => right.market_value - left.market_value).slice(0, 5)
  })

  const isEmpty = computed(() => {
    const holdingsCount = holdings.value?.items?.length ?? 0
    const marketValue = summary.value?.market_value ?? 0
    return !loading.value && holdingsCount === 0 && marketValue <= 0
  })

  return {
    summary,
    performance,
    exposures,
    holdings,
    risk,
    contributors,
    coverage,
    loading,
    loadingStates,
    error,
    errors,
    loadInitial,
    loadSecondary,
    loadAll,
    loadSummary,
    loadPerformance,
    loadExposures,
    loadHoldings,
    loadRisk,
    loadContributors,
    loadCoverage,
    hasData,
    hasCoverageWarnings,
    topHoldings,
    isEmpty
  }
}
