// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import LegacyAnalyticsSection from '@/modules/dashboard/components/LegacyAnalyticsSection.vue'

describe('LegacyAnalyticsSection', () => {
  it('renders collapsed legacy wrapper with slot content', () => {
    const wrapper = mount(LegacyAnalyticsSection, {
      slots: {
        default: '<div data-test="legacy-content">Legacy content</div>'
      }
    })

    expect(wrapper.find('details').attributes('open')).toBeUndefined()
    expect(wrapper.text()).toContain('Weitere Analytics (Legacy)')
    expect(wrapper.find('[data-test="legacy-content"]').exists()).toBe(true)
  })
})
