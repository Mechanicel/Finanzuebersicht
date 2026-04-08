// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
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

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    route.query.personId = 'person-1'
  })

  it('loads dashboard sections independently and keeps shell visible', async () => {
    vi.mocked(fetchDashboardOverview).mockRejectedValue({
      isAxiosError: true,
      code: 'ECONNABORTED',
      message: 'timeout of 8000ms exceeded'
    })
    vi.mocked(fetchDashboardAllocation).mockResolvedValue(makeSection('allocation', 'ready'))
    vi.mocked(fetchDashboardTimeseries).mockResolvedValue(makeSection('timeseries', 'stale'))
    vi.mocked(fetchDashboardMetrics).mockResolvedValue(makeSection('metrics', 'ready'))

    const wrapper = mount(DashboardPage, {
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
          DepotAnalysisWorkspace: { template: '<div data-test="depot" />' }
        }
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('Analytics-Dashboard')
    expect(fetchDashboardOverview).toHaveBeenCalledWith('person-1')
    expect(fetchDashboardAllocation).toHaveBeenCalledWith('person-1')
    expect(fetchDashboardTimeseries).toHaveBeenCalledWith('person-1')
    expect(fetchDashboardMetrics).toHaveBeenCalledWith('person-1')

    expect(wrapper.get('[data-test="overview"]').text()).toContain('overview:error')
    expect(wrapper.get('[data-test="overview"]').text()).not.toContain('timeout of 8000ms exceeded')
    expect(wrapper.get('[data-test="allocation"]').text()).toContain('allocation:ready')
    expect(wrapper.get('[data-test="timeseries"]').text()).toContain('timeseries:stale')
    expect(wrapper.get('[data-test="metrics"]').text()).toContain('metrics:ready')
  })
})
