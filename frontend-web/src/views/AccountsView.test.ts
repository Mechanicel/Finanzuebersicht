// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

import AccountsView from './AccountsView.vue'
import { apiClient } from '../api/client'

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: { personId: 'person-1' } })
}))

vi.mock('../api/client', () => ({
  apiClient: {
    person: vi.fn(),
    accounts: vi.fn(),
    personBanks: vi.fn(),
    banks: vi.fn(),
    createAccount: vi.fn(),
    updateAccount: vi.fn()
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

function buildAccount(label: string) {
  return {
    account_id: 'account-1',
    person_id: 'person-1',
    bank_id: 'bank-1',
    account_type: 'girokonto' as const,
    label,
    balance: '100.00',
    currency: 'EUR',
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
    vi.mocked(apiClient.createAccount).mockResolvedValue(buildAccount('Neu angelegt'))
    vi.mocked(apiClient.updateAccount).mockResolvedValue(buildAccount('Bearbeitetes Konto'))
  })

  it('mounts without runtime-template compilation warning for account form fields', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

    mount(AccountsView, {
      global: {
        stubs: { RouterLink: { template: '<a><slot /></a>' } }
      }
    })
    await flushUi()

    expect(
      warnSpy.mock.calls.some(([message]) =>
        String(message).includes('runtime compilation is not supported in this build of Vue')
      )
    ).toBe(false)

    warnSpy.mockRestore()
  })

  it('submits create form with entered label instead of triggering empty-label validation', async () => {
    const wrapper = mount(AccountsView, {
      global: {
        stubs: { RouterLink: { template: '<a><slot /></a>' } }
      }
    })
    await flushUi()

    const createForm = wrapper.find('article.accounts-card form.account-form')
    await createForm.find('input[placeholder="z. B. Giro Hauptkonto"]').setValue('Giro Urlaub')
    await createForm.find('input[placeholder="0.00"]').setValue('1250.50')
    await createForm.find('input[placeholder="EUR"]').setValue('eur')

    await createForm.trigger('submit.prevent')
    await flushUi()

    expect(apiClient.createAccount).toHaveBeenCalledWith(
      'person-1',
      expect.objectContaining({
        label: 'Giro Urlaub',
        bank_id: 'bank-1',
        balance: '1250.50',
        currency: 'EUR'
      })
    )
    expect(wrapper.text()).not.toContain('Bitte gib eine Bezeichnung für das Konto an.')
  })

  it('submits edit form with changed label', async () => {
    const wrapper = mount(AccountsView, {
      global: {
        stubs: { RouterLink: { template: '<a><slot /></a>' } }
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
    expect(wrapper.text()).not.toContain('Bitte gib eine Bezeichnung für das Konto an.')
  })
})
