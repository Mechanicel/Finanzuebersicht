// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

import AccountsView from './AccountsView.vue'
import { apiClient } from '../api/client'

const pushMock = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: { personId: 'person-1' } }),
  useRouter: () => ({ push: pushMock })
}))

vi.mock('../api/client', () => ({
  apiClient: {
    person: vi.fn(),
    accounts: vi.fn(),
    personBanks: vi.fn(),
    banks: vi.fn(),
    updateAccount: vi.fn(),
    deleteAccount: vi.fn()
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
  stats: {
    person_id: 'person-1',
    first_name: 'Max',
    last_name: 'Mustermann',
    email: null,
    bank_count: 1,
    allowance_total: '0.00'
  }
}

const bankResponse = {
  items: [
    {
      bank_id: 'bank-1',
      name: 'Testbank',
      bic: 'TESTDEFFXXX',
      blz: '10000000',
      country_code: 'DE'
    }
  ],
  total: 1
}

const assignmentResponse = {
  items: [{ person_id: 'person-1', bank_id: 'bank-1', assigned_at: '2026-03-01T00:00:00+00:00' }],
  total: 1
}

function buildAccount(label: string, accountType: 'girokonto' | 'depot' = 'girokonto', accountId = 'account-1') {
  return {
    account_id: accountId,
    person_id: 'person-1',
    bank_id: 'bank-1',
    account_type: accountType,
    label,
    balance: '100.00',
    currency: 'EUR',
    iban: accountId === 'account-1' ? 'DE111' : 'DE222',
    created_at: '2026-03-01',
    updated_at: '2026-03-01'
  }
}

async function flushUi() {
  await Promise.resolve()
  await nextTick()
}

describe('AccountsView form wiring', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(apiClient.person).mockResolvedValue(personResponse)
    vi.mocked(apiClient.banks).mockResolvedValue(bankResponse)
    vi.mocked(apiClient.personBanks).mockResolvedValue(assignmentResponse)
    vi.mocked(apiClient.accounts).mockResolvedValue([buildAccount('Bestehendes Konto')])
    vi.mocked(apiClient.updateAccount).mockResolvedValue(buildAccount('Bearbeitetes Konto'))
    vi.mocked(apiClient.deleteAccount).mockResolvedValue(undefined)
  })

  it('submits edit form with changed label', async () => {
    const wrapper = mount(AccountsView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } }
      }
    })
    await flushUi()

    await wrapper.find('button.secondary').trigger('click')
    await nextTick()

    const editForm = wrapper.find('form.edit-form')
    await editForm.find('input[placeholder="z. B. Giro Hauptkonto"]').setValue('Giro umbenannt')
    await editForm.trigger('submit.prevent')
    await flushUi()

    expect(apiClient.updateAccount).toHaveBeenCalledWith(
      'person-1',
      'account-1',
      expect.objectContaining({ label: 'Giro umbenannt' })
    )
  })

  it('filters account list through search input', async () => {
    vi.mocked(apiClient.accounts).mockResolvedValue([
      buildAccount('Giro Alltag', 'girokonto', 'account-1'),
      buildAccount('Depot Langfrist', 'depot', 'account-2')
    ])
    const wrapper = mount(AccountsView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } }
    })
    await flushUi()

    expect(wrapper.text()).toContain('Giro Alltag')
    expect(wrapper.text()).toContain('Depot Langfrist')

    await wrapper.find('input[type="search"]').setValue('langfrist')
    await flushUi()

    expect(wrapper.text()).not.toContain('Giro Alltag')
    expect(wrapper.text()).toContain('Depot Langfrist')
  })

  it('shows delete button and opens confirmation dialog; cancel does not delete', async () => {
    const wrapper = mount(AccountsView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } }
    })
    await flushUi()

    await wrapper.find('button.secondary').trigger('click')
    await flushUi()

    const deleteButton = wrapper.findAll('button').find((button) => button.text() === 'Löschen')
    expect(deleteButton).toBeTruthy()
    await deleteButton!.trigger('click')
    await flushUi()

    expect(wrapper.text()).toContain('Konto löschen?')

    const cancelButton = wrapper.findAll('button').find((button) => button.text() === 'Abbrechen')
    expect(cancelButton).toBeTruthy()
    await cancelButton!.trigger('click')
    await flushUi()

    expect(apiClient.deleteAccount).not.toHaveBeenCalled()
  })

  it('deletes account only after confirmation', async () => {
    const wrapper = mount(AccountsView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } }
    })
    await flushUi()

    await wrapper.find('button.secondary').trigger('click')
    await flushUi()

    const deleteButton = wrapper.findAll('button').find((button) => button.text() === 'Löschen')
    await deleteButton!.trigger('click')
    await flushUi()

    const confirmButton = wrapper.findAll('button').find((button) => button.text() === 'Löschen bestätigen')
    await confirmButton!.trigger('click')
    await flushUi()

    expect(apiClient.deleteAccount).toHaveBeenCalledWith('person-1', 'account-1')
  })

  it('opens dedicated depot holdings route during edit flow', async () => {
    vi.mocked(apiClient.accounts).mockResolvedValue([buildAccount('Depot Core', 'depot')])
    const wrapper = mount(AccountsView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } }
    })
    await flushUi()

    await wrapper.find('button.secondary').trigger('click')
    await flushUi()

    const holdingsButton = wrapper.findAll('button').find((button) => button.text() === 'Depot-Positionen öffnen')
    await holdingsButton!.trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/accounts/depot-holdings?personId=person-1&depotLabel=Depot%20Core&origin=manage')
  })
})
