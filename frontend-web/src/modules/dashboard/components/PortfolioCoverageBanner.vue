<template>
  <section class="coverage" :class="{ warning: hasCoverageGap }">
    <p class="title"><strong>Datenabdeckung</strong> für {{ coverage.total_holdings ?? 0 }} Holdings</p>
    <p class="meta"><strong>Snapshot</strong> · Stand: {{ asOfLabel }}</p>
    <p class="stats-line">
      Preise fehlen: {{ coverage.missing_prices ?? 0 }} ·
      Sektoren fehlen: {{ coverage.missing_sectors ?? 0 }} ·
      Länder fehlen: {{ coverage.missing_countries ?? 0 }} ·
      Währungen fehlen: {{ coverage.missing_currencies ?? 0 }} ·
      Preis-Fallbacks: {{ coverage.fallback_acquisition_prices ?? 0 }} ·
      Marketdata-Warnungen: {{ coverage.holdings_with_marketdata_warnings ?? 0 }}
    </p>
    <p v-if="hasWarnings" class="warnings">Hinweise: {{ compactWarnings }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PortfolioDataCoverageReadModel } from '@/shared/model/types'
import { formatDate, getStringMeta, mapCoverageWarning } from '@/modules/dashboard/model/portfolioFormatting'

const props = defineProps<{
  coverage: PortfolioDataCoverageReadModel
}>()

const asOfLabel = computed(() => formatDate(getStringMeta(props.coverage.meta, 'as_of', 'generated_at', 'updated_at') ?? props.coverage.as_of))

const hasCoverageGap = computed(
  () =>
    (props.coverage.missing_prices ?? 0) > 0 ||
    (props.coverage.missing_sectors ?? 0) > 0 ||
    (props.coverage.missing_countries ?? 0) > 0 ||
    (props.coverage.missing_currencies ?? 0) > 0 ||
    (props.coverage.fallback_acquisition_prices ?? 0) > 0 ||
    (props.coverage.holdings_with_marketdata_warnings ?? 0) > 0
)

const hasWarnings = computed(() => (props.coverage.warnings ?? []).length > 0)

const compactWarnings = computed(() =>
  (props.coverage.warnings ?? []).slice(0, 6).map((warning) => mapCoverageWarning(warning)).join(', ')
)
</script>

<style scoped>
.coverage {
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  border-radius: 10px;
  padding: 0.45rem 0.65rem;
  display: grid;
  gap: 0.2rem;
}

.coverage.warning {
  border-color: #f59e0b;
  background: #fffbeb;
}

p {
  margin: 0;
  color: #334155;
  font-size: 0.82rem;
}

.title {
  font-size: 0.84rem;
}

.stats-line {
  color: #475569;
  font-size: 0.78rem;
  line-height: 1.3;
}

.meta {
  color: #64748b;
  font-size: 0.76rem;
}

.warnings {
  color: #92400e;
  font-size: 0.76rem;
}
</style>
