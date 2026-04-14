// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { reactive } from 'vue'
import DashboardPage from '@/modules/dashboard/pages/DashboardPage.vue'

const route = reactive({ query: { personId: 'person-1' } })

vi.mock('vue-router', () => ({
  useRoute: () => route
}))

vi.mock('@/modules/dashboard/api/dashboardApi', () => ({
  fetchDashboardOverview: vi.fn(),
  fetchDashboardAllocation: vi.fn(),
  fetchDashboardTimeseries: vi.fn(),
  fetchDashboardMetrics: vi.fn()
}))

import {
  fetchDashboardOverview,
  fetchDashboardAllocation,
  fetchDashboardTimeseries,
  fetchDashboardMetrics
} from '@/modules/dashboard/api/dashboardApi'

function makeSection(section: string, state: 'ready' | 'pending' | 'stale' | 'error') {
  return {
    person_id: 'person-1',
    section,
    state,
    generated_at: '2026-01-01T00:00:00Z',
    stale_at: null,
    refresh_in_progress: false,
    warnings: [],
    payload: {}
  }
}

function mountDashboardPage() {
  return mount(DashboardPage, {
    global: {
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
        DashboardOverviewSection: {
          props: ['section', 'errorMessage'],
          template: '<div data-test="overview">overview:{{ section.state }}|{{ errorMessage }}</div>'
        },
        DashboardAllocationSection: {
          props: ['section'],
          template: '<div data-test="allocation">allocation:{{ section.state }}</div>'
        },
        DashboardTimeseriesSection: {
          props: ['section'],
          template: '<div data-test="timeseries">timeseries:{{ section.state }}</div>'
        },
        DashboardMetricsSection: {
          props: ['section'],
          template: '<div data-test="metrics">metrics:{{ section.state }}</div>'
        },
        LegacyAnalyticsSection: {
          props: ['open'],
          emits: ['update:open'],
          template:
            '<section data-test="legacy"><button data-test="open-legacy" @click="$emit(\'update:open\', true)" />' +
            '<button data-test="close-legacy" @click="$emit(\'update:open\', false)" /><slot /></section>'
        },
        PortfolioDashboardContainer: { template: '<div data-test="portfolio-cockpit" />' },
        DepotAnalysisWorkspace: { template: '<div data-test="depot" />' }
      }
    }
  })
}

describe('DashboardPage', () => {
  const wrappers: Array<ReturnType<typeof mountDashboardPage>> = []

  beforeEach(() => {
    vi.resetAllMocks()
    route.query.personId = 'person-1'

    vi.mocked(fetchDashboardOverview).mockResolvedValue(makeSection('overview', 'ready'))
    vi.mocked(fetchDashboardAllocation).mockResolvedValue(makeSection('allocation', 'ready'))
    vi.mocked(fetchDashboardTimeseries).mockResolvedValue(makeSection('timeseries', 'stale'))
    vi.mocked(fetchDashboardMetrics).mockResolvedValue(makeSection('metrics', 'ready'))
  })

  afterEach(() => {
    while (wrappers.length > 0) {
      wrappers.pop()?.unmount()
    }
  })

  it('does not start legacy requests on initial load while legacy section is closed', async () => {
    const wrapper = mountDashboardPage()
    wrappers.push(wrapper)

    await flushPromises()

    expect(wrapper.find('[data-test="legacy"]').exists()).toBe(true)
    expect(fetchDashboardOverview).not.toHaveBeenCalled()
    expect(fetchDashboardAllocation).not.toHaveBeenCalled()
    expect(fetchDashboardTimeseries).not.toHaveBeenCalled()
    expect(fetchDashboardMetrics).not.toHaveBeenCalled()
  })

  it('does not mount DepotAnalysisWorkspace initially', async () => {
    const wrapper = mountDashboardPage()
    wrappers.push(wrapper)

    await flushPromises()

    expect(wrapper.find('[data-test="depot"]').exists()).toBe(false)
  })

  it('starts legacy requests when opening legacy section', async () => {
    const wrapper = mountDashboardPage()
    wrappers.push(wrapper)

    await wrapper.get('[data-test="open-legacy"]').trigger('click')
    await flushPromises()

    expect(fetchDashboardOverview).toHaveBeenCalledWith('person-1')
    expect(fetchDashboardAllocation).toHaveBeenCalledWith('person-1')
    expect(fetchDashboardTimeseries).toHaveBeenCalledWith('person-1')
    expect(fetchDashboardMetrics).toHaveBeenCalledWith('person-1')
    expect(wrapper.find('[data-test="depot"]').exists()).toBe(true)
  })

  it('does not start legacy requests on personId change while legacy section stays closed', async () => {
    const wrapper = mountDashboardPage()
    wrappers.push(wrapper)
    await flushPromises()

    route.query.personId = 'person-2'
    await flushPromises()

    expect(fetchDashboardOverview).not.toHaveBeenCalled()
    expect(fetchDashboardAllocation).not.toHaveBeenCalled()
    expect(fetchDashboardTimeseries).not.toHaveBeenCalled()
    expect(fetchDashboardMetrics).not.toHaveBeenCalled()
  })
})
