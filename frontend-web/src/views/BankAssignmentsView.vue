<template>
  <section class="card">
    <h2>Bankzuordnung</h2>
    <p v-if="!personId" class="context-hint">
      Diese Ansicht ist ein Schritt im Personen-Hub. Bitte wähle zuerst eine Person aus.
    </p>
    <div v-if="!personId" class="back-links">
      <RouterLink class="btn secondary" to="/persons/select">Zur Personenliste</RouterLink>
      <RouterLink class="btn secondary" to="/">Zur Startseite</RouterLink>
    </div>

    <template v-else>
      <div class="back-links">
        <RouterLink class="btn secondary" :to="`/persons/${personId}`">Zurück zum Personen-Hub</RouterLink>
        <RouterLink class="btn secondary" to="/persons/select">Zur Personenliste</RouterLink>
      </div>

      <LoadingState v-if="loading" />
      <ErrorState v-else-if="errorMessage" :message="errorMessage" />

      <template v-else>
        <p v-if="feedbackMessage" :class="feedbackType">{{ feedbackMessage }}</p>

        <article class="assignment-card">
          <h3>Neue Bank zuordnen</h3>
          <p v-if="banks.length === 0" class="empty">Es sind noch keine Banken angelegt.</p>
          <p v-else-if="availableBanks.length === 0" class="empty">
            Alle verfügbaren Banken sind dieser Person bereits zugeordnet.
          </p>
          <div v-else class="grid assign-grid">
            <div>
              <label for="bank-select">Bank auswählen</label>
              <select id="bank-select" class="input" v-model="selectedBankId">
                <option value="">Bitte auswählen</option>
                <option v-for="bank in availableBanks" :key="bank.bank_id" :value="bank.bank_id">
                  {{ bank.name }} ({{ bank.bic }})
                </option>
              </select>
            </div>
            <button class="btn" @click="assign" :disabled="submitting || !selectedBankId">Zuordnen</button>
          </div>
        </article>

        <article class="assignment-card">
          <h3>Bereits zugeordnete Banken</h3>
          <EmptyState v-if="assignments.length === 0">Noch keine Bankzuordnungen vorhanden.</EmptyState>
          <ul v-else class="assignment-list">
            <li v-for="assignment in assignments" :key="assignment.bank_id">
              <div>
                <strong>{{ bankName(assignment.bank_id) }}</strong>
                <p class="muted">Bank-ID: {{ assignment.bank_id }}</p>
              </div>
              <button class="btn danger" @click="unassign(assignment.bank_id)" :disabled="submitting">
                Entfernen
              </button>
            </li>
          </ul>
        </article>
      </template>
    </template>
  </section>
</template>
<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient } from '../api/client'
import type { BankReadModel, PersonBankAssignmentReadModel } from '../types/models'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import LoadingState from '../components/LoadingState.vue'

const route = useRoute()
const personId = computed(() => (typeof route.query.personId === 'string' ? route.query.personId : ''))

const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref<string | null>(null)
const feedbackMessage = ref('')
const feedbackType = ref<'success' | 'error'>('success')
const assignments = ref<PersonBankAssignmentReadModel[]>([])
const banks = ref<BankReadModel[]>([])
const selectedBankId = ref('')

const assignedBankIds = computed(() => new Set(assignments.value.map((item) => item.bank_id)))
const availableBanks = computed(() => banks.value.filter((bank) => !assignedBankIds.value.has(bank.bank_id)))

function showFeedback(type: 'success' | 'error', message: string) {
  feedbackType.value = type
  feedbackMessage.value = message
}

function bankName(bankId: string) {
  return banks.value.find((bank) => bank.bank_id === bankId)?.name ?? `Unbekannte Bank (${bankId})`
}

async function loadData() {
  if (!personId.value) {
    return
  }
  loading.value = true
  errorMessage.value = null
  feedbackMessage.value = ''
  try {
    const [assignmentResult, bankResult] = await Promise.all([
      apiClient.personBanks(personId.value),
      apiClient.banks()
    ])
    assignments.value = assignmentResult.items
    banks.value = bankResult.items
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : 'Fehler beim Laden der Bankzuordnung.'
  } finally {
    loading.value = false
  }
}

async function assign() {
  if (!personId.value || !selectedBankId.value) {
    return
  }

  submitting.value = true
  try {
    await apiClient.assignBank(personId.value, selectedBankId.value)
    selectedBankId.value = ''
    showFeedback('success', 'Bank wurde zugeordnet.')
    await loadData()
  } catch (e) {
    if (axios.isAxiosError(e) && e.response?.status === 409) {
      showFeedback('error', 'Diese Bank ist bereits zugeordnet.')
      return
    }
    showFeedback('error', e instanceof Error ? e.message : 'Bank konnte nicht zugeordnet werden.')
  } finally {
    submitting.value = false
  }
}

async function unassign(bankId: string) {
  if (!personId.value) {
    return
  }
  submitting.value = true
  try {
    await apiClient.unassignBank(personId.value, bankId)
    showFeedback('success', 'Bankzuordnung wurde entfernt.')
    await loadData()
  } catch (e) {
    showFeedback('error', e instanceof Error ? e.message : 'Bankzuordnung konnte nicht entfernt werden.')
  } finally {
    submitting.value = false
  }
}

onMounted(loadData)
watch(personId, loadData)
</script>

<style scoped>
.context-hint {
  margin-top: 0;
  margin-bottom: 0.75rem;
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 0.65rem 0.75rem;
}

.back-links {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.assignment-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.assign-grid {
  grid-template-columns: 1fr auto;
}

.assignment-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.75rem;
}

.assignment-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem;
}

.muted {
  margin: 0.25rem 0 0;
  color: #64748b;
  font-size: 0.875rem;
}

.success {
  color: #166534;
}

.error {
  color: #991b1b;
}

.danger {
  background: #dc2626;
}
</style>
