// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

import AccountDetailView from './AccountDetailView.vue'
import { apiClient } from '../api/client'

const pushMock = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: { personId: 'person-1' }, params: { accountId: 'account-1' } }),
  useRouter: () => ({ push: pushMock })
}))

vi.mock('../api/client', () => ({
  apiClient: {
    accounts: vi.fn(),
    personBanks: vi.fn(),
    banks: vi.fn(),
    updateAccount: vi.fn(),
    deleteAccount: vi.fn()
  }
}))

async function flushUi() {
  await Promise.resolve()
  await nextTick()
}

describe('AccountDetailView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(apiClient.accounts).mockResolvedValue([
      {
        account_id: 'account-1',
        person_id: 'person-1',
        bank_id: 'bank-1',
        account_type: 'depot',
        label: 'Depot Core',
        balance: '100.00',
        currency: 'EUR',
        created_at: '2026-03-01',
        updated_at: '2026-03-01'
      }
    ])
    vi.mocked(apiClient.personBanks).mockResolvedValue({ items: [{ person_id: 'person-1', bank_id: 'bank-1', assigned_at: '2026-03-01' }], total: 1 })
    vi.mocked(apiClient.banks).mockResolvedValue({
      items: [{ bank_id: 'bank-1', name: 'Testbank', bic: 'TESTDEFFXXX', blz: '10000000', country_code: 'DE' }],
      total: 1
    })
    vi.mocked(apiClient.updateAccount).mockResolvedValue({} as never)
    vi.mocked(apiClient.deleteAccount).mockResolvedValue(undefined)
  })

  it('has back button to account list and renders depot holdings context', async () => {
    const wrapper = mount(AccountDetailView, {
      global: {
        stubs: {
          DepotHoldingsManager: { template: '<div class="depot-stub">DepotStub</div>' }
        }
      }
    })
    await flushUi()

    expect(wrapper.text()).toContain('Zurück zur Kontenliste')
    await wrapper.find('button.flow-btn').trigger('click')
    expect(pushMock).toHaveBeenCalledWith('/accounts/manage?personId=person-1')
    expect(wrapper.find('.depot-stub').exists()).toBe(true)
  })
})
