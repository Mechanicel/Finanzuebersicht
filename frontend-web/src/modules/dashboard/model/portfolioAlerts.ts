import type {
  PortfolioContributorsReadModel,
  PortfolioDataCoverageReadModel,
  PortfolioRiskReadModel,
  PortfolioSummaryReadModel
} from '@/shared/model/types'
import {
  formatPercent,
  formatSignedPercentFromRatio,
  formatSignedPercentPoints
} from '@/modules/dashboard/model/portfolioFormatting'

export type PortfolioAlertSeverity = 'kritisch' | 'warnung' | 'info'
export type PortfolioAlertSourceKey = 'concentration' | 'coverage' | 'risk' | 'contributors' | 'summary'

interface ThresholdBand {
  warning: number
  critical: number
}

export interface PortfolioAlert {
  id: string
  severity: PortfolioAlertSeverity
  priority: number
  title: string
  detail: string
  source: string
  sourceKey: PortfolioAlertSourceKey
  sourceLabel: string
  actionHint: string
}

export interface PortfolioAlertSources {
  summary?: PortfolioSummaryReadModel | null
  risk?: PortfolioRiskReadModel | null
  coverage?: PortfolioDataCoverageReadModel | null
  contributors?: PortfolioContributorsReadModel | null
}

export interface PortfolioAlertRuleConfig {
  maxAlerts: number
  smallPortfolioMaxHoldings: number
  minHoldingsForConcentrationBreach: number
  concentration: {
    topPosition: ThresholdBand
    top3: ThresholdBand
  }
  risk: {
    annualizedVolatility: ThresholdBand
    dailyVolatility: ThresholdBand
    annualizedTrackingError: ThresholdBand
    dailyTrackingError: ThresholdBand
    maxDrawdown: ThresholdBand
  }
  coverage: {
    missingPricesCriticalFrom: number
    qualityGapWarningFrom: number
  }
  contributors: {
    contributionReturnCriticalBelow: number
    contributionPercentPointsCriticalBelow: number
  }
}

export interface BuildPortfolioAlertsOptions {
  maxAlerts?: number
  config?: PartialPortfolioAlertRuleConfig
}

export type PartialPortfolioAlertRuleConfig = Partial<{
  maxAlerts: number
  smallPortfolioMaxHoldings: number
  minHoldingsForConcentrationBreach: number
  concentration: Partial<PortfolioAlertRuleConfig['concentration']>
  risk: Partial<PortfolioAlertRuleConfig['risk']>
  coverage: Partial<PortfolioAlertRuleConfig['coverage']>
  contributors: Partial<PortfolioAlertRuleConfig['contributors']>
}>

interface PortfolioAlertRuleContext {
  sources: PortfolioAlertSources
  config: PortfolioAlertRuleConfig
  holdingsCount: number | null
}

export interface PortfolioAlertRuleDefinition {
  id: string
  description: string
  derive(context: PortfolioAlertRuleContext): PortfolioAlert[]
}

// Central frontend alert thresholds. Values are ratios unless noted otherwise.
// - Concentration is suppressed below minHoldingsForConcentrationBreach.
// - Daily risk thresholds are fallback limits when annualized values are absent.
// - Coverage gaps count missing classifications, fallback prices and marketdata warnings.
// - Contribution percent points are absolute percentage points, not ratios.
export const DEFAULT_PORTFOLIO_ALERT_RULES: PortfolioAlertRuleConfig = {
  maxAlerts: 5,
  smallPortfolioMaxHoldings: 3,
  minHoldingsForConcentrationBreach: 4,
  concentration: {
    topPosition: { warning: 0.35, critical: 0.5 },
    top3: { warning: 0.65, critical: 0.8 }
  },
  risk: {
    annualizedVolatility: { warning: 0.2, critical: 0.3 },
    dailyVolatility: { warning: 0.015, critical: 0.025 },
    annualizedTrackingError: { warning: 0.08, critical: 0.12 },
    dailyTrackingError: { warning: 0.006, critical: 0.012 },
    maxDrawdown: { warning: -0.15, critical: -0.25 }
  },
  coverage: {
    missingPricesCriticalFrom: 1,
    qualityGapWarningFrom: 1
  },
  contributors: {
    contributionReturnCriticalBelow: -0.1,
    contributionPercentPointsCriticalBelow: -10
  }
}

