<template>
  <AnalyticsSectionCard
    title="Zeitreihe"
    :state="section.state"
    :meta-text="metaText"
    :show-refreshing-badge="section.refresh_in_progress"
    :error-message="errorMessage"
    @retry="$emit('retry')"
  >
    <div v-if="points.length > 0" class="chart-box">
      <SimpleLineChart :points="points" />
    </div>
    <EmptyState v-else>Keine Zeitreihendaten verfügbar.</EmptyState>
  </AnalyticsSectionCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AnalyticsSectionCard from '@/modules/dashboard/components/AnalyticsSectionCard.vue'
import type { DashboardSectionReadModel, DashboardTimeseriesPayload } from '@/shared/model/types'
import EmptyState from '@/shared/ui/EmptyState.vue'
import SimpleLineChart from '@/shared/ui/SimpleLineChart.vue'

const props = defineProps<{
  section: DashboardSectionReadModel<DashboardTimeseriesPayload>
  metaText: string
  errorMessage: string
}>()

defineEmits<{ (event: 'retry'): void }>()

const points = computed(() => props.section.payload?.points ?? [])
</script>

<style scoped>
.chart-box {
  min-height: 260px;
}
</style>
