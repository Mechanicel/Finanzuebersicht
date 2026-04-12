import type {
  PortfolioAttributionBucket,
  PortfolioAttributionBucketKey,
  PortfolioAttributionItem,
  PortfolioAttributionReadModel,
  PortfolioContributorsReadModel,
  PortfolioPerformanceReadModel,
  PortfolioRiskReadModel
} from '@/shared/model/types'

export interface AttributionSectionDefinition {
  key: PortfolioAttributionBucketKey
  title: string
  bucketKey: keyof Pick<
    PortfolioAttributionReadModel,
    'by_position' | 'by_sector' | 'by_country' | 'by_currency'
  >
}

export interface NormalizedAttributionBucket {
  positive: PortfolioAttributionItem[]
  negative: PortfolioAttributionItem[]
}

export const attributionSections: AttributionSectionDefinition[] = [
  { key: 'position', title: 'Positionen', bucketKey: 'by_position' },
  { key: 'sector', title: 'Sektoren', bucketKey: 'by_sector' },
  { key: 'country', title: 'Laender', bucketKey: 'by_country' },
  { key: 'currency', title: 'Waehrungen', bucketKey: 'by_currency' }
]

function hasNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

function firstNumber(...values: unknown[]): number | null {
  return values.find((value): value is number => hasNumber(value)) ?? null
}

function firstText(...values: unknown[]): string {
  for (const value of values) {
    if (typeof value === 'string' && value.trim().length > 0) {
      return value.trim()
    }
  }

  return ''
}

function asAttributionItem(rawItem: unknown): PortfolioAttributionItem | null {
  if (!rawItem || typeof rawItem !== 'object') return null

  const item = rawItem as Record<string, unknown>
  const contribution = firstNumber(
    item.contribution_pct_points,
    item.contribution_pp,
    item.contribution,
    item.value,
    item.pp
  )
  const label = firstText(item.label, item.display_name, item.name, item.symbol, item.id)

  if (contribution == null || !label) return null

  return {
    ...item,
    label,
    symbol: typeof item.symbol === 'string' ? item.symbol : null,
    contribution_pct_points: contribution,
    return_pct: hasNumber(item.return_pct) ? item.return_pct : null,
    weight: hasNumber(item.weight) ? item.weight : null,
    market_value: hasNumber(item.market_value) ? item.market_value : null,
    direction: typeof item.direction === 'string' ? item.direction : contribution > 0 ? 'positive' : contribution < 0 ? 'negative' : 'neutral'
  }
}

function normalizeItems(items: unknown): PortfolioAttributionItem[] {
  return Array.isArray(items)
    ? items.map((item) => asAttributionItem(item)).filter((item): item is PortfolioAttributionItem => Boolean(item))
    : []
}

function sortPositive(items: PortfolioAttributionItem[]) {
  return [...items].sort(
    (left, right) => right.contribution_pct_points - left.contribution_pct_points || left.label.localeCompare(right.label)
  )
}

function sortNegative(items: PortfolioAttributionItem[]) {
  return [...items].sort(
    (left, right) => left.contribution_pct_points - right.contribution_pct_points || left.label.localeCompare(right.label)
  )
}

export function normalizeAttributionBucket(
  bucket: PortfolioAttributionBucket | null | undefined
): NormalizedAttributionBucket {
  if (!bucket) {
    return { positive: [], negative: [] }
  }

  if (Array.isArray(bucket)) {
    const items = normalizeItems(bucket)
    return {
      positive: sortPositive(items.filter((item) => item.contribution_pct_points > 0)),
      negative: sortNegative(items.filter((item) => item.contribution_pct_points < 0))
    }
  }

  const explicitPositive = [
    ...normalizeItems(bucket.top_positive),
    ...normalizeItems(bucket.positive),
    ...normalizeItems(bucket.top_contributors)
  ]
  const explicitNegative = [
    ...normalizeItems(bucket.top_negative),
    ...normalizeItems(bucket.negative),
    ...normalizeItems(bucket.top_detractors)
  ]
  const unclassified = normalizeItems(bucket.items)

  const positive = explicitPositive.length
    ? explicitPositive
    : unclassified.filter((item) => item.contribution_pct_points > 0)
  const negative = explicitNegative.length
    ? explicitNegative
    : unclassified.filter((item) => item.contribution_pct_points < 0)

  return {
    positive: sortPositive(positive),
    negative: sortNegative(negative)
  }
}

