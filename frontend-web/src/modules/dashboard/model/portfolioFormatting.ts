export function formatMoney(value: number | null | undefined, currency = 'EUR'): string {
  if (value == null || Number.isNaN(value)) {
    return 'n/a'
  }

  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2
  }).format(value)
}

export function formatPercent(value: number | null | undefined, fractionDigits = 2): string {
  if (value == null || Number.isNaN(value)) {
    return 'n/a'
  }

  return new Intl.NumberFormat('de-DE', {
    style: 'percent',
    maximumFractionDigits: fractionDigits,
    minimumFractionDigits: fractionDigits
  }).format(value)
}

export function formatPercentPoints(value: number | null | undefined, fractionDigits = 2): string {
  if (value == null || Number.isNaN(value)) {
    return 'n/a'
  }

  return `${new Intl.NumberFormat('de-DE', {
    maximumFractionDigits: fractionDigits,
    minimumFractionDigits: fractionDigits
  }).format(value)} %`
}

export function formatNumber(value: number | null | undefined, fractionDigits = 2): string {
  if (value == null || Number.isNaN(value)) {
    return 'n/a'
  }

  return new Intl.NumberFormat('de-DE', {
    maximumFractionDigits: fractionDigits,
    minimumFractionDigits: fractionDigits
  }).format(value)
}

export function formatSignedMoney(value: number | null | undefined, currency = 'EUR'): string {
  if (value == null || Number.isNaN(value)) {
    return 'n/a'
  }
  const formatted = formatMoney(Math.abs(value), currency)
  if (value > 0) return `+${formatted}`
  if (value < 0) return `-${formatted}`
  return formatted
}

export function mapHoldingDataStatus(status: string | null | undefined): string {
  if (!status) return 'Unbekannt'
  if (status === 'ok') return 'OK'
  if (status === 'fallback_acquisition_price') return 'Preis-Fallback'
  if (status === 'missing_symbol') return 'Symbol fehlt'
  return status.replaceAll('_', ' ')
}

export function mapConcentrationNote(note: string | null | undefined): string {
  if (!note) return 'n/a'
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
