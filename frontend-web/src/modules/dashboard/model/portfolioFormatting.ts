const NA_TEXT = 'n/a'

function isMissingNumber(value: number | null | undefined): boolean {
  return value == null || Number.isNaN(value)
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

export function formatMoney(value: number | null | undefined, currency = 'EUR'): string {
  if (isMissingNumber(value)) {
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
  if (isMissingNumber(value)) {
    return NA_TEXT
  }

  const absValue = Math.abs(value)
  const formatted = formatMoney(absValue, currency)

  if (value > 0) return `+${formatted}`
  if (value < 0) return `-${formatted}`
  return formatted
}

export function formatPercentFromRatio(value: number | null | undefined, fractionDigits = 2): string {
  if (isMissingNumber(value)) {
    return NA_TEXT
  }

  return new Intl.NumberFormat('de-DE', {
    style: 'percent',
    maximumFractionDigits: fractionDigits,
    minimumFractionDigits: fractionDigits
  }).format(value)
}

export function formatPercentValue(value: number | null | undefined, fractionDigits = 2): string {
  if (isMissingNumber(value)) {
    return NA_TEXT
  }

  return `${formatDecimal(value, fractionDigits)} %`
}

export function formatSignedPercentValue(value: number | null | undefined, fractionDigits = 2): string {
  if (isMissingNumber(value)) {
    return NA_TEXT
  }

  const formatted = formatPercentValue(Math.abs(value), fractionDigits)
  if (value > 0) return `+${formatted}`
  if (value < 0) return `-${formatted}`
  return formatted
}

export function formatPercentPoints(value: number | null | undefined, fractionDigits = 2): string {
  if (isMissingNumber(value)) {
    return NA_TEXT
  }

  return `${formatDecimal(value, fractionDigits)} pp`
}

export function formatSignedPercentPoints(value: number | null | undefined, fractionDigits = 2): string {
  if (isMissingNumber(value)) {
    return NA_TEXT
  }

  const formatted = formatPercentPoints(Math.abs(value), fractionDigits)
  if (value > 0) return `+${formatted}`
  if (value < 0) return `-${formatted}`
  return formatted
}

export function formatNumber(value: number | null | undefined, fractionDigits = 2): string {
  if (isMissingNumber(value)) {
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
  return status.replaceAll('_', ' ')
}

export function mapConcentrationNote(note: string | null | undefined): string {
  if (!note) return NA_TEXT
  if (note === 'very_high_top3_concentration') return 'Top-3 sehr konzentriert'
  if (note === 'high_top3_concentration') return 'Top-3 hoch konzentriert'
  if (note === 'single_position_dominates') return 'Einzeltitel dominiert'
  return note.replaceAll('_', ' ')
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
  return mappedWarnings[warning] ?? warning.replaceAll('_', ' ')
}