function contributorToAttributionItem(item: Record<string, unknown>, forceNegative = false): PortfolioAttributionItem | null {
  const normalized = asAttributionItem({
    ...item,
    label: firstText(item.display_name, item.symbol),
    contribution_pct_points: firstNumber(item.contribution_pct_points, item.contribution_return)
  })

  if (!normalized) return null

  return forceNegative && normalized.contribution_pct_points > 0
    ? { ...normalized, contribution_pct_points: -normalized.contribution_pct_points }
    : normalized
}

export function buildFallbackAttributionFromContributors(options: {
  contributors?: PortfolioContributorsReadModel | null
  performance?: PortfolioPerformanceReadModel | null
  risk?: PortfolioRiskReadModel | null
  personId?: string | null
}): PortfolioAttributionReadModel | null {
  const contributors = options.contributors
  if (!contributors) return null

  const topPositive = (contributors.top_contributors ?? [])
    .map((item) => contributorToAttributionItem(item as unknown as Record<string, unknown>))
    .filter((item): item is PortfolioAttributionItem => Boolean(item))
  const topNegative = (contributors.top_detractors ?? [])
    .map((item) => contributorToAttributionItem(item as unknown as Record<string, unknown>, true))
    .filter((item): item is PortfolioAttributionItem => Boolean(item))

  return {
    person_id: contributors.person_id || options.personId || '',
    as_of: contributors.as_of ?? (options.performance?.meta?.as_of as string | undefined) ?? '',
    range: contributors.range ?? options.performance?.range ?? '3m',
    range_label: contributors.range_label ?? options.performance?.range_label ?? null,
    benchmark_symbol: options.performance?.benchmark_symbol ?? options.risk?.benchmark_symbol ?? null,
    methodology: {
      key: contributors.methodology ?? contributors.return_basis ?? 'range_contribution',
      label: contributors.methodology ?? contributors.return_basis ?? 'range contribution',
      description: 'Fallback from portfolio contributors while portfolio attribution is unavailable.',
      contribution_basis: 'return contribution over selected range',
      contribution_unit: 'percentage_points'
    },
    summary: {
      portfolio_return_pct: options.performance?.summary?.return_pct ?? null,
      total_contribution_pct_points: contributors.total_contribution_pct_points ?? 0,
      residual_pct_points:
        options.performance?.summary?.return_pct != null && contributors.total_contribution_pct_points != null
          ? options.performance.summary.return_pct - contributors.total_contribution_pct_points
          : null,
      covered_positions: topPositive.length + topNegative.length,
      total_positions: topPositive.length + topNegative.length,
      unattributed_positions: 0
    },
    by_position: [...topPositive, ...topNegative],
    by_sector: [],
    by_country: [],
    by_currency: [],
    warnings: contributors.warnings ?? [],
    meta: {
      ...(contributors.meta ?? {}),
      source: 'contributors_fallback'
    }
  }
}

export function resolvePortfolioAttribution(options: {
  attribution?: PortfolioAttributionReadModel | null
  contributors?: PortfolioContributorsReadModel | null
  performance?: PortfolioPerformanceReadModel | null
  risk?: PortfolioRiskReadModel | null
  personId?: string | null
}): PortfolioAttributionReadModel | null {
  return (
    options.attribution ??
    buildFallbackAttributionFromContributors({
      contributors: options.contributors,
      performance: options.performance,
      risk: options.risk,
      personId: options.personId
    })
  )
}
