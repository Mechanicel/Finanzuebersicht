<template>
  <section class="grid person-hub">
    <article class="card">
      <div class="view-header">
        <div class="view-header-copy">
          <p class="eyebrow">Personen-Hub</p>
          <h2>{{ fullName }}</h2>
          <p class="subline">{{ personEmail }}</p>
        </div>
        <RouterLink class="btn flow-btn" to="/persons/select">Zur Personenliste</RouterLink>
      </div>

      <LoadingState v-if="loading" />
      <ErrorState v-else-if="error" :message="error" />

      <template v-else>
        <div class="stats-grid">
          <article class="metric-card">
            <span>Banken</span>
            <strong>{{ personStats.bank_count }}</strong>
          </article>
          <article class="metric-card">
            <span>Konten</span>
            <strong>{{ accountCount }}</strong>
          </article>
          <article class="metric-card">
            <span>Freibeträge gesamt</span>
            <strong>{{ personStats.allowance_total }} EUR</strong>
          </article>
        </div>

        <div class="hub-sections">
          <article class="hub-card">
            <h3>Verwalten</h3>
            <p>Arbeite die Stammdaten und fachlichen Verwaltungs-Schritte für diese Person ab.</p>
            <div class="action-list">
              <RouterLink class="action-item" :to="personRoute('/bank-assignments')">Bank hinzufügen / Bankzuordnung</RouterLink>
              <RouterLink class="action-item" :to="personRoute('/allowances')">Freibeträge verwalten</RouterLink>
              <RouterLink class="action-item" :to="personRoute('/accounts/new')">Konto hinzufügen</RouterLink>
              <RouterLink class="action-item" :to="personRoute('/accounts/manage')">Konten ansehen &amp; bearbeiten</RouterLink>
            </div>
          </article>

          <article class="hub-card">
            <h3>Analysieren</h3>
            <p>Öffne die Auswertungen und Kennzahlen mit dem gesetzten Personenkontext.</p>
            <div class="action-list">
              <RouterLink class="action-item" :to="personRoute('/dashboard')">Dashboard / Analyse öffnen</RouterLink>
            </div>
          </article>

          <article class="hub-card">
            <h3>Stammdaten</h3>
            <p>Bearbeite die Person direkt aus dem Hub heraus.</p>
            <div class="grid" style="grid-template-columns: 1fr 1fr 1fr">
              <div><label>Vorname</label><input class="input" v-model.trim="form.firstName" /></div>
              <div><label>Nachname</label><input class="input" v-model.trim="form.lastName" /></div>
              <div><label>E-Mail</label><input class="input" v-model.trim="form.email" type="email" /></div>
            </div>
            <div class="grid tax-profile-grid">
              <div>
                <label>Steuerland</label>
                <select class="input" v-model="form.taxCountry">
                  <option value="DE">Deutschland (DE)</option>
                </select>
              </div>
              <div>
                <label>Veranlagungsstatus</label>
                <select class="input" v-model="form.filingStatus">
                  <option value="single">single</option>
                  <option value="joint">joint</option>
                </select>
              </div>
            </div>
            <p v-if="formError" class="error">{{ formError }}</p>
            <div class="form-actions">
              <button class="btn" @click="save" :disabled="submitting">Änderungen speichern</button>
              <button class="btn" @click="deleteCurrent" :disabled="submitting" style="background: #dc2626">Person löschen</button>
            </div>
          </article>
        </div>
      </template>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '@/shared/api/client'
import type { FilingStatus, PersonListItem, TaxCountryCode } from '@/shared/model/types'
import LoadingState from '@/shared/ui/LoadingState.vue'
import ErrorState from '@/shared/ui/ErrorState.vue'
import { extractApiErrorMessage } from '@/shared/api/extractApiErrorMessage'

const props = defineProps<{ personId: string }>()
const personId = props.personId
const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const error = ref<string | null>(null)
const accountCount = ref(0)
const personStats = ref<PersonListItem>({
  person_id: personId,
  first_name: '',
  last_name: '',
  email: null,
  bank_count: 0,
  allowance_total: '0.00'
})

const form = reactive({
  firstName: '',
  lastName: '',
  email: '',
  taxCountry: 'DE' as TaxCountryCode,
  filingStatus: 'single' as FilingStatus
})
const formError = ref<string | null>(null)

const fullName = computed(() => {
  if (!form.firstName && !form.lastName) {
    return 'Person lädt ...'
  }
  return `${form.firstName} ${form.lastName}`.trim()
})

const personEmail = computed(() => form.email || 'Keine E-Mail hinterlegt')

function personRoute(path: string) {
  return { path, query: { personId } }
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const [personDetail, accountList] = await Promise.all([apiClient.person(personId), apiClient.accounts(personId)])
    form.firstName = personDetail.person.first_name
    form.lastName = personDetail.person.last_name
    form.email = personDetail.person.email ?? ''
    form.taxCountry = personDetail.person.tax_profile?.tax_country ?? 'DE'
    form.filingStatus = personDetail.person.tax_profile?.filing_status === 'joint' ? 'joint' : 'single'
    personStats.value = personDetail.stats
    accountCount.value = accountList.length
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Fehler beim Laden'
  } finally {
    loading.value = false
  }
}

async function save() {
  formError.value = null
  if (!form.firstName || !form.lastName) {
    formError.value = 'Vorname und Nachname sind Pflichtfelder.'
    return
  }

  submitting.value = true
  try {
    await apiClient.updatePerson(personId, {
      first_name: form.firstName,
      last_name: form.lastName,
      email: form.email || undefined,
      tax_profile: {
        tax_country: form.taxCountry,
        filing_status: form.filingStatus
      }
    })
    await load()
  } catch (e) {
    formError.value = extractApiErrorMessage(e, 'Speichern fehlgeschlagen.')
  } finally {
    submitting.value = false
  }
}

async function deleteCurrent() {
  formError.value = null
  submitting.value = true
  try {
    await apiClient.deletePerson(personId)
    await router.push('/persons/select')
  } catch (e) {
    formError.value = e instanceof Error ? e.message : 'Löschen fehlgeschlagen.'
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.person-hub {
  grid-template-columns: 1fr;
}

.eyebrow {
  margin: 0;
  color: #475569;
  font-weight: 600;
}

.subline {
  margin-top: 0.4rem;
  color: #475569;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.metric-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.75rem;
  background: #f8fafc;
}

.metric-card span {
  color: #64748b;
  font-size: 0.85rem;
}

.metric-card strong {
  display: block;
  margin-top: 0.25rem;
  font-size: 1.2rem;
}

.hub-sections {
  display: grid;
  gap: 1rem;
}

.hub-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem;
}

.hub-card h3 {
  margin-top: 0;
}

.hub-card p {
  color: #475569;
}

.action-list {
  display: grid;
  gap: 0.5rem;
}

.action-item {
  display: block;
  text-decoration: none;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 0.6rem 0.75rem;
  color: #0f172a;
  background: #ffffff;
}

.action-item:hover {
  border-color: #2563eb;
  background: #eff6ff;
}

.form-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.tax-profile-grid {
  grid-template-columns: 1fr 1fr;
  margin-top: 0.75rem;
}
</style>
