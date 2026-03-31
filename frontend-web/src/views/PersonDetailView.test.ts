// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

import PersonDetailView from './PersonDetailView.vue'
import { apiClient } from '../api/client'

vi.mock('vue-router', () => ({ useRouter: () => ({ push: vi.fn() }) }))
vi.mock('../api/client', () => ({
  apiClient: {
    person: vi.fn(),
    accounts: vi.fn(),
    updatePerson: vi.fn(),
    deletePerson: vi.fn()
  }
}))

async function flushUi() {
  await Promise.resolve()
  await nextTick()
}

describe('PersonDetailView navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(apiClient.person).mockResolvedValue({
      person: {
        person_id: 'person-1',
        first_name: 'Max',
        last_name: 'Mustermann',
        email: null,
        tax_profile: { tax_country: 'DE', filing_status: 'single' },
        created_at: 'x',
        updated_at: 'x'
      },
      stats: {
        person_id: 'person-1',
        first_name: 'Max',
        last_name: 'Mustermann',
        email: null,
        bank_count: 1,
        allowance_total: '0.00'
      }
    })
    vi.mocked(apiClient.accounts).mockResolvedValue([])
  })

  it('shows account add/manage actions and no holdings shortcut', async () => {
    const wrapper = mount(PersonDetailView, {
      props: { personId: 'person-1' },
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } }
    })

    await flushUi()

    expect(wrapper.text()).toContain('Konto hinzufügen')
    expect(wrapper.text()).toContain('Konten ansehen & bearbeiten')
    expect(wrapper.text()).not.toContain('Holdings / Depot')
  })
})
