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

export interface PortfolioAlert {
  id: string
  severity: PortfolioAlertSeverity
  priority: number
  title: string
  detail: string
  source: string
}

export interface PortfolioAlertSources {
  summary?: PortfolioSummaryReadModel | null
  risk?: PortfolioRiskReadModel | null
  coverage?: PortfolioDataCoverageReadModel | null
  contributors?: PortfolioContributorsReadModel | null
}

const MAX_ALERTS = 5

// Alert thresholds are intentionally simple and visible:
// - concentration uses the same business thresholds as PortfolioSummaryBar
// - risk limits are heuristic dashboard breaches, not a backend risk engine
// - coverage/contributor warnings are surfaced when existing counters report gaps
// - portfolios below four holdings get an info note instead of concentration breaches
const ALERT_RULES = {
  minHoldingsForConcentrationBreach: 4,
  topPosition: { warning: 0.35, critical: 0.5 },
  top3: { warning: 0.65, critical: 0.8 },
  annualizedVolatility: { warning: 0.2, critical: 0.3 },
  dailyVolatility: { warning: 0.015, critical: 0.025 },
  annualizedTrackingError: { warning: 0.08, critical: 0.12 },
  dailyTrackingError: { warning: 0.006, critical: 0.012 },
  maxDrawdown: { warning: -0.15, critical: -0.25 },
  contributionReturn: { critical: -0.1 },
  contributionPercentPoints: { critical: -10 }
} as const

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
  limits: { warning: number; critical: number }
): Exclude<PortfolioAlertSeverity, 'info'> | null {
  if (!hasNumber(value)) return null
  if (value >= limits.critical) return 'kritisch'
  if (value >= limits.warning) return 'warnung'
  return null
}

