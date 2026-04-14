<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <header class="modal-header">
        <h2 id="modal-title">Benchmark konfigurieren</h2>
        <button class="close-btn" aria-label="Schließen" @click="$emit('close')">✕</button>
      </header>

      <nav class="tab-nav" role="tablist">
        <button
          role="tab"
          :aria-selected="activeTab === 'suggest'"
          :class="{ active: activeTab === 'suggest' }"
          @click="activeTab = 'suggest'"
        >
          Auto-Vorschlag
        </button>
        <button
          role="tab"
          :aria-selected="activeTab === 'custom'"
          :class="{ active: activeTab === 'custom' }"
          @click="activeTab = 'custom'"
        >
          Eigener Benchmark
        </button>
      </nav>

      <!-- ── Auto-Suggest Tab ─────────────────────────────────────── -->
      <section v-if="activeTab === 'suggest'" class="tab-panel">
        <p class="hint">
          Automatisch ermittelter Benchmark basierend auf den Länder-Expositionen des Portfolios.
        </p>

        <div v-if="suggestLoading" class="loading-hint">Vorschlag wird berechnet…</div>
        <div v-else-if="suggestError" class="error-hint">{{ suggestError }}</div>
        <template v-else-if="suggestion">
          <p class="reasoning">{{ suggestion.reasoning }}</p>

          <table class="component-table">
            <thead>
              <tr>
                <th>ETF</th>
                <th>Name</th>
                <th class="align-right">Gewicht</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="comp in suggestion.components" :key="comp.ticker">
                <td><code>{{ comp.ticker }}</code></td>
                <td>{{ comp.name ?? '—' }}</td>
                <td class="align-right">{{ comp.weight.toFixed(1) }}%</td>
              </tr>
            </tbody>
          </table>

          <div class="action-row">
            <button class="btn btn-primary" :disabled="saving" @click="applyAndSave(suggestion.components)">
              {{ saving ? 'Wird gespeichert…' : 'Vorschlag übernehmen' }}
            </button>
          </div>
        </template>
      </section>

      <!-- ── Custom Tab ───────────────────────────────────────────── -->
      <section v-if="activeTab === 'custom'" class="tab-panel">
        <p class="hint">
          Wähle bis zu 5 ETF-Ticker und gib Gewichte ein (Summe muss 100 % ergeben).
        </p>

        <div class="component-editor">
          <div
            v-for="(comp, idx) in editComponents"
            :key="idx"
            class="component-row"
          >
            <input
              v-model="comp.ticker"
              class="input-ticker"
              placeholder="Ticker (z. B. IWDA.L)"
              maxlength="20"
              @input="comp.ticker = comp.ticker.toUpperCase()"
            />
            <input
              v-model="comp.name"
              class="input-name"
              placeholder="Name (optional)"
              maxlength="100"
            />
            <input
              v-model.number="comp.weight"
              class="input-weight"
              type="number"
              min="0.1"
              max="100"
              step="0.1"
              placeholder="%"
            />
            <button class="btn-remove" title="Entfernen" @click="removeComponent(idx)">✕</button>
          </div>
        </div>

        <button
          v-if="editComponents.length < 5"
          class="btn btn-secondary btn-add"
          @click="addComponent"
        >
          + Komponente hinzufügen
        </button>

        <div class="weight-summary" :class="{ error: weightError }">
          Summe: <strong>{{ totalWeight.toFixed(1) }}%</strong>
          <span v-if="weightError" class="weight-error-msg"> — muss 100% ergeben</span>
        </div>

        <div v-if="saveError" class="error-hint">{{ saveError }}</div>

        <div class="action-row">
          <button
            class="btn btn-secondary"
            @click="resetToDefault"
          >
            Standard (SPY)
          </button>
          <button
            class="btn btn-primary"
            :disabled="!canSave || saving"
            @click="saveCustom"
          >
            {{ saving ? 'Wird gespeichert…' : 'Speichern' }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { BenchmarkComponent } from '@/shared/model/types'
import { fetchBenchmarkConfig, fetchBenchmarkSuggestion, saveBenchmarkConfig } from '../api/portfolioDashboardApi'

const props = defineProps<{ personId: string }>()
const emit = defineEmits<{ (e: 'close'): void; (e: 'saved'): void }>()

const activeTab = ref<'suggest' | 'custom'>('suggest')

// ── Suggest tab state ─────────────────────────────────────────────────────
const suggestion = ref<{ components: BenchmarkComponent[]; reasoning: string } | null>(null)
const suggestLoading = ref(false)
const suggestError = ref<string | null>(null)

async function loadSuggestion() {
  suggestLoading.value = true
  suggestError.value = null
  try {
    suggestion.value = await fetchBenchmarkSuggestion(props.personId)
  } catch {
    suggestError.value = 'Vorschlag konnte nicht geladen werden.'
  } finally {
    suggestLoading.value = false
  }
}

// ── Custom tab state ──────────────────────────────────────────────────────
interface EditComponent {
  ticker: string
  name: string
  weight: number
}

const editComponents = ref<EditComponent[]>([{ ticker: '', name: '', weight: 100 }])
const saving = ref(false)
const saveError = ref<string | null>(null)

const totalWeight = computed(() => editComponents.value.reduce((sum, c) => sum + (c.weight || 0), 0))
const weightError = computed(() => editComponents.value.length > 0 && Math.abs(totalWeight.value - 100) > 0.05)
const canSave = computed(
  () => editComponents.value.length > 0
    && editComponents.value.every(c => c.ticker.trim().length > 0 && c.weight > 0)
    && !weightError.value
)

function addComponent() {
  editComponents.value.push({ ticker: '', name: '', weight: 0 })
}

function removeComponent(idx: number) {
  editComponents.value.splice(idx, 1)
}

function resetToDefault() {
  editComponents.value = []
  saveError.value = null
}

async function loadExistingConfig() {
  try {
    const config = await fetchBenchmarkConfig(props.personId)
    if (config.components.length > 0) {
      editComponents.value = config.components.map(c => ({
        ticker: c.ticker,
        name: c.name ?? '',
        weight: c.weight,
      }))
    }
  } catch {
    // Ignore — use default empty state
  }
}

async function saveCustom() {
  if (!canSave.value) return
  saving.value = true
  saveError.value = null
  try {
    await saveBenchmarkConfig(props.personId, {
      components: editComponents.value.map(c => ({
        ticker: c.ticker.trim().toUpperCase(),
        name: c.name.trim() || null,
        weight: c.weight,
      })),
    })
    emit('saved')
    emit('close')
  } catch (err: unknown) {
    saveError.value = err instanceof Error ? err.message : 'Speichern fehlgeschlagen.'
  } finally {
    saving.value = false
  }
}

async function applyAndSave(components: BenchmarkComponent[]) {
  saving.value = true
  try {
    await saveBenchmarkConfig(props.personId, { components })
    emit('saved')
    emit('close')
  } catch {
    suggestError.value = 'Speichern fehlgeschlagen.'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadSuggestion(), loadExistingConfig()])
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--color-surface, #fff);
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  width: min(560px, 95vw);
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
}

