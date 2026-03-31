import { describe, expect, it } from 'vitest'
import {
  createEmptyAccountForm,
  toCreatePayload,
  visibleFieldsForAccountType
} from '@/modules/accounts/model/accountForm'

describe('accountForm helpers', () => {
  it('returns type-specific optional fields', () => {
    expect(visibleFieldsForAccountType('girokonto')).toEqual(['account_number', 'iban'])
    expect(visibleFieldsForAccountType('depot')).toEqual(['depot_number', 'opening_date', 'settlement_account_iban'])
  })

  it('normalizes create payload', () => {
    const form = createEmptyAccountForm('30000000-0000-0000-0000-000000000001')
    form.label = '  Tagesgeld Reserve  '
    form.account_type = 'tagesgeldkonto'
    form.balance = '5000.00'
    form.currency = 'eur'
    form.iban = '  DE00  '
    form.account_number = ''

    const payload = toCreatePayload(form)

    expect(payload.label).toBe('Tagesgeld Reserve')
    expect(payload.currency).toBe('EUR')
    expect(payload.iban).toBe('DE00')
    expect(payload.account_number).toBeNull()
  })
})
