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
    mock.onPost('/app/persons').reply(201, { data: { person_id: id, first_name: 'A', last_name: 'B', email: null, created_at: 'x', updated_at: 'x' } })
    mock.onGet(`/app/persons/${id}`).reply(200, { data: { person: { person_id: id, first_name: 'A', last_name: 'B', email: null, created_at: 'x', updated_at: 'x' }, stats: { person_id: id, first_name: 'A', last_name: 'B', email: null, bank_count: 0, allowance_total: '0' } } })
    mock.onPatch(`/app/persons/${id}`).reply(200, { data: { person_id: id, first_name: 'A', last_name: 'C', email: null, created_at: 'x', updated_at: 'y' } })
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