export const severityLabels: Record<PortfolioAlertSeverity, string> = {
  kritisch: 'Kritisch',
  warnung: 'Warnung',
  info: 'Info'
}

export const sourceLabels: Record<PortfolioAlertSourceKey, string> = {
  risk: 'Risk',
  coverage: 'Coverage',
  concentration: 'Konzentration',
  contributors: 'Contributors',
  summary: 'Summary'
}

export const sourceOrder: PortfolioAlertSourceKey[] = ['risk', 'coverage', 'concentration', 'contributors', 'summary']

const severityOrder: Record<PortfolioAlertSeverity, number> = {
  kritisch: 0,
  warnung: 1,
  info: 2
}

function hasNumber(value: number | null | undefined): value is number {
  return value != null && Number.isFinite(value)
}

function firstNumber(...values: Array<number | null | undefined>): number | null {
  return values.find((value): value is number => hasNumber(value)) ?? null
}

function severityFromUpperLimit(
  value: number | null,
  limits: ThresholdBand
): Exclude<PortfolioAlertSeverity, 'info'> | null {
  if (!hasNumber(value)) return null
  if (value >= limits.critical) return 'kritisch'
  if (value >= limits.warning) return 'warnung'
  return null
}

function severityFromLowerLimit(
  value: number | null,
  limits: ThresholdBand
): Exclude<PortfolioAlertSeverity, 'info'> | null {
  if (!hasNumber(value)) return null
  if (value <= limits.critical) return 'kritisch'
  if (value <= limits.warning) return 'warnung'
  return null
}

function positiveCount(...values: Array<number | null | undefined>): number {
  return values.reduce<number>((sum, value) => sum + (hasNumber(value) && value > 0 ? value : 0), 0)
}

function pluralizeHolding(count: number): string {
  return count === 1 ? 'Holding' : 'Holdings'
}

function concentrationDetail(label: string, value: number, holdingsCount: number | null): string {
  const holdingsSuffix = holdingsCount == null ? '' : ` bei ${holdingsCount} ${pluralizeHolding(holdingsCount)}`
  return `${label} liegt bei ${formatPercent(value)}${holdingsSuffix}.`
}

function alert(
  sourceKey: PortfolioAlertSourceKey,
  values: Omit<PortfolioAlert, 'sourceKey' | 'sourceLabel' | 'source'>
): PortfolioAlert {
  return {
    ...values,
    sourceKey,
    sourceLabel: sourceLabels[sourceKey],
    source: sourceLabels[sourceKey]
  }
}

function isSmallPortfolio(context: PortfolioAlertRuleContext): boolean {
  return (
    context.holdingsCount != null &&
    context.holdingsCount > 0 &&
    context.holdingsCount <= context.config.smallPortfolioMaxHoldings
  )
}

function hasBenchmark(risk: PortfolioRiskReadModel): boolean {
  return Boolean(risk.benchmark_symbol?.trim())
}

function hasBenchmarkMissingWarning(risk: PortfolioRiskReadModel): boolean {
  const warnings = risk.meta?.warnings
  if (!Array.isArray(warnings)) return false

  return warnings.some((warning) => {
    if (typeof warning === 'string') return warning === 'benchmark_data_missing'
    if (warning && typeof warning === 'object' && 'code' in warning) {
      return warning.code === 'benchmark_data_missing'
    }
    return false
  })
}

