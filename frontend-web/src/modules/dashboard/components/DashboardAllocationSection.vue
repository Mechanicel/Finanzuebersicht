<template>
  <AnalyticsSectionCard
    title="Allokation"
    :state="section.state"
    :meta-text="metaText"
    :show-refreshing-badge="section.refresh_in_progress"
    :error-message="errorMessage"
    @retry="$emit('retry')"
  >
    <div v-if="hasData" class="chart-box">
      <SimplePieChart :labels="labels" :values="values" />
    </div>
    <EmptyState v-else>Keine Allokationsdaten verfügbar.</EmptyState>
  </AnalyticsSectionCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AnalyticsSectionCard from '@/modules/dashboard/components/AnalyticsSectionCard.vue'
import type { DashboardAllocationPayload, DashboardSectionReadModel } from '@/shared/model/types'
import EmptyState from '@/shared/ui/EmptyState.vue'
import SimplePieChart from '@/shared/ui/SimplePieChart.vue'

const props = defineProps<{
  section: DashboardSectionReadModel<DashboardAllocationPayload>
  metaText: string
  errorMessage: string
}>()

defineEmits<{ (event: 'retry'): void }>()

const labels = computed(() => props.section.payload?.labels ?? [])
const values = computed(() => props.section.payload?.values ?? [])
const hasData = computed(() => labels.value.length > 0 && values.value.length > 0)
</script>

<style scoped>
.chart-box {
  min-height: 240px;
}
</style>
