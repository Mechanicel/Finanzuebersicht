// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

import AccountsCreateView from '@/modules/accounts/pages/AccountCreatePage.vue'
import { apiClient } from '@/shared/api/client'

const pushMock = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: { personId: 'person-1' } }),
  useRouter: () => ({ push: pushMock })
}))

vi.mock('@/shared/api/client', () => ({
  apiClient: {
    person: vi.fn(),
    personBanks: vi.fn(),
    banks: vi.fn(),
    createAccount: vi.fn()
  }
}))

const personResponse = {
  person: {
    person_id: 'person-1',
    first_name: 'Max',
    last_name: 'Mustermann',
    email: null,
    tax_profile: { tax_country: 'DE', filing_status: 'single' as const },
    created_at: '2026-03-01',
    updated_at: '2026-03-01'
  },
  stats: { person_id: 'person-1', first_name: 'Max', last_name: 'Mustermann', email: null, bank_count: 1, allowance_total: '0.00' }
}

async function flushUi() {
  await Promise.resolve()
  await nextTick()
}

describe('AccountsCreateView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(apiClient.person).mockResolvedValue(personResponse)
    vi.mocked(apiClient.personBanks).mockResolvedValue({ items: [{ person_id: 'person-1', bank_id: 'bank-1', assigned_at: 'x' }], total: 1 })
    vi.mocked(apiClient.banks).mockResolvedValue({
      items: [{ bank_id: 'bank-1', name: 'Testbank', bic: 'TESTDEFFXXX', blz: '10000000', country_code: 'DE' }],
      total: 1
    })
    vi.mocked(apiClient.createAccount).mockResolvedValue({
      account_id: 'account-created',
      person_id: 'person-1',
      bank_id: 'bank-1',
      account_type: 'depot',
      label: 'Depot Langfrist',
      balance: '1000.00',
      currency: 'EUR',
      created_at: '2026-03-01',
      updated_at: '2026-03-01',
    } as never)
  })

  it('navigates back to person hub after successful normal account creation', async () => {
    const wrapper = mount(AccountsCreateView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } }
    })
    await flushUi()

    const form = wrapper.find('form.account-form')
    await form.find('input[placeholder="z. B. Giro Hauptkonto"]').setValue('Giro')
    await form.find('input[placeholder="0.00"]').setValue('1250.50')
    await form.find('input[placeholder="EUR"]').setValue('eur')

    await form.trigger('submit.prevent')
    await flushUi()

    expect(apiClient.createAccount).toHaveBeenCalled()
    expect(pushMock).toHaveBeenCalledWith('/persons/person-1')
  })

  it('routes depot creation into dedicated holdings screen instead of inline expansion', async () => {
    const wrapper = mount(AccountsCreateView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } }
    })
    await flushUi()

    await wrapper.find('select.input').setValue('depot')
    const form = wrapper.find('form.account-form')
    await form.find('input[placeholder="z. B. Giro Hauptkonto"]').setValue('Depot Langfrist')
    await form.find('input[placeholder="0.00"]').setValue('1000')
    await form.trigger('submit.prevent')
    await flushUi()

    expect(apiClient.createAccount).toHaveBeenCalledWith('person-1', expect.objectContaining({ account_type: 'depot' }))
    expect(pushMock).toHaveBeenCalledWith('/accounts/depot-holdings?personId=person-1&accountId=account-created&depotLabel=Depot%20Langfrist&origin=create')
    expect(wrapper.text()).not.toContain('Depot-Flow abschließen')
  })
})