function mergeConfig(config: PartialPortfolioAlertRuleConfig | undefined): PortfolioAlertRuleConfig {
  return {
    ...DEFAULT_PORTFOLIO_ALERT_RULES,
    ...config,
    concentration: {
      ...DEFAULT_PORTFOLIO_ALERT_RULES.concentration,
      ...config?.concentration
    },
    risk: {
      ...DEFAULT_PORTFOLIO_ALERT_RULES.risk,
      ...config?.risk
    },
    coverage: {
      ...DEFAULT_PORTFOLIO_ALERT_RULES.coverage,
      ...config?.coverage
    },
    contributors: {
      ...DEFAULT_PORTFOLIO_ALERT_RULES.contributors,
      ...config?.contributors
    }
  }
}

function deriveConcentrationAlerts(context: PortfolioAlertRuleContext): PortfolioAlert[] {
  if (
    context.holdingsCount != null &&
    context.holdingsCount < context.config.minHoldingsForConcentrationBreach
  ) {
    return []
  }

  const alerts: PortfolioAlert[] = []
  const topPositionWeight = firstNumber(
    context.sources.summary?.top_position_weight,
    context.sources.risk?.top_position_weight
  )
  const topPositionSeverity = severityFromUpperLimit(topPositionWeight, context.config.concentration.topPosition)
  if (topPositionSeverity && topPositionWeight != null) {
    alerts.push(
      alert('concentration', {
        id: 'top-position-concentration',
        severity: topPositionSeverity,
        priority: 10,
        title: topPositionSeverity === 'kritisch' ? 'Top-Position kritisch' : 'Top-Position erhoeht',
        detail: concentrationDetail('Die groesste Position', topPositionWeight, context.holdingsCount),
        actionHint: 'Konzentration pruefen'
      })
    )
  }

  const top3Weight = firstNumber(context.sources.summary?.top3_weight, context.sources.risk?.top3_weight)
  const top3Severity = severityFromUpperLimit(top3Weight, context.config.concentration.top3)
  if (top3Severity && top3Weight != null) {
    alerts.push(
      alert('concentration', {
        id: 'top3-concentration',
        severity: top3Severity,
        priority: 20,
        title: top3Severity === 'kritisch' ? 'Top-3-Konzentration kritisch' : 'Top-3-Konzentration erhoeht',
        detail: concentrationDetail('Die Top 3', top3Weight, context.holdingsCount),
        actionHint: 'Konzentration pruefen'
      })
    )
  }

  return alerts
}

function deriveCoverageAlerts(context: PortfolioAlertRuleContext): PortfolioAlert[] {
  const coverage = context.sources.coverage
  if (!coverage) return []

  const alerts: PortfolioAlert[] = []
  const missingPrices = coverage.missing_prices ?? 0
  if (missingPrices >= context.config.coverage.missingPricesCriticalFrom) {
    alerts.push(
      alert('coverage', {
        id: 'missing-prices',
        severity: 'kritisch',
        priority: 30,
        title: 'Fehlende Preise',
        detail: `${missingPrices} ${pluralizeHolding(missingPrices)} ohne aktuellen Preis.`,
        actionHint: 'Datenquelle pruefen'
      })
    )
  }

  const classificationGaps = positiveCount(
    coverage.missing_sectors,
    coverage.missing_countries,
    coverage.missing_currencies,
    coverage.fallback_acquisition_prices,
    coverage.holdings_with_marketdata_warnings
  )
  const warningCount = coverage.warnings?.length ?? 0
  const qualitySignals = classificationGaps + warningCount

  if (qualitySignals >= context.config.coverage.qualityGapWarningFrom) {
    const parts: string[] = []
    if (classificationGaps > 0) parts.push(`${classificationGaps} Datenluecken`)
    if (warningCount > 0) parts.push(`${warningCount} Hinweise`)

    alerts.push(
      alert('coverage', {
        id: 'coverage-quality-warnings',
        severity: 'warnung',
        priority: 40,
        title: 'Datenqualitaet pruefen',
        detail: parts.join(', '),
        actionHint: 'Datenquelle pruefen'
      })
    )
  }

  return alerts
}

