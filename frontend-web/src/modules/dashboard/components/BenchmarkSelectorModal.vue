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
          Suche nach ETFs oder Indizes und gib Gewichte ein (Summe muss 100&nbsp;% ergeben, max. 5 Komponenten).
        </p>

        <!-- Search input + dropdown -->
        <div v-if="editComponents.length < 5" class="search-block" ref="searchBlockRef">
          <div class="search-input-wrap">
            <input
              ref="searchInputRef"
              v-model.trim="searchQuery"
              class="input search-input"
              placeholder="ETF / Index suchen (z. B. MSCI World, DAX, S&P 500)"
              autocomplete="off"
              @input="onSearchInput"
              @keydown.escape="closeDropdown"
              @keydown.arrow-down.prevent="moveDropdownFocus(1)"
              @keydown.arrow-up.prevent="moveDropdownFocus(-1)"
              @keydown.enter.prevent="selectFocusedResult"
            />
            <span v-if="searching" class="search-spinner" aria-hidden="true">⏳</span>
          </div>

          <p v-if="searchHint" class="search-hint">{{ searchHint }}</p>

          <ul
            v-if="showDropdown"
            class="search-dropdown"
            role="listbox"
            aria-label="Suchergebnisse"
          >
            <li v-if="searchError" class="dropdown-item dropdown-item--error">
              {{ searchError }}
            </li>
            <li v-else-if="searchResults.length === 0 && !searching" class="dropdown-item dropdown-item--empty">
              Keine Treffer gefunden.
            </li>
            <li
              v-for="(item, idx) in searchResults"
              :key="item.symbol"
              class="dropdown-item"
              :class="{ 'dropdown-item--focused': dropdownFocusIndex === idx }"
              role="option"
              :aria-selected="dropdownFocusIndex === idx"
              @click="selectResult(item)"
              @mouseenter="dropdownFocusIndex = idx"
            >
              <div class="result-row">
                <strong class="result-symbol">{{ item.symbol }}</strong>
                <span class="result-name">{{ item.display_name || item.company_name || '' }}</span>
              </div>
              <div class="result-meta">
                <small v-if="item.currency">{{ item.currency }}</small>
                <small v-if="item.exchange">{{ item.exchange }}</small>
                <small v-if="item.exchange_full_name" class="result-exchange-full">{{ item.exchange_full_name }}</small>
              </div>
            </li>
          </ul>
        </div>

        <!-- Added components list -->
        <div v-if="editComponents.length > 0" class="component-list">
          <div
            v-for="(comp, idx) in editComponents"
            :key="idx"
            class="component-entry"
          >
            <div class="component-entry-info">
              <span class="ticker-badge">{{ comp.ticker }}</span>
              <span class="component-name">{{ comp.name || comp.ticker }}</span>
            </div>
            <div class="component-entry-controls">
              <div class="weight-input-wrap">
                <input
                  v-model.number="comp.weight"
                  class="input weight-input"
                  type="number"
                  min="0.1"
                  max="100"
                  step="0.1"
                  :placeholder="'%'"
                  aria-label="`Gewicht für ${comp.ticker}`"
                />
                <span class="weight-unit">%</span>
              </div>
              <button class="btn-remove" title="Entfernen" @click="removeComponent(idx)">✕</button>
            </div>
          </div>
        </div>

        <p v-else class="empty-components-hint">
          Suche nach einem ETF oder Index, um ihn als Benchmark-Komponente hinzuzufügen.
        </p>

        <!-- Weight summary -->
        <div v-if="editComponents.length > 0" class="weight-summary" :class="{ error: weightError }">
          <span>Summe: <strong>{{ totalWeight.toFixed(1) }}%</strong></span>
          <span v-if="weightError" class="weight-error-msg">— muss 100% ergeben</span>
          <span v-else-if="totalWeight === 100" class="weight-ok-msg">✓</span>
        </div>

        <div v-if="saveError" class="error-hint">{{ saveError }}</div>

        <div class="action-row">
          <button
            v-if="editComponents.length > 0"
            class="btn btn-secondary"
            @click="resetComponents"
          >
            Zurücksetzen
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
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import type { BenchmarkComponent, InstrumentSearchItem } from '@/shared/model/types'
import { searchInstruments } from '@/modules/portfolio/api/portfolioApi'
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

