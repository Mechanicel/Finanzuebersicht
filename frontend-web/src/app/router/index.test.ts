// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest'
import { router } from './index'

describe('router', () => {
  afterEach(async () => {
    await router.push('/')
    await router.isReady()
  })

  it('does not provide obsolete /holdings route', () => {
    expect(router.resolve('/holdings').matched).toHaveLength(0)
  })

  it('provides dedicated depot holdings screen route', () => {
    expect(router.resolve('/accounts/depot-holdings').matched).toHaveLength(1)
  })

  it('redirects /dashboard without personId to home on initial navigation', async () => {
    await router.push('/dashboard')
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/')
  })

  it('allows /dashboard navigation when personId query is present', async () => {
    await router.push('/dashboard?personId=123')
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/dashboard')
    expect(router.currentRoute.value.query.personId).toBe('123')
  })
})
