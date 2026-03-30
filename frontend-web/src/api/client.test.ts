import { afterEach, describe, expect, it } from 'vitest'
import MockAdapter from 'axios-mock-adapter'

import { apiClient } from './client'
import { http } from './http'

const mock = new MockAdapter(http)

afterEach(() => {
  mock.reset()
})

describe('apiClient person CRUD', () => {
  it('calls list endpoint with optional search parameters', async () => {
    mock.onGet('/app/persons').reply(200, { data: { items: [], pagination: { limit: 25, offset: 0, returned: 0, total: 0 } } })

    const result = await apiClient.persons({ q: 'anna', limit: 10, offset: 5 })

    expect(result.pagination.total).toBe(0)
    expect(mock.history.get[0]?.params).toEqual({ q: 'anna', limit: 10, offset: 5 })
  })

  it('calls create/update/delete/detail endpoints', async () => {
    const id = '00000000-0000-0000-0000-000000000101'
    mock.onPost('/app/persons').reply(201, { data: { person_id: id, first_name: 'A', last_name: 'B', email: null, tax_profile: { tax_country: 'DE', filing_status: 'single' }, created_at: 'x', updated_at: 'x' } })
    mock.onGet(`/app/persons/${id}`).reply(200, { data: { person: { person_id: id, first_name: 'A', last_name: 'B', email: null, tax_profile: { tax_country: 'DE', filing_status: 'single' }, created_at: 'x', updated_at: 'x' }, stats: { person_id: id, first_name: 'A', last_name: 'B', email: null, bank_count: 0, allowance_total: '0' } } })
    mock.onPatch(`/app/persons/${id}`).reply(200, { data: { person_id: id, first_name: 'A', last_name: 'C', email: null, tax_profile: { tax_country: 'DE', filing_status: 'single' }, created_at: 'x', updated_at: 'y' } })
    mock.onDelete(`/app/persons/${id}`).reply(204)

    expect((await apiClient.createPerson({ first_name: 'A', last_name: 'B' })).person_id).toBe(id)
    expect((await apiClient.person(id)).person.person_id).toBe(id)
    expect((await apiClient.updatePerson(id, { last_name: 'C' })).last_name).toBe('C')
    await expect(apiClient.deletePerson(id)).resolves.toBeUndefined()
  })
})

describe('apiClient bank endpoints', () => {
  it('calls list/create bank endpoints', async () => {
    mock.onGet('/app/banks').reply(200, {
      data: {
        items: [{ bank_id: 'b1', name: 'Bank', bic: 'DEUTDEFFXXX', blz: '12345678', country_code: 'DE' }],
        total: 1
      }
    })
    mock.onPost('/app/banks').reply(201, {
      data: { bank_id: 'b2', name: 'Neue Bank', bic: 'MARKDEF1100', blz: '87654321', country_code: 'DE' }
    })

    const list = await apiClient.banks()
    const created = await apiClient.createBank({
      name: 'Neue Bank',
      bic: 'MARKDEF1100',
      blz: '87654321',
      country_code: 'DE'
    })

    expect(list.total).toBe(1)
    expect(created.bank_id).toBe('b2')
  })
})

describe('apiClient person bank assignments', () => {
  it('calls person bank assignment endpoints', async () => {
    const personId = '00000000-0000-0000-0000-000000000101'
    const bankId = '30000000-0000-0000-0000-000000000001'

    mock.onGet(`/app/persons/${personId}/banks`).reply(200, {
      data: {
        items: [{ person_id: personId, bank_id: bankId, assigned_at: '2026-03-01T08:00:00+00:00' }],
        total: 1
      }
    })
    mock.onPost(`/app/persons/${personId}/banks/${bankId}`).reply(201, {
      data: { person_id: personId, bank_id: bankId, assigned_at: '2026-03-01T08:00:00+00:00' }
    })
    mock.onDelete(`/app/persons/${personId}/banks/${bankId}`).reply(204)

    const list = await apiClient.personBanks(personId)
    const assigned = await apiClient.assignBank(personId, bankId)
    await expect(apiClient.unassignBank(personId, bankId)).resolves.toBeUndefined()

    expect(list.total).toBe(1)
    expect(assigned.bank_id).toBe(bankId)
  })
})

describe('apiClient allowances', () => {
  it('calls person allowance endpoints', async () => {
    const personId = '00000000-0000-0000-0000-000000000101'
    const bankId = '30000000-0000-0000-0000-000000000001'
    const taxYear = 2026

    mock.onGet(`/app/persons/${personId}/allowances`).reply(200, {
      data: {
        items: [{ person_id: personId, bank_id: bankId, tax_year: taxYear, amount: '75.00', currency: 'EUR', updated_at: '2026-03-01' }],
        total: 1,
        amount_total: '75.00'
      }
    })
    mock.onPut(`/app/persons/${personId}/allowances/${bankId}`).reply(200, {
      data: { person_id: personId, bank_id: bankId, tax_year: taxYear, amount: '125.00', currency: 'EUR', updated_at: '2026-03-02' }
    })
    mock.onGet(`/app/persons/${personId}/allowances/summary`).reply(200, {
      data: {
        person_id: personId,
        tax_year: taxYear,
        banks: [{ bank_id: bankId, tax_year: taxYear, amount: '125.00' }],
        total_amount: '125.00',
        annual_limit: '1000.00',
        remaining_amount: '875.00',
        currency: 'EUR'
      }
    })

    const list = await apiClient.allowances(personId, taxYear)
    const changed = await apiClient.setAllowance(personId, bankId, { tax_year: taxYear, amount: '125.00', currency: 'EUR' })
    const summary = await apiClient.allowanceSummary(personId, taxYear)

    expect(list.total).toBe(1)
    expect(changed.amount).toBe('125.00')
    expect(summary.total_amount).toBe('125.00')
    expect(summary.remaining_amount).toBe('875.00')
    expect(mock.history.get[0]?.params).toEqual({ tax_year: taxYear })
    expect(mock.history.get[1]?.params).toEqual({ tax_year: taxYear })
    expect(mock.history.put[0]?.data).toBe(JSON.stringify({ tax_year: taxYear, amount: '125.00', currency: 'EUR' }))
  })
})