// ── Search state ──────────────────────────────────────────────────────────
const MIN_SEARCH_LENGTH = 2
const SEARCH_DEBOUNCE_MS = 400

const searchInputRef = ref<HTMLInputElement | null>(null)
const searchBlockRef = ref<HTMLElement | null>(null)
const searchQuery = ref('')
const searching = ref(false)
const searchResults = ref<InstrumentSearchItem[]>([])
const searchError = ref<string | null>(null)
const showDropdown = ref(false)
const dropdownFocusIndex = ref(-1)

let searchDebounceHandle: ReturnType<typeof setTimeout> | null = null
let activeSearchRequestId = 0

const searchHint = computed(() => {
  if (searchQuery.value.length === 0) return null
  if (searchQuery.value.length < MIN_SEARCH_LENGTH) {
    return `Mindestens ${MIN_SEARCH_LENGTH} Zeichen eingeben…`
  }
  return null
})

function onSearchInput() {
  searchError.value = null
  dropdownFocusIndex.value = -1

  if (searchDebounceHandle) clearTimeout(searchDebounceHandle)

  if (searchQuery.value.length < MIN_SEARCH_LENGTH) {
    showDropdown.value = false
    searchResults.value = []
    return
  }

  const requestId = ++activeSearchRequestId
  searchDebounceHandle = setTimeout(() => {
    void runSearch(requestId)
  }, SEARCH_DEBOUNCE_MS)
}

async function runSearch(requestId: number) {
  if (searchQuery.value.length < MIN_SEARCH_LENGTH) return
  searching.value = true
  showDropdown.value = true
  try {
    const result = await searchInstruments(searchQuery.value, 10)
    if (requestId !== activeSearchRequestId) return  // Stale response
    searchResults.value = result.items
    searchError.value = null
  } catch {
    if (requestId !== activeSearchRequestId) return
    searchError.value = 'Suche fehlgeschlagen. Bitte erneut versuchen.'
    searchResults.value = []
  } finally {
    if (requestId === activeSearchRequestId) {
      searching.value = false
    }
  }
}

function closeDropdown() {
  showDropdown.value = false
  dropdownFocusIndex.value = -1
}

function moveDropdownFocus(delta: number) {
  if (!showDropdown.value || searchResults.value.length === 0) return
  const next = dropdownFocusIndex.value + delta
  dropdownFocusIndex.value = Math.max(0, Math.min(searchResults.value.length - 1, next))
}

function selectFocusedResult() {
  if (dropdownFocusIndex.value >= 0 && dropdownFocusIndex.value < searchResults.value.length) {
    selectResult(searchResults.value[dropdownFocusIndex.value])
  }
}

function selectResult(item: InstrumentSearchItem) {
  // Avoid duplicates
  if (editComponents.value.some(c => c.ticker === item.symbol)) {
    closeDropdown()
    searchQuery.value = ''
    return
  }
  editComponents.value.push({
    ticker: item.symbol,
    name: item.display_name || item.company_name || item.symbol,
    weight: editComponents.value.length === 0 ? 100 : 0,
  })
  searchQuery.value = ''
  searchResults.value = []
  closeDropdown()
  if (searchDebounceHandle) clearTimeout(searchDebounceHandle)
}

// Close dropdown when clicking outside
function onDocumentClick(event: MouseEvent) {
  if (searchBlockRef.value && !searchBlockRef.value.contains(event.target as Node)) {
    closeDropdown()
  }
}

// ── Custom component list state ───────────────────────────────────────────
interface EditComponent {
  ticker: string
  name: string
  weight: number
}

const editComponents = ref<EditComponent[]>([])
const saving = ref(false)
const saveError = ref<string | null>(null)

const totalWeight = computed(() =>
  editComponents.value.reduce((sum, c) => sum + (Number(c.weight) || 0), 0)
)
const weightError = computed(() =>
  editComponents.value.length > 0 && Math.abs(totalWeight.value - 100) > 0.05
)
const canSave = computed(
  () =>
    editComponents.value.length > 0 &&
    editComponents.value.every(c => c.ticker.trim().length > 0 && Number(c.weight) > 0) &&
    !weightError.value
)

function removeComponent(idx: number) {
  editComponents.value.splice(idx, 1)
}

