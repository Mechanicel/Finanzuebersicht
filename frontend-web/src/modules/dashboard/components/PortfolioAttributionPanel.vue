<template>
  <article class="attribution-panel" data-testid="portfolio-attribution-panel" :data-state="panelState">
    <header class="panel-header">
      <div>
        <p class="eyebrow">Attribution</p>
        <h3>Warum lief das Portfolio so?</h3>
      </div>
      <span class="panel-status" :class="{ 'panel-status--empty': !hasAnyRows }">
        {{ statusLabel }}
      </span>
    </header>

    <div class="meta-strip" data-testid="attribution-meta">
      <span><strong>Zeitraum</strong> {{ rangeLabel }}</span>
      <span><strong>Stand</strong> {{ asOfLabel }}</span>
      <span><strong>Benchmark</strong> {{ benchmarkLabel }}</span>
      <span><strong>Methodik</strong> {{ methodologyLabel }}</span>
    </div>

    <p v-if="warningLabel" class="warning-line" data-testid="attribution-warnings">
      Hinweise: {{ warningLabel }}
    </p>

    <div class="attribution-grid" data-testid="attribution-grid">
      <section
        v-for="section in sections"
        :key="section.key"
        class="attribution-section"
        :class="{ 'attribution-section--empty': section.rowCount === 0 }"
        :data-testid="`attribution-section-${section.key}`"
      >
        <header class="section-header">
          <h4>{{ section.title }}</h4>
          <span class="section-count">{{ section.rowCount }}</span>
        </header>

        <div class="split-lists">
          <div class="split-list split-list--positive">
            <p class="split-title">Positiv</p>
            <ul v-if="section.positive.length > 0">
              <li
                v-for="item in section.positive"
                :key="`${section.key}-positive-${item.symbol ?? item.label}`"
                :data-testid="`attribution-positive-${section.key}`"
              >
                <span class="item-label">{{ item.label }}</span>
                <strong class="item-value item-value--positive">{{ formatContribution(item.contribution_pct_points) }}</strong>
              </li>
            </ul>
            <p v-else class="empty-copy" :data-testid="`attribution-empty-positive-${section.key}`">
              Keine positiven Beitraege
            </p>
          </div>

          <div class="split-list split-list--negative">
            <p class="split-title">Negativ</p>
            <ul v-if="section.negative.length > 0">
              <li
                v-for="item in section.negative"
                :key="`${section.key}-negative-${item.symbol ?? item.label}`"
                :data-testid="`attribution-negative-${section.key}`"
              >
                <span class="item-label">{{ item.label }}</span>
                <strong class="item-value item-value--negative">{{ formatContribution(item.contribution_pct_points) }}</strong>
              </li>
            </ul>
            <p v-else class="empty-copy" :data-testid="`attribution-empty-negative-${section.key}`">
              Keine negativen Beitraege
            </p>
          </div>
        </div>
      </section>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type {
  PortfolioAttributionBucketKey,
  PortfolioAttributionItem,
  PortfolioAttributionReadModel
} from '@/shared/model/types'
import {
  attributionSections,
  normalizeAttributionBucket
} from '@/modules/dashboard/model/portfolioAttribution'
import {
  formatDate,
  formatNullableText,
  formatRangeLabel,
  formatSignedPercentPoints,
  getStringMeta,
  mapPortfolioMethodology,
  mapPortfolioWarning
} from '@/modules/dashboard/model/portfolioFormatting'

interface AttributionPanelSection {
  key: PortfolioAttributionBucketKey
  title: string
  positive: PortfolioAttributionItem[]
  negative: PortfolioAttributionItem[]
  rowCount: number
}

const props = withDefaults(
  defineProps<{
    attribution?: PortfolioAttributionReadModel | null
    maxItemsPerSide?: number
  }>(),
  {
    attribution: null,
    maxItemsPerSide: 3
  }
)

const sections = computed<AttributionPanelSection[]>(() =>
  attributionSections.map((definition) => {
    const bucket = normalizeAttributionBucket(props.attribution?.[definition.bucketKey])
    const positive = bucket.positive.slice(0, props.maxItemsPerSide)
    const negative = bucket.negative.slice(0, props.maxItemsPerSide)

    return {
      key: definition.key,
      title: definition.title,
      positive,
      negative,
      rowCount: positive.length + negative.length
    }
  })
)

