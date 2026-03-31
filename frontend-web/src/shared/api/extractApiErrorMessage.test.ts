import { describe, expect, it } from 'vitest'

import { extractApiErrorMessage } from '@/shared/api/extractApiErrorMessage'

describe('extractApiErrorMessage', () => {
  it('returns axios detail when it is a string', () => {
    const error = {
      isAxiosError: true,
      message: 'request failed',
      response: { data: { detail: 'Validation failed' } }
    }

    expect(extractApiErrorMessage(error, 'fallback')).toBe('Validation failed')
  })

  it('returns detail.message when detail is an object', () => {
    const error = {
      isAxiosError: true,
      message: 'request failed',
      response: { data: { detail: { message: 'Structured error' } } }
    }

    expect(extractApiErrorMessage(error, 'fallback')).toBe('Structured error')
  })

  it('returns response.data.message when available', () => {
    const error = {
      isAxiosError: true,
      message: 'request failed',
      response: { data: { message: 'Top-level error' } }
    }

    expect(extractApiErrorMessage(error, 'fallback')).toBe('Top-level error')
  })

  it('falls back to error.message and fallback text', () => {
    expect(extractApiErrorMessage({ isAxiosError: true, message: 'Network' }, 'fallback')).toBe('Network')
    expect(extractApiErrorMessage('unknown', 'fallback')).toBe('fallback')
  })
})