function resetComponents() {
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
      // If there's already a custom config, start on the custom tab
      activeTab.value = 'custom'
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
        weight: Number(c.weight),
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
  document.addEventListener('click', onDocumentClick, true)
  await Promise.all([loadSuggestion(), loadExistingConfig()])
  await nextTick()
  if (activeTab.value === 'custom') {
    searchInputRef.value?.focus()
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick, true)
  if (searchDebounceHandle) clearTimeout(searchDebounceHandle)
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
  width: min(540px, 95vw);
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
  position: sticky;
  top: 0;
  background: var(--color-surface, #fff);
  z-index: 1;
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
  gap: 0.875rem;
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
  padding: 0.25rem 0;
}

.error-hint { color: var(--color-danger, #dc2626); }

/* ── Suggest table ── */
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

/* ── Search block ── */
.search-block {
  position: relative;
}

.search-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input {
  width: 100%;
  padding: 0.5rem 2rem 0.5rem 0.625rem;
  border: 1px solid var(--color-border, #d1d5db);
  border-radius: 6px;
  font-size: 0.875rem;
  background: var(--color-surface, #fff);
  color: var(--color-text, #111827);
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.search-input:focus {
  border-color: var(--color-accent, #2563eb);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}

.search-spinner {
  position: absolute;
  right: 0.5rem;
  font-size: 0.875rem;
  animation: spin 1s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.search-hint {
  font-size: 0.75rem;
  color: var(--color-text-muted, #9ca3af);
  margin: 0.25rem 0 0;
}

/* ── Dropdown ── */
.search-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #d1d5db);
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  list-style: none;
  margin: 0;
  padding: 0.25rem 0;
  max-height: 240px;
  overflow-y: auto;
  z-index: 100;
}

.dropdown-item {
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  transition: background 0.1s;
}

.dropdown-item:hover,
.dropdown-item--focused {
  background: var(--color-surface-hover, #f3f4f6);
}

.dropdown-item--error,
.dropdown-item--empty {
  cursor: default;
  color: var(--color-text-muted, #6b7280);
  font-size: 0.875rem;
}

.dropdown-item--error { color: var(--color-danger, #dc2626); }

.result-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.result-symbol {
  font-family: monospace;
  font-size: 0.8125rem;
  color: var(--color-accent, #2563eb);
  flex-shrink: 0;
}

.result-name {
  font-size: 0.8125rem;
  color: var(--color-text, #374151);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-meta {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.125rem;
}

.result-meta small {
  font-size: 0.7rem;
  color: var(--color-text-muted, #9ca3af);
  background: var(--color-surface-raised, #f3f4f6);
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
}

.result-exchange-full { display: none; }

/* ── Component list ── */
.component-list {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.component-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.625rem;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 6px;
  background: var(--color-surface-raised, #f9fafb);
}

.component-entry-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
  flex: 1;
}

.ticker-badge {
  font-family: monospace;
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--color-accent, #2563eb);
  background: rgba(37, 99, 235, 0.08);
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  flex-shrink: 0;
}

.component-name {
  font-size: 0.8125rem;
  color: var(--color-text-muted, #6b7280);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.component-entry-controls {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  flex-shrink: 0;
}

.weight-input-wrap {
  display: flex;
  align-items: center;
  gap: 0.2rem;
}

.weight-input {
  width: 64px;
  padding: 0.3rem 0.4rem;
  border: 1px solid var(--color-border, #d1d5db);
  border-radius: 4px;
  font-size: 0.8125rem;
  text-align: right;
  background: var(--color-surface, #fff);
  color: var(--color-text, #111827);
}

.weight-unit {
  font-size: 0.8125rem;
  color: var(--color-text-muted, #6b7280);
}

.btn-remove {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted, #9ca3af);
  font-size: 0.875rem;
  padding: 0.15rem 0.25rem;
  line-height: 1;
  border-radius: 3px;
  transition: color 0.1s, background 0.1s;
}

.btn-remove:hover {
  color: var(--color-danger, #dc2626);
  background: rgba(220, 38, 38, 0.08);
}

.empty-components-hint {
  font-size: 0.8125rem;
  color: var(--color-text-muted, #9ca3af);
  text-align: center;
  margin: 0.25rem 0;
  font-style: italic;
}

/* ── Weight summary ── */
.weight-summary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
  color: var(--color-text-muted, #6b7280);
}

.weight-summary.error { color: var(--color-danger, #dc2626); }

.weight-error-msg { font-size: 0.8125rem; }
.weight-ok-msg { color: #16a34a; }

/* ── Actions ── */
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