function deriveRiskAlerts(context: PortfolioAlertRuleContext): PortfolioAlert[] {
  const risk = context.sources.risk
  if (!risk) return []

  const alerts: PortfolioAlert[] = []
  const annualizedVolatility = firstNumber(risk.annualized_volatility)
  const dailyVolatility = annualizedVolatility == null ? firstNumber(risk.portfolio_volatility) : null
  const volatilityValue = annualizedVolatility ?? dailyVolatility
  const volatilityLimits =
    annualizedVolatility == null ? context.config.risk.dailyVolatility : context.config.risk.annualizedVolatility
  const volatilitySeverity = severityFromUpperLimit(volatilityValue, volatilityLimits)
  if (volatilitySeverity && volatilityValue != null) {
    alerts.push(
      alert('risk', {
        id: 'high-volatility',
        severity: volatilitySeverity,
        priority: 50,
        title: volatilitySeverity === 'kritisch' ? 'Hohe Volatilitaet kritisch' : 'Hohe Volatilitaet',
        detail: `${annualizedVolatility == null ? 'Tagesvolatilitaet' : 'Ann. Volatilitaet'} ${formatPercent(volatilityValue)}.`,
        actionHint: 'Risikobudget pruefen'
      })
    )
  }

  const benchmarkMissing = !hasBenchmark(risk) || hasBenchmarkMissingWarning(risk)
  if (benchmarkMissing) {
    alerts.push(
      alert('risk', {
        id: 'benchmark-missing',
        severity: 'info',
        priority: 55,
        title: 'Benchmark fehlt',
        detail: 'Tracking Error und relative Kennzahlen sind nur eingeschraenkt bewertbar.',
        actionHint: 'Benchmark setzen'
      })
    )
  } else {
    const annualizedTrackingError = firstNumber(risk.annualized_tracking_error)
    const dailyTrackingError = annualizedTrackingError == null ? firstNumber(risk.tracking_error) : null
    const trackingErrorValue = annualizedTrackingError ?? dailyTrackingError
    const trackingErrorLimits =
      annualizedTrackingError == null
        ? context.config.risk.dailyTrackingError
        : context.config.risk.annualizedTrackingError
    const trackingErrorSeverity = severityFromUpperLimit(trackingErrorValue, trackingErrorLimits)
    if (trackingErrorSeverity && trackingErrorValue != null) {
      alerts.push(
        alert('risk', {
          id: 'high-tracking-error',
          severity: trackingErrorSeverity,
          priority: 60,
          title: trackingErrorSeverity === 'kritisch' ? 'Tracking Error kritisch' : 'Tracking Error erhoeht',
          detail: `${annualizedTrackingError == null ? 'Tracking Error' : 'Ann. Tracking Error'} ${formatPercent(trackingErrorValue)}.`,
          actionHint: 'Benchmark-Abweichung pruefen'
        })
      )
    }
  }

  const maxDrawdown = firstNumber(risk.max_drawdown)
  const drawdownSeverity = severityFromLowerLimit(maxDrawdown, context.config.risk.maxDrawdown)
  if (drawdownSeverity && maxDrawdown != null) {
    alerts.push(
      alert('risk', {
        id: 'max-drawdown',
        severity: drawdownSeverity,
        priority: 70,
        title: drawdownSeverity === 'kritisch' ? 'Max Drawdown stark' : 'Max Drawdown erhoeht',
        detail: `Max Drawdown ${formatSignedPercentFromRatio(maxDrawdown)}.`,
        actionHint: 'Risikobudget pruefen'
      })
    )
  }

  return alerts
}

