export const NA_TEXT = 'n/a'

function hasNumber(value: number | null | undefined): value is number {
  return value != null && !Number.isNaN(value)
}

function formatDecimal(value: number, fractionDigits = 2): string {
  return new Intl.NumberFormat('de-DE', {
    maximumFractionDigits: fractionDigits,
    minimumFractionDigits: fractionDigits
  }).format(value)
}

export function formatNullableText(value: string | null | undefined, fallback = NA_TEXT): string {
  if (value == null) {
    return fallback
  }

  const normalized = value.trim()
  return normalized.length > 0 ? normalized : fallback
}

export function getStringMeta(meta: Record<string, unknown> | null | undefined, ...keys: string[]): string | null {
  for (const key of keys) {
    const value = meta?.[key]
    if (typeof value === 'string' && value.trim().length > 0) {
      return value.trim()
    }
  }

  return null
}

export function formatDate(value: string | null | undefined): string {
  const normalized = formatNullableText(value)
  if (normalized === NA_TEXT) {
    return NA_TEXT
  }

  const dateOnlyMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(normalized)
  if (dateOnlyMatch) {
    return `${dateOnlyMatch[3]}.${dateOnlyMatch[2]}.${dateOnlyMatch[1]}`
  }

  const parsed = new Date(normalized)
  if (!Number.isNaN(parsed.getTime())) {
    return new Intl.DateTimeFormat('de-DE').format(parsed)
  }

  return normalized
}

export function formatRangeLabel(range: string | null | undefined, rangeLabel?: string | null): string {
  const explicitLabel = formatNullableText(rangeLabel, '')
  if (explicitLabel) {
    return explicitLabel
  }

  const normalizedRange = formatNullableText(range)
  const mappedRanges: Record<string, string> = {
    '1m': '1 Monat',
    '3m': '3 Monate',
    '6m': '6 Monate',
    ytd: 'Jahr bis heute',
    '1y': '1 Jahr',
    max: 'Gesamtzeitraum'
  }

  return mappedRanges[normalizedRange] ?? normalizedRange
}

export function mapPortfolioMethodology(methodology: string | null | undefined): string {
  const normalized = formatNullableText(methodology)
  if (normalized === NA_TEXT) {
    return NA_TEXT
  }

  const mappedMethodologies: Record<string, string> = {
    daily_returns_on_range: 'Tägliche Renditen im Zeitraum',
    range_start_value: 'gegen Startwert',
    range_contribution: 'Beitrag zur Zeitraumrendite',
    since_cost_basis: 'gegen Einstandswert',
    relative_to_benchmark: 'relativ zur Benchmark'
  }

  return mappedMethodologies[normalized] ?? normalized.replace(/_/g, ' ')
}

export function formatMoney(value: number | null | undefined, currency = 'EUR'): string {
  if (!hasNumber(value)) {
    return NA_TEXT
  }

  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
    minimumFractionDigits: 2
  }).format(value)
}

export function formatSignedMoney(value: number | null | undefined, currency = 'EUR'): string {
  if (!hasNumber(value)) {
    return NA_TEXT
  }

  const absValue = Math.abs(value)
  const formatted = formatMoney(absValue, currency)

  if (value > 0) return `+${formatted}`
  if (value < 0) return `-${formatted}`
  return formatted
}

export function formatPercentFromRatio(value: number | null | undefined, fractionDigits = 2): string {
  if (!hasNumber(value)) {
    return NA_TEXT
  }

  return new Intl.NumberFormat('de-DE', {
    style: 'percent',
    maximumFractionDigits: fractionDigits,
    minimumFractionDigits: fractionDigits
  }).format(value)
}

export function formatPercentValue(value: number | null | undefined, fractionDigits = 2): string {
  if (!hasNumber(value)) {
    return NA_TEXT
  }

  return `${formatDecimal(value, fractionDigits)} %`
}

export function formatSignedPercentValue(value: number | null | undefined, fractionDigits = 2): string {
  if (!hasNumber(value)) {
    return NA_TEXT
  }

  const formatted = formatPercentValue(Math.abs(value), fractionDigits)
  if (value > 0) return `+${formatted}`
  if (value < 0) return `-${formatted}`
  return formatted
}

export function formatPercentPoints(value: number | null | undefined, fractionDigits = 2): string {
  if (!hasNumber(value)) {
    return NA_TEXT
  }

  return `${formatDecimal(value, fractionDigits)} pp`
}

export function formatSignedPercentPoints(value: number | null | undefined, fractionDigits = 2): string {
  if (!hasNumber(value)) {
    return NA_TEXT
  }

  const formatted = formatPercentPoints(Math.abs(value), fractionDigits)
  if (value > 0) return `+${formatted}`
  if (value < 0) return `-${formatted}`
  return formatted
}

export function formatNumber(value: number | null | undefined, fractionDigits = 2): string {
  if (!hasNumber(value)) {
    return NA_TEXT
  }

  return formatDecimal(value, fractionDigits)
}

// Legacy helper names kept as wrappers for compatibility.
export function formatPercent(value: number | null | undefined, fractionDigits = 2): string {
  return formatPercentFromRatio(value, fractionDigits)
}

export function mapHoldingDataStatus(status: string | null | undefined): string {
  if (!status) return 'Unbekannt'
  if (status === 'ok') return 'OK'
  if (status === 'fallback_acquisition_price') return 'Preis-Fallback'
  if (status === 'missing_symbol') return 'Symbol fehlt'
  return status.replace(/_/g, ' ')
}

export function mapConcentrationNote(note: string | null | undefined): string {
  if (!note) return NA_TEXT
  if (note === 'very_high_top3_concentration') return 'Top-3 sehr konzentriert'
  if (note === 'high_top3_concentration') return 'Top-3 hoch konzentriert'
  if (note === 'single_position_dominates') return 'Einzeltitel dominiert'
  return note.replace(/_/g, ' ')
}

export function mapCoverageWarning(warning: string): string {
  const mappedWarnings: Record<string, string> = {
    price_fallback_used_for_some_holdings: 'Preis-Fallback bei einzelnen Holdings',
    fallback_acquisition_price_used: 'Fallback auf Einstandspreise aktiv',
    holdings_with_marketdata_warnings: 'Einzelne Titel mit Marketdata-Warnungen',
    missing_sector_data: 'Sektordaten unvollständig',
    missing_country_data: 'Länderdaten unvollständig',
    missing_currency_data: 'Währungsdaten unvollständig'
  }
  return mappedWarnings[warning] ?? warning.replace(/_/g, ' ')
}

export function mapPortfolioWarning(warning: string | null | undefined): string {
  const normalized = formatNullableText(warning)
  if (normalized === NA_TEXT) {
    return NA_TEXT
  }

  const mappedWarnings: Record<string, string> = {
    missing_current_price: 'Aktueller Preis fehlt',
    missing_price: 'Preis fehlt',
    missing_symbol: 'Symbol fehlt',
    missing_sector_data: 'Sektordaten unvollständig',
    missing_country_data: 'Länderdaten unvollständig',
    missing_currency_data: 'Währungsdaten unvollständig',
    fallback_acquisition_price_used: 'Fallback auf Einstandspreis aktiv',
    price_fallback_used_for_some_holdings: 'Preis-Fallback bei einzelnen Holdings',
    insufficient_history: 'Historie unvollständig',
    benchmark_data_missing: 'Benchmark-Daten fehlen'
  }

  return mappedWarnings[normalized] ?? normalized.replace(/_/g, ' ')
}
