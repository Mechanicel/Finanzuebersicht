import axios from 'axios'

export function extractApiErrorMessage(error: unknown, fallback: string): string {
  if (!axios.isAxiosError(error)) {
    return error instanceof Error ? error.message : fallback
  }

  const detail = error.response?.data?.detail
  if (typeof detail === 'string') {
    return detail
  }

  if (detail && typeof detail === 'object' && 'message' in detail && typeof detail.message === 'string') {
    return detail.message
  }

  const message = error.response?.data?.message
  if (typeof message === 'string') {
    return message
  }

  return error.message || fallback
}