.modal-header h2 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0.25rem;
  color: var(--color-text-muted, #6b7280);
}

.tab-nav {
  display: flex;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
}

.tab-nav button {
  flex: 1;
  background: none;
  border: none;
  padding: 0.75rem 1rem;
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--color-text-muted, #6b7280);
  border-bottom: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}

.tab-nav button.active {
  color: var(--color-accent, #2563eb);
  border-bottom-color: var(--color-accent, #2563eb);
  font-weight: 600;
}

.tab-panel {
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.hint {
  font-size: 0.8125rem;
  color: var(--color-text-muted, #6b7280);
  margin: 0;
}

.reasoning {
  font-size: 0.8125rem;
  color: var(--color-text, #374151);
  margin: 0;
  font-style: italic;
}

.loading-hint,
.error-hint {
  font-size: 0.875rem;
  padding: 0.5rem 0;
}

.error-hint { color: var(--color-danger, #dc2626); }

.component-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.component-table th,
.component-table td {
  padding: 0.375rem 0.5rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
}

.component-table th {
  font-weight: 600;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6b7280);
  text-transform: uppercase;
}

.align-right { text-align: right; }

.component-editor {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.component-row {
  display: grid;
  grid-template-columns: 110px 1fr 70px 28px;
  gap: 0.375rem;
  align-items: center;
}

.component-row input {
  padding: 0.35rem 0.5rem;
  border: 1px solid var(--color-border, #d1d5db);
  border-radius: 4px;
  font-size: 0.8125rem;
  background: var(--color-surface, #fff);
  color: var(--color-text, #111827);
  width: 100%;
}

.input-weight { text-align: right; }

.btn-remove {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted, #9ca3af);
  font-size: 0.875rem;
  padding: 0;
  line-height: 1;
}

.btn-remove:hover { color: var(--color-danger, #dc2626); }

.btn-add {
  align-self: flex-start;
}

.weight-summary {
  font-size: 0.8125rem;
  color: var(--color-text-muted, #6b7280);
}

.weight-summary.error { color: var(--color-danger, #dc2626); }
.weight-error-msg { font-size: 0.8125rem; }

.action-row {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 0.25rem;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: opacity 0.15s;
}

.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-primary {
  background: var(--color-accent, #2563eb);
  color: #fff;
}

.btn-primary:hover:not(:disabled) { opacity: 0.9; }

.btn-secondary {
  background: var(--color-surface-raised, #f3f4f6);
  color: var(--color-text, #374151);
  border: 1px solid var(--color-border, #d1d5db);
}

.btn-secondary:hover:not(:disabled) { background: var(--color-surface-hover, #e5e7eb); }
</style>
