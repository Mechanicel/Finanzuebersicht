<template>
  <!-- Legacy analytics stay available intentionally, but portfolio cockpit is the primary flow. -->
  <details class="legacy-sections">
    <summary class="legacy-header">
      <span>
        <strong>{{ title }}</strong>
        <small>{{ subtitle }}</small>
      </span>
    </summary>
    <p v-if="description" class="legacy-note">{{ description }}</p>
    <slot />
  </details>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title?: string
    subtitle?: string
    description?: string
  }>(),
  {
    title: 'Weitere Analytics (Legacy)',
    subtitle: 'Optional · sekundärer Bereich',
    description: 'Bestehende Auswertungen bleiben verfügbar, sind aber nicht mehr der primäre Cockpit-Fokus.'
  }
)
</script>

<style scoped>
.legacy-sections {
  display: grid;
  gap: 0.85rem;
  border-top: 1px dashed #cbd5e1;
  padding-top: 1rem;
  opacity: 0.92;
}

.legacy-header {
  cursor: pointer;
  list-style: none;
}

.legacy-header::-webkit-details-marker {
  display: none;
}

.legacy-header span {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.legacy-header small {
  color: #64748b;
  font-size: 0.78rem;
}

.legacy-note {
  margin: 0;
  color: #64748b;
  font-size: 0.88rem;
}
</style>