function severityFromLowerLimit(
  value: number | null,
  limits: { warning: number; critical: number }
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

function addConcentrationAlerts(alerts: PortfolioAlert[], sources: PortfolioAlertSources, holdingsCount: number | null) {
  if (holdingsCount != null && holdingsCount < ALERT_RULES.minHoldingsForConcentrationBreach) {
    return
  }

  const topPositionWeight = firstNumber(sources.summary?.top_position_weight, sources.risk?.top_position_weight)
  const topPositionSeverity = severityFromUpperLimit(topPositionWeight, ALERT_RULES.topPosition)
  if (topPositionSeverity && topPositionWeight != null) {
    alerts.push({
      id: 'top-position-concentration',
      severity: topPositionSeverity,
      priority: 10,
      title: topPositionSeverity === 'kritisch' ? 'Top-Position kritisch' : 'Top-Position erhoeht',
      detail: concentrationDetail('Die groesste Position', topPositionWeight, holdingsCount),
      source: 'Summary/Risk'
    })
  }

  const top3Weight = firstNumber(sources.summary?.top3_weight, sources.risk?.top3_weight)
  const top3Severity = severityFromUpperLimit(top3Weight, ALERT_RULES.top3)
  if (top3Severity && top3Weight != null) {
    alerts.push({
      id: 'top3-concentration',
      severity: top3Severity,
      priority: 20,
      title: top3Severity === 'kritisch' ? 'Top-3-Konzentration kritisch' : 'Top-3-Konzentration erhoeht',
      detail: concentrationDetail('Die Top 3', top3Weight, holdingsCount),
      source: 'Summary/Risk'
    })
  }
}

function addCoverageAlerts(alerts: PortfolioAlert[], coverage: PortfolioDataCoverageReadModel | null | undefined) {
  if (!coverage) return

  const missingPrices = coverage.missing_prices ?? 0
  if (missingPrices > 0) {
    alerts.push({
      id: 'missing-prices',
      severity: 'kritisch',
      priority: 30,
      title: 'Fehlende Preise',
      detail: `${missingPrices} ${pluralizeHolding(missingPrices)} ohne aktuellen Preis.`,
      source: 'Coverage'
    })
  }

  const classificationGaps = positiveCount(
    coverage.missing_sectors,
    coverage.missing_countries,
    coverage.missing_currencies,
    coverage.fallback_acquisition_prices,
    coverage.holdings_with_marketdata_warnings
  )
  const warningCount = coverage.warnings?.length ?? 0

  if (classificationGaps > 0 || warningCount > 0) {
    const parts: string[] = []
    if (classificationGaps > 0) parts.push(`${classificationGaps} Datenluecken`)
    if (warningCount > 0) parts.push(`${warningCount} Hinweise`)

    alerts.push({
      id: 'coverage-quality-warnings',
      severity: 'warnung',
      priority: 40,
      title: 'Datenqualitaet pruefen',
      detail: parts.join(', '),
      source: 'Coverage'
    })
  }
}

function addRiskAlerts(alerts: PortfolioAlert[], risk: PortfolioRiskReadModel | null | undefined) {
  if (!risk) return

  const annualizedVolatility = firstNumber(risk.annualized_volatility)
  const dailyVolatility = annualizedVolatility == null ? firstNumber(risk.portfolio_volatility) : null
  const volatilityValue = annualizedVolatility ?? dailyVolatility
  const volatilityLimits = annualizedVolatility == null ? ALERT_RULES.dailyVolatility : ALERT_RULES.annualizedVolatility
  const volatilitySeverity = severityFromUpperLimit(volatilityValue, volatilityLimits)
  if (volatilitySeverity && volatilityValue != null) {
    alerts.push({
      id: 'high-volatility',
      severity: volatilitySeverity,
      priority: 50,
      title: volatilitySeverity === 'kritisch' ? 'Hohe Volatilitaet kritisch' : 'Hohe Volatilitaet',
      detail: `${annualizedVolatility == null ? 'Tagesvolatilitaet' : 'Ann. Volatilitaet'} ${formatPercent(volatilityValue)}.`,
      source: 'Risk'
    })
  }

  const annualizedTrackingError = firstNumber(risk.annualized_tracking_error)
  const dailyTrackingError = annualizedTrackingError == null ? firstNumber(risk.tracking_error) : null
  const trackingErrorValue = annualizedTrackingError ?? dailyTrackingError
  const trackingErrorLimits =
    annualizedTrackingError == null ? ALERT_RULES.dailyTrackingError : ALERT_RULES.annualizedTrackingError
  const trackingErrorSeverity = severityFromUpperLimit(trackingErrorValue, trackingErrorLimits)
  if (trackingErrorSeverity && trackingErrorValue != null) {
    alerts.push({
      id: 'high-tracking-error',
      severity: trackingErrorSeverity,
      priority: 60,
      title: trackingErrorSeverity === 'kritisch' ? 'Tracking Error kritisch' : 'Tracking Error erhoeht',
      detail: `${annualizedTrackingError == null ? 'Tracking Error' : 'Ann. Tracking Error'} ${formatPercent(trackingErrorValue)}.`,
      source: 'Risk'
    })
  }

  const maxDrawdown = firstNumber(risk.max_drawdown)
  const drawdownSeverity = severityFromLowerLimit(maxDrawdown, ALERT_RULES.maxDrawdown)
  if (drawdownSeverity && maxDrawdown != null) {
    alerts.push({
      id: 'max-drawdown',
      severity: drawdownSeverity,
      priority: 70,
      title: drawdownSeverity === 'kritisch' ? 'Max Drawdown stark' : 'Max Drawdown erhoeht',
      detail: `Max Drawdown ${formatSignedPercentFromRatio(maxDrawdown)}.`,
      source: 'Risk'
    })
  }
}

function addContributorAlerts(alerts: PortfolioAlert[], contributors: PortfolioContributorsReadModel | null | undefined) {
  if (!contributors) return

  const contributionPercentPoints = firstNumber(contributors.total_contribution_pct_points)
  const contributionReturn = contributionPercentPoints == null ? firstNumber(contributors.total_contribution_return) : null

  if (contributionPercentPoints != null && contributionPercentPoints < 0) {
    alerts.push({
      id: 'negative-range-return',
      severity: contributionPercentPoints <= ALERT_RULES.contributionPercentPoints.critical ? 'kritisch' : 'warnung',
      priority: 80,
      title: 'Zeitraumrendite negativ',
      detail: `Gesamtbeitrag ${formatSignedPercentPoints(contributionPercentPoints)}.`,
      source: 'Contributors'
    })
  } else if (contributionReturn != null && contributionReturn < 0) {
    alerts.push({
      id: 'negative-range-return',
      severity: contributionReturn <= ALERT_RULES.contributionReturn.critical ? 'kritisch' : 'warnung',
      priority: 80,
      title: 'Zeitraumrendite negativ',
      detail: `Gesamtbeitrag ${formatSignedPercentFromRatio(contributionReturn)}.`,
      source: 'Contributors'
    })
  }

  const warningCount = contributors.warnings?.length ?? 0
  if (warningCount > 0) {
    alerts.push({
      id: 'contributor-quality-warnings',
      severity: 'warnung',
      priority: 90,
      title: 'Contributor-Hinweise vorhanden',
      detail: `${warningCount} Hinweise zur Beitragsrechnung.`,
      source: 'Contributors'
    })
  }
}

function addSmallPortfolioInfo(alerts: PortfolioAlert[], holdingsCount: number | null) {
  if (holdingsCount == null || holdingsCount <= 0 || holdingsCount >= ALERT_RULES.minHoldingsForConcentrationBreach) {
    return
  }

  alerts.push({
    id: 'small-portfolio',
    severity: 'info',
    priority: 100,
    title: 'Kleines Portfolio',
    detail: `${holdingsCount} ${pluralizeHolding(holdingsCount)}; Konzentration nur eingeschraenkt bewertbar.`,
    source: 'Summary/Coverage'
  })
}

export function buildPortfolioAlerts(sources: PortfolioAlertSources, maxAlerts = MAX_ALERTS): PortfolioAlert[] {
  const alerts: PortfolioAlert[] = []
  const holdingsCount = firstNumber(sources.summary?.holdings_count, sources.coverage?.total_holdings)

  addConcentrationAlerts(alerts, sources, holdingsCount)
  addCoverageAlerts(alerts, sources.coverage)
  addRiskAlerts(alerts, sources.risk)
  addContributorAlerts(alerts, sources.contributors)
  addSmallPortfolioInfo(alerts, holdingsCount)

  return alerts
    .sort((left, right) => severityOrder[left.severity] - severityOrder[right.severity] || left.priority - right.priority)
    .slice(0, Math.max(0, maxAlerts))
}
