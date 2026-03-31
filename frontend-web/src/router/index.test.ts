// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { router } from './index'

describe('router', () => {
  it('does not provide obsolete /holdings route', () => {
    expect(router.resolve('/holdings').matched).toHaveLength(0)
  })
})
