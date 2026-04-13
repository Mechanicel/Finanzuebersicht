// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

import AccountsView from '@/modules/accounts/pages/AccountsManagePage.vue'
import { apiClient } from '@/shared/api/client'

const pushMock = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: { personId: 'person-1' } }),
  useRouter: () => ({ push: pushMock })
}))

vi.mock('@/shared/api/client', () => ({
  apiClient: {
    person: vi.fn(),
    accounts: vi.fn(),
    banks: vi.fn(),
    portfolio: vi.fn()
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

const bankResponse = {
  items: [{ bank_id: 'bank-1', name: 'Testbank', bic: 'TESTDEFFXXX', blz: '10000000', country_code: 'DE' }],
  total: 1
}

function buildAccount(
  label: string,
  accountType: 'girokonto' | 'depot' = 'girokonto',
  accountId = 'account-1',
  portfolioId: string | null = null
) {
  return {
    account_id: accountId,
    person_id: 'person-1',
    bank_id: 'bank-1',
    account_type: accountType,
    label,
    balance: '100.00',
    currency: 'EUR',
    portfolio_id: portfolioId,
    iban: accountId === 'account-1' ? 'DE111' : 'DE222',
    created_at: '2026-03-01',
    updated_at: '2026-03-01'
  }
}

async function flushUi() {
  await Promise.resolve()
  await Promise.resolve()
  await Promise.resolve()
  await new Promise((resolve) => setTimeout(resolve, 0))
  await nextTick()
}

describe('AccountsView list flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(apiClient.person).mockResolvedValue(personResponse)
    vi.mocked(apiClient.banks).mockResolvedValue(bankResponse)
    vi.mocked(apiClient.portfolio).mockResolvedValue({
      portfolio_id: 'portfolio-1',
      person_id: 'person-1',
      display_name: 'Depot Langfrist',
      created_at: '2026-03-01',
      updated_at: '2026-03-01',
      holdings: []
    })
    vi.mocked(apiClient.accounts).mockResolvedValue([buildAccount('Bestehendes Konto')])
  })

  it('renders each account row as clickable element and has no bearbeiten button', async () => {
    const wrapper = mount(AccountsView, { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } })
    await flushUi()

    expect(wrapper.find('button.account-row-btn').exists()).toBe(true)
    expect(wrapper.findAll('button').some((button) => button.text() === 'Bearbeiten')).toBe(false)
  })

  it('navigates to dedicated detail route on row click', async () => {
    const wrapper = mount(AccountsView, { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } })
    await flushUi()

    await wrapper.find('button.account-row-btn').trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/accounts/manage/account-1?personId=person-1')
  })

  it('navigates depot rows directly to bestandteile section', async () => {
    vi.mocked(apiClient.accounts).mockResolvedValue([buildAccount('Depot Langfrist', 'depot', 'account-2', 'portfolio-1')])
    const wrapper = mount(AccountsView, { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } })
    await flushUi()

    await wrapper.find('button.account-row-btn').trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/accounts/manage/account-2?personId=person-1&section=bestandteile')
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

  it('renders depot summary card without IBAN and with empty holdings message', async () => {
    vi.mocked(apiClient.accounts).mockResolvedValue([buildAccount('Depot Langfrist', 'depot', 'account-2')])
    const wrapper = mount(AccountsView, { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } })
    await flushUi()

    expect(wrapper.text()).toContain('Noch keine Depot-Bestandteile')
    expect(wrapper.text()).not.toContain('IBAN')
    expect(wrapper.text()).not.toContain('Kontonummer')
  })
})
