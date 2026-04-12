import { computed, ref, unref, type Ref } from 'vue'
import { extractApiErrorMessage } from '@/shared/api/extractApiErrorMessage'
import {
  fetchPortfolioDashboard,
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
  PortfolioDashboardReadModel,
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
  contributors: false,
  coverage: false
}

const errorsDefault = {
  summary: '',
  performance: '',
  exposures: '',
  holdings: '',
  risk: '',
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

  async function loadRisk(version = loadVersion.value) {
    loadingStates.value.risk = true
    errors.value.risk = ''
    try {
      const payload = await fetchPortfolioRisk(currentPersonId())
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

  async function loadContributors(version = loadVersion.value) {
    loadingStates.value.contributors = true
    errors.value.contributors = ''
    try {
      const payload = await fetchPortfolioContributors(currentPersonId())
      if (isCurrentLoad(version)) {
        contributors.value = payload
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

  async function runSectionLoad<T>(loader: () => Promise<T>) {
    try {
      const value = await loader()
      return { status: 'fulfilled', value } as const
    } catch (reason) {
      return { status: 'rejected', reason } as const
    }
  }

  async function loadInOrder(version: number) {
    const results = [] as Array<
      | { status: 'fulfilled'; value: unknown }
      | { status: 'rejected'; reason: unknown }
    >

    results.push(await runSectionLoad(() => loadSummary(version)))
    results.push(await runSectionLoad(() => loadPerformance(version)))
    results.push(await runSectionLoad(() => loadHoldings(version)))
    results.push(await runSectionLoad(() => loadRisk(version)))
    results.push(await runSectionLoad(() => loadContributors(version)))
    results.push(await runSectionLoad(() => loadCoverage(version)))
    results.push(await runSectionLoad(() => loadExposures(version)))

    return results
  }

  async function loadInitial() {
    const version = ++loadVersion.value
    return loadInOrder(version)
  }

  async function loadSecondary() {
    return Promise.allSettled([])
  }

  async function loadBootstrap(range = '3m'): Promise<PortfolioDashboardReadModel> {
    const version = ++loadVersion.value
    const keys: SectionKey[] = ['summary', 'performance', 'exposures', 'holdings', 'risk', 'contributors', 'coverage']
    keys.forEach((key) => {
      loadingStates.value[key] = true
      errors.value[key] = ''
    })

    try {
      const payload = await fetchPortfolioDashboard(currentPersonId(), range)
      if (isCurrentLoad(version)) {
        summary.value = payload.summary
        performance.value = payload.performance
        exposures.value = payload.exposures
        holdings.value = payload.holdings
        risk.value = payload.risk
        contributors.value = payload.contributors
        coverage.value = payload.coverage
      }
      return payload
    } catch (rawError) {
      const message = normalizeError(rawError, 'Portfolio-Dashboard-Daten konnten nicht geladen werden.')
      if (isCurrentLoad(version)) {
        keys.forEach((key) => {
          errors.value[key] = message
        })
      }
      throw rawError
    } finally {
      if (isCurrentLoad(version)) {
        keys.forEach((key) => {
          loadingStates.value[key] = false
        })
      }
    }
  }

  async function loadAll() {
    loading.value = true
    clearErrors()
    const version = ++loadVersion.value
    try {
      const results = await loadInOrder(version)
      const fulfilledCount = results.filter((result) => result.status === 'fulfilled').length
      if (fulfilledCount === 0) {
        error.value = 'Portfolio-Dashboard-Daten konnten nicht vollständig geladen werden.'
      }
      return results
    } finally {
      if (isCurrentLoad(version)) {
        loading.value = false
      }
    }
  }

  const dashboardSummary = computed(() => holdings.value?.summary ?? summary.value)

  const hasData = computed(
    () =>
      !!dashboardSummary.value ||
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
    loadContributors,
    loadCoverage,
    hasData,
    hasCoverageWarnings,
    topHoldings,
    isEmpty
  }
}
