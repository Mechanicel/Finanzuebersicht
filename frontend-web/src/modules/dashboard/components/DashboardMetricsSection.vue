<template>
  <AnalyticsSectionCard
    title="Kennzahlen"
    :state="section.state"
    :meta-text="metaText"
    :show-refreshing-badge="section.refresh_in_progress"
    :error-message="errorMessage"
    @retry="$emit('retry')"
  >
    <pre class="metrics-preview">{{ prettyMetrics }}</pre>
  </AnalyticsSectionCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AnalyticsSectionCard from '@/modules/dashboard/components/AnalyticsSectionCard.vue'
import type { DashboardMetricsPayload, DashboardSectionReadModel } from '@/shared/model/types'

const props = defineProps<{
  section: DashboardSectionReadModel<DashboardMetricsPayload>
  metaText: string
  errorMessage: string
}>()

defineEmits<{ (event: 'retry'): void }>()

const prettyMetrics = computed(() => JSON.stringify(props.section.payload ?? {}, null, 2))
</script>

<style scoped>
.metrics-preview {
  margin: 0;
  max-height: 260px;
  overflow: auto;
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 10px;
  padding: 0.75rem;
}
</style>
