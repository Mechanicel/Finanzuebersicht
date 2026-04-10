<template>
  <section class="coverage" :class="{ warning: hasCoverageGap }">
    <p class="title"><strong>Datenabdeckung</strong> für {{ coverage.total_holdings }} Holdings</p>
    <div class="stats">
      <span>Preise fehlen: {{ coverage.missing_prices }}</span>
      <span>Sektoren fehlen: {{ coverage.missing_sectors }}</span>
      <span>Länder fehlen: {{ coverage.missing_countries }}</span>
      <span>Währungen fehlen: {{ coverage.missing_currencies }}</span>
      <span>Preis-Fallbacks: {{ coverage.fallback_acquisition_prices ?? 0 }}</span>
      <span>Marketdata-Warnungen: {{ coverage.holdings_with_marketdata_warnings ?? 0 }}</span>
    </div>
    <p v-if="coverage.warnings.length > 0" class="warnings">Hinweise: {{ compactWarnings }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PortfolioDataCoverageReadModel } from '@/shared/model/types'
import { mapCoverageWarning } from '@/modules/dashboard/model/portfolioFormatting'

const props = defineProps<{
  coverage: PortfolioDataCoverageReadModel
}>()

const hasCoverageGap = computed(
  () =>
    props.coverage.missing_prices > 0 ||
    props.coverage.missing_sectors > 0 ||
    props.coverage.missing_countries > 0 ||
    props.coverage.missing_currencies > 0 ||
    (props.coverage.fallback_acquisition_prices ?? 0) > 0 ||
    (props.coverage.holdings_with_marketdata_warnings ?? 0) > 0
)

const compactWarnings = computed(() =>
  props.coverage.warnings.slice(0, 6).map((warning) => mapCoverageWarning(warning)).join(', ')
)
</script>

<style scoped>
.coverage {
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  border-radius: 10px;
  padding: 0.75rem 0.9rem;
}

.coverage.warning {
  border-color: #f59e0b;
  background: #fffbeb;
}

p {
  margin: 0;
  color: #334155;
  font-size: 0.88rem;
}

.title {
  margin-bottom: 0.35rem;
}

.stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.6rem;
  color: #475569;
  font-size: 0.82rem;
}

.warnings {
  margin-top: 0.35rem;
  color: #92400e;
}
</style>
