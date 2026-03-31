import { describe, expect, it } from 'vitest'

import { isValidAllowanceAmount, normalizeAllowanceInput } from '@/modules/allowances/model/allowanceAmount'

describe('normalizeAllowanceInput', () => {
  it('converts numeric values into trimmed strings', () => {
    expect(normalizeAllowanceInput(10)).toBe('10')
    expect(normalizeAllowanceInput(10.5)).toBe('10.5')
  })

  it('trims string values and handles nullish values', () => {
    expect(normalizeAllowanceInput(' 12.30 ')).toBe('12.30')
    expect(normalizeAllowanceInput(undefined)).toBe('')
    expect(normalizeAllowanceInput(null)).toBe('')
  })
})

describe('isValidAllowanceAmount', () => {
  it('accepts non-negative amounts with up to two decimals', () => {
    expect(isValidAllowanceAmount('0')).toBe(true)
    expect(isValidAllowanceAmount('125')).toBe(true)
    expect(isValidAllowanceAmount('125.5')).toBe(true)
    expect(isValidAllowanceAmount('125.50')).toBe(true)
  })

  it('rejects invalid inputs', () => {
    expect(isValidAllowanceAmount('')).toBe(false)
    expect(isValidAllowanceAmount('-1')).toBe(false)
    expect(isValidAllowanceAmount('1.234')).toBe(false)
    expect(isValidAllowanceAmount('abc')).toBe(false)
  })
})
