import { computed, ref, unref, type Ref } from 'vue'
import { extractApiErrorMessage } from '@/shared/api/extractApiErrorMessage'
import {
  fetchPortfolioAttribution,
  fetchPortfolioContributors,
  fetchPortfolioDataCoverage,
  fetchPortfolioExposures,
  fetchPortfolioHoldings,
  fetchPortfolioPerformance,
  fetchPortfolioRisk,
  fetchPortfolioSummary
} from '@/modules/dashboard/api/portfolioDashboardApi'
import { resolvePortfolioAttribution } from '@/modules/dashboard/model/portfolioAttribution'
import type {
  PortfolioAttributionReadModel,
  PortfolioContributorsReadModel,
  PortfolioDashboardRange,
  PortfolioDataCoverageReadModel,
  PortfolioExposuresReadModel,
  PortfolioHoldingsReadModel,
  PortfolioPerformanceReadModel,
  PortfolioRiskReadModel,
  PortfolioSummaryReadModel
} from '@/shared/model/types'

type MaybeRef<T> = T | Ref<T>
type SectionKey = keyof typeof loadingStatesDefault

const loadingStatesDefault = {
  summary: false,
  performance: false,
  exposures: false,
  holdings: false,
  risk: false,
  attribution: false,
  contributors: false,
  coverage: false
}

const errorsDefault = {
  summary: '',
  performance: '',
  exposures: '',
  holdings: '',
  risk: '',
  attribution: '',
  contributors: '',
  coverage: ''
}