const hasAnyRows = computed(() => sections.value.some((section) => section.rowCount > 0))
const filledSectionCount = computed(() => sections.value.filter((section) => section.rowCount > 0).length)
const panelState = computed(() => (hasAnyRows.value ? 'ready' : 'empty'))
const statusLabel = computed(() => (hasAnyRows.value ? `${filledSectionCount.value}/4 Bereiche` : 'Keine Daten'))

const rangeLabel = computed(() =>
  formatRangeLabel(
    props.attribution?.range ?? getStringMeta(props.attribution?.meta, 'range'),
    props.attribution?.range_label ?? getStringMeta(props.attribution?.meta, 'range_label')
  )
)
const asOfLabel = computed(() =>
  formatDate(props.attribution?.as_of ?? getStringMeta(props.attribution?.meta, 'as_of', 'generated_at', 'updated_at'))
)
const benchmarkLabel = computed(() =>
  formatNullableText(
    props.attribution?.benchmark_symbol ?? getStringMeta(props.attribution?.meta, 'benchmark_symbol', 'benchmark'),
    'Keine Benchmark'
  )
)
const methodologyLabel = computed(() => {
  const methodology = props.attribution?.methodology
  if (methodology?.label) {
    return methodology.label
  }
  const fallback = getStringMeta(props.attribution?.meta, 'methodology', 'return_basis')
  return fallback ? mapPortfolioMethodology(fallback) : 'Beitrag in Prozentpunkten'
})
const warningLabel = computed(() =>
  (props.attribution?.warnings ?? [])
    .filter((warning) => warning.trim().length > 0)
    .slice(0, 3)
    .map((warning) => mapPortfolioWarning(warning))
    .join(', ')
)

function formatContribution(value: number) {
  return formatSignedPercentPoints(value)
}
</script>

<style scoped>
.attribution-panel {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #ffffff;
  padding: 0.7rem 0.75rem;
  display: grid;
  gap: 0.55rem;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.eyebrow {
  margin: 0;
  color: #475569;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0;
  line-height: 1.2;
  text-transform: uppercase;
}

h3 {
  margin: 0.08rem 0 0;
  color: #0f172a;
  font-size: 1rem;
  line-height: 1.2;
}

.panel-status,
.section-count {
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #ffffff;
  color: #334155;
  font-size: 0.72rem;
  font-weight: 700;
  line-height: 1.1;
  padding: 0.16rem 0.4rem;
  white-space: nowrap;
}

.panel-status--empty {
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
}

.meta-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 0.28rem;
  color: #64748b;
  font-size: 0.74rem;
  line-height: 1.25;
}

.meta-strip span {
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #f8fafc;
  padding: 0.12rem 0.36rem;
}

.meta-strip strong {
  color: #334155;
}

.warning-line {
  margin: 0;
  color: #92400e;
  font-size: 0.76rem;
  line-height: 1.3;
}

.attribution-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.45rem;
}

.attribution-section {
  min-width: 0;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  padding: 0.45rem;
  display: grid;
  gap: 0.38rem;
}

.attribution-section--empty {
  background: #f8fafc;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem;
}

h4 {
  margin: 0;
  color: #334155;
  font-size: 0.84rem;
  line-height: 1.2;
}

.section-count {
  min-width: 1.35rem;
  padding-inline: 0.28rem;
  text-align: center;
}

.split-lists {
  display: grid;
  gap: 0.36rem;
}

.split-list {
  min-width: 0;
  display: grid;
  gap: 0.16rem;
}

.split-title {
  margin: 0;
  color: #475569;
  font-size: 0.7rem;
  font-weight: 700;
  line-height: 1.2;
  text-transform: uppercase;
}

ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.12rem;
}

li {
  min-width: 0;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.35rem;
  color: #334155;
  font-size: 0.78rem;
  line-height: 1.2;
}

.item-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-value {
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.item-value--positive {
  color: #047857;
}

.item-value--negative {
  color: #be123c;
}

.empty-copy {
  margin: 0;
  color: #94a3b8;
  font-size: 0.74rem;
  line-height: 1.25;
}

@media (max-width: 1180px) {
  .attribution-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 620px) {
  .panel-header {
    display: grid;
  }

  .attribution-grid {
    grid-template-columns: 1fr;
  }
}
</style>
