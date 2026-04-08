<template>
  <article class="card section-card">
    <header class="section-head">
      <div>
        <h3>{{ title }}</h3>
        <p v-if="metaText" class="meta-text">{{ metaText }}</p>
      </div>
      <span v-if="showRefreshingBadge" class="refresh-badge">Cache wird aktualisiert</span>
    </header>

    <div v-if="state === 'pending'" class="pending-wrap">
      <slot name="pending">
        <LoadingState />
      </slot>
    </div>

    <div v-else-if="state === 'error'" class="error-wrap">
      <ErrorState :message="errorMessage ?? 'Die Section konnte nicht geladen werden.'" />
      <button class="btn flow-btn retry-btn" type="button" @click="$emit('retry')">Erneut laden</button>
    </div>

    <div v-else>
      <slot />
      <p v-if="state === 'stale'" class="stale-note">Es werden Cache-Daten angezeigt, die im Hintergrund erneuert werden.</p>
    </div>
  </article>
</template>

<script setup lang="ts">
import LoadingState from '@/shared/ui/LoadingState.vue'
import ErrorState from '@/shared/ui/ErrorState.vue'
import type { DashboardSectionState } from '@/shared/model/types'

defineProps<{
  title: string
  state: DashboardSectionState
  metaText?: string
  showRefreshingBadge?: boolean
  errorMessage?: string
}>()

defineEmits<{ (event: 'retry'): void }>()
</script>

<style scoped>
.section-card h3 {
  margin: 0;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: flex-start;
  margin-bottom: 0.65rem;
}

.meta-text {
  margin: 0.25rem 0 0;
  color: #475569;
  font-size: 0.85rem;
}

.refresh-badge {
  font-size: 0.75rem;
  color: #1d4ed8;
  background: #dbeafe;
  border-radius: 999px;
  padding: 0.2rem 0.55rem;
  white-space: nowrap;
}

.stale-note {
  margin: 0.75rem 0 0;
  color: #1d4ed8;
  font-size: 0.85rem;
}

.retry-btn {
  border: 1px solid #cbd5e1;
}

.error-wrap,
.pending-wrap {
  display: grid;
  gap: 0.75rem;
  justify-items: start;
}
</style>