export function usePortfolioDashboard(personId: MaybeRef<string>) {
  const currentPersonId = () => unref(personId)
  const summary = ref<PortfolioSummaryReadModel | null>(null)
  const performance = ref<PortfolioPerformanceReadModel | null>(null)
  const exposures = ref<PortfolioExposuresReadModel | null>(null)
  const holdings = ref<PortfolioHoldingsReadModel | null>(null)
  const risk = ref<PortfolioRiskReadModel | null>(null)
  const contributors = ref<PortfolioContributorsReadModel | null>(null)
  const attribution = ref<PortfolioAttributionReadModel | null>(null)
  const coverage = ref<PortfolioDataCoverageReadModel | null>(null)

  const loading = ref(false)
  const loadingStates = ref({ ...loadingStatesDefault })

  const error = ref('')
  const errors = ref({ ...errorsDefault })
  const loadVersion = ref(0)

  function normalizeError(rawError: unknown, fallbackMessage: string): string {
    return extractApiErrorMessage(rawError, fallbackMessage)
  }

  function clearErrors() {
    error.value = ''
    errors.value = { ...errorsDefault }
  }

  function isCurrentLoad(version: number) {
    return loadVersion.value === version
  }

  function updateAttribution(rawAttribution?: PortfolioAttributionReadModel | null) {
    attribution.value = resolvePortfolioAttribution({
      attribution: rawAttribution ?? attribution.value,
      contributors: contributors.value,
      performance: performance.value,
      risk: risk.value,
      personId: currentPersonId()
    })
  }

  async function loadSummary(version = loadVersion.value) {
    loadingStates.value.summary = true
    errors.value.summary = ''
    try {
      const payload = await fetchPortfolioSummary(currentPersonId())
      if (isCurrentLoad(version)) {
        summary.value = payload
      }
      return payload
    } catch (rawError) {
      const message = normalizeError(rawError, 'Portfolio Summary konnte nicht geladen werden.')
      if (isCurrentLoad(version)) {
        errors.value.summary = message
      }
      throw rawError
    } finally {
      if (isCurrentLoad(version)) {
        loadingStates.value.summary = false
      }
    }
  }

  async function loadPerformance(version = loadVersion.value) {
    loadingStates.value.performance = true
    errors.value.performance = ''
    try {
      const payload = await fetchPortfolioPerformance(currentPersonId())
      if (isCurrentLoad(version)) {
        performance.value = payload
      }
      return payload
    } catch (rawError) {
      const message = normalizeError(rawError, 'Portfolio Performance konnte nicht geladen werden.')
      if (isCurrentLoad(version)) {
        errors.value.performance = message
      }
      throw rawError
    } finally {
      if (isCurrentLoad(version)) {
        loadingStates.value.performance = false
      }
    }
  }

  async function loadExposures(version = loadVersion.value) {
    loadingStates.value.exposures = true
    errors.value.exposures = ''
    try {
      const payload = await fetchPortfolioExposures(currentPersonId())
      if (isCurrentLoad(version)) {
        exposures.value = payload
      }
      return payload
    } catch (rawError) {
      const message = normalizeError(rawError, 'Portfolio Exposures konnten nicht geladen werden.')
      if (isCurrentLoad(version)) {
        errors.value.exposures = message
      }
      throw rawError
    } finally {
      if (isCurrentLoad(version)) {
        loadingStates.value.exposures = false
      }
    }
  }

  async function loadHoldings(version = loadVersion.value) {
    loadingStates.value.holdings = true
    errors.value.holdings = ''
    try {
      const payload = await fetchPortfolioHoldings(currentPersonId())
      if (isCurrentLoad(version)) {
        holdings.value = payload
      }
      return payload
    } catch (rawError) {
      const message = normalizeError(rawError, 'Portfolio Holdings konnten nicht geladen werden.')
      if (isCurrentLoad(version)) {
        errors.value.holdings = message
      }
      throw rawError
    } finally {
      if (isCurrentLoad(version)) {
        loadingStates.value.holdings = false
      }
    }
  }

  async function loadRisk(range: PortfolioDashboardRange | string = '3m', version = loadVersion.value) {
    loadingStates.value.risk = true
    errors.value.risk = ''
    try {
      const payload = await fetchPortfolioRisk(currentPersonId(), range)
      if (isCurrentLoad(version)) {
        risk.value = payload
      }
      return payload
    } catch (rawError) {
      const message = normalizeError(rawError, 'Portfolio Risk konnte nicht geladen werden.')
      if (isCurrentLoad(version)) {
        errors.value.risk = message
      }
      throw rawError
    } finally {
      if (isCurrentLoad(version)) {
        loadingStates.value.risk = false
      }
    }
  }

  async function loadContributors(range: PortfolioDashboardRange | string = '3m', version = loadVersion.value) {
    loadingStates.value.contributors = true
    errors.value.contributors = ''
    try {
      const payload = await fetchPortfolioContributors(currentPersonId(), range)
      if (isCurrentLoad(version)) {
        contributors.value = payload
        updateAttribution()
      }
      return payload
    } catch (rawError) {
      const message = normalizeError(rawError, 'Portfolio Contributors konnten nicht geladen werden.')
      if (isCurrentLoad(version)) {
        errors.value.contributors = message
      }
      throw rawError
    } finally {
      if (isCurrentLoad(version)) {
        loadingStates.value.contributors = false
      }
    }
  }

  async function loadAttribution(range: PortfolioDashboardRange | string = '3m', version = loadVersion.value) {
    loadingStates.value.attribution = true
    errors.value.attribution = ''
    try {
      const payload = await fetchPortfolioAttribution(currentPersonId(), range)
      if (isCurrentLoad(version)) {
        attribution.value = payload
      }
      return payload
    } catch (rawError) {
      const message = normalizeError(rawError, 'Portfolio Attribution konnte nicht geladen werden.')
      if (isCurrentLoad(version)) {
        errors.value.attribution = message
      }
      throw rawError
    } finally {
      if (isCurrentLoad(version)) {
        loadingStates.value.attribution = false
      }
    }
  }

  async function loadCoverage(version = loadVersion.value) {
    loadingStates.value.coverage = true
    errors.value.coverage = ''
    try {
      const payload = await fetchPortfolioDataCoverage(currentPersonId())
      if (isCurrentLoad(version)) {
        coverage.value = payload
      }
      return payload
    } catch (rawError) {
      const message = normalizeError(rawError, 'Portfolio Data Coverage konnte nicht geladen werden.')
      if (isCurrentLoad(version)) {
        errors.value.coverage = message
      }
      throw rawError
    } finally {
      if (isCurrentLoad(version)) {
        loadingStates.value.coverage = false
      }
    }
  }

  async function loadInitial(range: PortfolioDashboardRange | string = '3m') {
    return loadBootstrap(range)
  }

  async function loadSecondary() {
    return Promise.allSettled([])
  }

  async function loadBootstrap(range: PortfolioDashboardRange | string = '3m'): Promise<void> {
    loading.value = true
    clearErrors()
    const version = ++loadVersion.value

    const allKeys: SectionKey[] = ['summary', 'performance', 'exposures', 'holdings', 'risk', 'attribution', 'contributors', 'coverage']
    allKeys.forEach((key) => {
      loadingStates.value[key] = true
      errors.value[key] = ''
    })

    // Phase 1: fast — DB reads + cached prices; renders UI as soon as these settle
    await Promise.allSettled([
      loadSummary(version),
      loadHoldings(version),
      loadExposures(version)
    ])

    if (!isCurrentLoad(version)) return
    loading.value = false

    // Phase 2: slow — time-series calculations; non-blocking, errors are section-level
    void Promise.allSettled([
      loadPerformance(version),
      loadRisk(range, version),
      loadAttribution(range, version),
      loadContributors(range, version),
      loadCoverage(version)
    ])
  }

  async function loadAll(range: PortfolioDashboardRange | string = '3m') {
    return loadBootstrap(range)
  }

  const dashboardSummary = computed(() => holdings.value?.summary ?? summary.value)

  const hasData = computed(
    () =>
      !!dashboardSummary.value ||
      !!performance.value ||
      !!exposures.value ||
      !!holdings.value ||
      !!risk.value ||
      !!attribution.value ||
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
    const marketValue = dashboardSummary.value?.market_value ?? 0
    return !loading.value && holdingsCount === 0 && marketValue <= 0
  })

  return {
    summary,
    dashboardSummary,
    performance,
    exposures,
    holdings,
    risk,
    contributors,
    attribution,
    coverage,
    loading,
    loadingStates,
    error,
    errors,
    loadInitial,
    loadSecondary,
    loadAll,
    loadBootstrap,
    loadSummary,
    loadPerformance,
    loadExposures,
    loadHoldings,
    loadRisk,
    loadAttribution,
    loadContributors,
    loadCoverage,
    hasData,
    hasCoverageWarnings,
    topHoldings,
    isEmpty
  }
}