function deriveContributorAlerts(context: PortfolioAlertRuleContext): PortfolioAlert[] {
  const contributors = context.sources.contributors
  if (!contributors) return []

  const alerts: PortfolioAlert[] = []
  const contributionPercentPoints = firstNumber(contributors.total_contribution_pct_points)
  const contributionReturn = contributionPercentPoints == null ? firstNumber(contributors.total_contribution_return) : null

  if (contributionPercentPoints != null && contributionPercentPoints < 0) {
    alerts.push(
      alert('contributors', {
        id: 'negative-range-return',
        severity:
          contributionPercentPoints <= context.config.contributors.contributionPercentPointsCriticalBelow
            ? 'kritisch'
            : 'warnung',
        priority: 80,
        title: 'Zeitraumrendite negativ',
        detail: `Gesamtbeitrag ${formatSignedPercentPoints(contributionPercentPoints)}.`,
        actionHint: 'Renditetreiber pruefen'
      })
    )
  } else if (contributionReturn != null && contributionReturn < 0) {
    alerts.push(
      alert('contributors', {
        id: 'negative-range-return',
        severity:
          contributionReturn <= context.config.contributors.contributionReturnCriticalBelow ? 'kritisch' : 'warnung',
        priority: 80,
        title: 'Zeitraumrendite negativ',
        detail: `Gesamtbeitrag ${formatSignedPercentFromRatio(contributionReturn)}.`,
        actionHint: 'Renditetreiber pruefen'
      })
    )
  }

  const warningCount = contributors.warnings?.length ?? 0
  if (warningCount > 0) {
    alerts.push(
      alert('contributors', {
        id: 'contributor-quality-warnings',
        severity: 'warnung',
        priority: 90,
        title: 'Contributor-Hinweise vorhanden',
        detail: `${warningCount} Hinweise zur Beitragsrechnung.`,
        actionHint: 'Renditetreiber pruefen'
      })
    )
  }

  return alerts
}

function deriveSmallPortfolioAlerts(context: PortfolioAlertRuleContext): PortfolioAlert[] {
  if (!isSmallPortfolio(context)) return []

  const holdingsCount = context.holdingsCount
  if (holdingsCount == null) return []

  return [
    alert('concentration', {
      id: 'small-portfolio',
      severity: 'info',
      priority: 100,
      title: 'Kleines Portfolio',
      detail: `${holdingsCount} ${pluralizeHolding(holdingsCount)}; Konzentration nur eingeschraenkt bewertbar.`,
      actionHint: 'Konzentration pruefen'
    })
  ]
}

export const PORTFOLIO_ALERT_RULE_DEFINITIONS: PortfolioAlertRuleDefinition[] = [
  {
    id: 'concentration',
    description: 'Evaluates top-position and top-3 concentration for sufficiently diversified portfolios.',
    derive: deriveConcentrationAlerts
  },
  {
    id: 'coverage',
    description: 'Surfaces missing prices and classification/data-quality gaps.',
    derive: deriveCoverageAlerts
  },
  {
    id: 'risk',
    description: 'Evaluates volatility, benchmark availability, tracking error and max drawdown.',
    derive: deriveRiskAlerts
  },
  {
    id: 'contributors',
    description: 'Surfaces negative range contribution and contributor calculation warnings.',
    derive: deriveContributorAlerts
  },
  {
    id: 'small-portfolio',
    description: 'Adds an information alert for portfolios where concentration breaches would be misleading.',
    derive: deriveSmallPortfolioAlerts
  }
]

export function buildPortfolioAlerts(
  sources: PortfolioAlertSources,
  options: number | BuildPortfolioAlertsOptions = {}
): PortfolioAlert[] {
  const normalizedOptions = typeof options === 'number' ? { maxAlerts: options } : options
  const config = mergeConfig(normalizedOptions.config)
  const maxAlerts = normalizedOptions.maxAlerts ?? config.maxAlerts
  const context: PortfolioAlertRuleContext = {
    sources,
    config,
    holdingsCount: firstNumber(sources.summary?.holdings_count, sources.coverage?.total_holdings)
  }

  return PORTFOLIO_ALERT_RULE_DEFINITIONS.flatMap((rule) => rule.derive(context))
    .sort((left, right) => severityOrder[left.severity] - severityOrder[right.severity] || left.priority - right.priority)
    .slice(0, Math.max(0, maxAlerts))
}
