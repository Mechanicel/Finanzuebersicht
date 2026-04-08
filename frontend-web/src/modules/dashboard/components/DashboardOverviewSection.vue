<template>
  <AnalyticsSectionCard
    title="Überblick"
    :state="section.state"
    :meta-text="metaText"
    :show-refreshing-badge="section.refresh_in_progress"
    :error-message="errorMessage"
    @retry="$emit('retry')"
  >
    <div v-if="kpis.length > 0" class="kpis">
      <div class="card kpi-card" v-for="(kpi, index) in kpis" :key="`${kpi.label}-${index}`">
        <strong>{{ kpi.label }}</strong>
        <div>{{ kpi.value }}</div>
      </div>
    </div>
    <EmptyState v-else>Keine Überblicksdaten verfügbar.</EmptyState>
  </AnalyticsSectionCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { DashboardOverviewPayload, DashboardSectionReadModel } from '@/shared/model/types'
import EmptyState from '@/shared/ui/EmptyState.vue'
import AnalyticsSectionCard from '@/modules/dashboard/components/AnalyticsSectionCard.vue'

const props = defineProps<{
  section: DashboardSectionReadModel<DashboardOverviewPayload>
  metaText: string
  errorMessage: string
}>()

defineEmits<{ (event: 'retry'): void }>()

const kpis = computed(() => props.section.payload?.kpis ?? [])
</script>

<style scoped>
.kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 0.75rem;
}

.kpi-card {
  padding: 0.7rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}
</style>
