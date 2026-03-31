import type { AccountCreatePayload, AccountReadModel, AccountType, AccountUpdatePayload } from '../types/models'

export interface AccountFormState {
  account_type: AccountType
  label: string
  bank_id: string
  balance: string
  currency: string
  account_number: string
  depot_number: string
  iban: string
  opening_date: string
  interest_rate: string
  payout_account_iban: string
  settlement_account_iban: string
}

export const accountTypeLabels: Record<AccountType, string> = {
  girokonto: 'Normales Konto (Girokonto)',
  tagesgeldkonto: 'Tagesgeldkonto',
  festgeldkonto: 'Festgeldkonto',
  depot: 'Depot (Wertpapierdepot)'
}

const optionalFields: Record<AccountType, Array<keyof AccountFormState>> = {
  girokonto: ['account_number', 'iban'],
  tagesgeldkonto: ['account_number', 'iban', 'interest_rate', 'payout_account_iban'],
  festgeldkonto: ['account_number', 'iban', 'opening_date', 'interest_rate', 'payout_account_iban'],
  depot: ['depot_number', 'opening_date', 'settlement_account_iban']
}

export function visibleFieldsForAccountType(accountType: AccountType) {
  return optionalFields[accountType]
}

export function createEmptyAccountForm(defaultBankId = ''): AccountFormState {
  return {
    account_type: 'girokonto',
    label: '',
    bank_id: defaultBankId,
    balance: '0.00',
    currency: 'EUR',
    account_number: '',
    depot_number: '',
    iban: '',
    opening_date: '',
    interest_rate: '',
    payout_account_iban: '',
    settlement_account_iban: ''
  }
}

export function createFormFromAccount(account: AccountReadModel): AccountFormState {
  return {
    account_type: account.account_type,
    label: account.label,
    bank_id: account.bank_id,
    balance: account.balance,
    currency: account.currency,
    account_number: account.account_number ?? '',
    depot_number: account.depot_number ?? '',
    iban: account.iban ?? '',
    opening_date: account.opening_date ?? '',
    interest_rate: account.interest_rate ?? '',
    payout_account_iban: account.payout_account_iban ?? '',
    settlement_account_iban: account.settlement_account_iban ?? ''
  }
}

function normalizeOptional(value: string): string | null {
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : null
}

export function toCreatePayload(form: AccountFormState): AccountCreatePayload {
  return {
    account_type: form.account_type,
    label: form.label.trim(),
    bank_id: form.bank_id,
    balance: form.balance.trim(),
    currency: form.currency.trim().toUpperCase(),
    account_number: normalizeOptional(form.account_number),
    depot_number: normalizeOptional(form.depot_number),
    iban: normalizeOptional(form.iban),
    opening_date: normalizeOptional(form.opening_date),
    interest_rate: normalizeOptional(form.interest_rate),
    payout_account_iban: normalizeOptional(form.payout_account_iban),
    settlement_account_iban: normalizeOptional(form.settlement_account_iban)
  }
}

export function toUpdatePayload(form: AccountFormState): AccountUpdatePayload {
  return toCreatePayload(form)
}
