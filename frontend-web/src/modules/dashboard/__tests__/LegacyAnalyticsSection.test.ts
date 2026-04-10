// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import LegacyAnalyticsSection from '@/modules/dashboard/components/LegacyAnalyticsSection.vue'

describe('LegacyAnalyticsSection', () => {
  it('renders collapsed by default and emits open state updates', async () => {
    const wrapper = mount(LegacyAnalyticsSection, {
      slots: {
        default: '<div data-test="legacy-content">Legacy content</div>'
      }
    })

    expect(wrapper.find('details').attributes('open')).toBeUndefined()
    expect(wrapper.text()).toContain('Weitere Analytics (Legacy)')
    expect(wrapper.find('[data-test="legacy-content"]').exists()).toBe(true)

    const detailsElement = wrapper.find('details').element as HTMLDetailsElement
    detailsElement.open = true
    await wrapper.find('details').trigger('toggle')
    expect(wrapper.emitted('update:open')?.[0]).toEqual([true])
  })
})
