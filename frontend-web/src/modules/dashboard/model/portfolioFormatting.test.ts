import { describe, expect, it } from 'vitest'

import {
  formatDate,
  formatMoney,
  formatNullableText,
  formatPercent,
  formatPercentFromRatio,
  formatPercentPoints,
  formatPercentValue,
  formatRangeLabel,
  formatSignedPercentFromRatio,
  formatSignedMoney,
  formatSignedPercentPoints,
  formatSignedPercentValue,
  mapPortfolioMethodology,
  mapPortfolioWarning
} from '@/modules/dashboard/model/portfolioFormatting'

describe('portfolioFormatting', () => {
  it('formats ratio values as percent (legacy wrapper + explicit helper)', () => {
    expect(formatPercentFromRatio(0.128)).toBe('12,80 %')
    expect(formatPercent(0.128)).toBe('12,80 %')
  })

  it('formats signed ratio values as percent', () => {
    expect(formatSignedPercentFromRatio(0.128)).toBe('+12,80\u00a0%')
    expect(formatSignedPercentFromRatio(-0.128)).toBe('-12,80\u00a0%')
    expect(formatSignedPercentFromRatio(0)).toBe('0,00\u00a0%')
  })

  it('formats raw percent values and percent points with dedicated units', () => {
    expect(formatPercentValue(1.92)).toBe('1,92 %')
    expect(formatPercentPoints(0.35)).toBe('0,35 pp')
  })

  it('formats signed percent values and signed percent points', () => {
    expect(formatSignedPercentValue(1.92)).toBe('+1,92 %')
    expect(formatSignedPercentValue(-1.92)).toBe('-1,92 %')
    expect(formatSignedPercentValue(0)).toBe('0,00 %')

    expect(formatSignedPercentPoints(0.35)).toBe('+0,35 pp')
    expect(formatSignedPercentPoints(-0.35)).toBe('-0,35 pp')
    expect(formatSignedPercentPoints(0)).toBe('0,00 pp')
  })

  it('formats EUR currency with consistent sign handling', () => {
    expect(formatMoney(257.61)).toBe('257,61 €')
    expect(formatSignedMoney(257.61)).toBe('+257,61 €')
    expect(formatSignedMoney(-257.61)).toBe('-257,61 €')
    expect(formatSignedMoney(0)).toBe('0,00 €')
  })

  it('returns n/a for nullish and NaN number values', () => {
    expect(formatMoney(null)).toBe('n/a')
    expect(formatMoney(undefined)).toBe('n/a')
    expect(formatMoney(Number.NaN)).toBe('n/a')

    expect(formatPercentFromRatio(null)).toBe('n/a')
    expect(formatPercentValue(undefined)).toBe('n/a')
    expect(formatPercentPoints(Number.NaN)).toBe('n/a')
  })

  it('normalizes nullable text values with the standard fallback', () => {
    expect(formatNullableText('Depot A')).toBe('Depot A')
    expect(formatNullableText('   ')).toBe('n/a')
    expect(formatNullableText(null)).toBe('n/a')
    expect(formatNullableText(undefined, '—')).toBe('—')
  })

  it('formats portfolio meta labels', () => {
    expect(formatDate('2026-04-10')).toBe('10.04.2026')
    expect(formatRangeLabel('3m')).toBe('3 Monate')
    expect(formatRangeLabel('3m', 'Letzte 3 Monate')).toBe('Letzte 3 Monate')
    expect(mapPortfolioMethodology('range_contribution')).toBe('Beitrag zur Zeitraumrendite')
    expect(mapPortfolioWarning('missing_current_price')).toBe('Aktueller Preis fehlt')
  })
})
