export function normalizeAllowanceInput(value: unknown): string {
  if (value === null || value === undefined) {
    return ''
  }

  return String(value).trim()
}

export function isValidAllowanceAmount(value: string): boolean {
  return /^\d+(\.\d{1,2})?$/.test(value)
}
