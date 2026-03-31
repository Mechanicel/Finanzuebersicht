<template>
  <div class="grid form-grid">
    <div>
      <label>Kontotyp</label>
      <select class="input" :value="modelValue.account_type" @change="onSelect('account_type', $event)">
        <option value="girokonto">{{ accountTypeLabels.girokonto }}</option>
        <option value="tagesgeldkonto">{{ accountTypeLabels.tagesgeldkonto }}</option>
        <option value="festgeldkonto">{{ accountTypeLabels.festgeldkonto }}</option>
        <option value="depot">{{ accountTypeLabels.depot }}</option>
      </select>
    </div>
    <div>
      <label>Bezeichnung</label>
      <input
        class="input"
        :value="modelValue.label"
        @input="onInput('label', $event)"
        maxlength="120"
        placeholder="z. B. Giro Hauptkonto"
      />
    </div>
    <div>
      <label>Bank</label>
      <select class="input" :value="modelValue.bank_id" @change="onSelect('bank_id', $event)">
        <option value="">Bitte auswählen</option>
        <option v-for="bank in bankOptions" :key="bank.bank_id" :value="bank.bank_id">
          {{ bank.name }} ({{ bank.bic }})
        </option>
      </select>
    </div>
    <div>
      <label>Saldo</label>
      <input class="input" :value="modelValue.balance" @input="onInput('balance', $event)" inputmode="decimal" placeholder="0.00" />
    </div>
    <div>
      <label>Währung</label>
      <input class="input" :value="modelValue.currency" @input="onInput('currency', $event)" maxlength="3" placeholder="EUR" />
    </div>

    <div v-if="visibleFields.has('account_number')">
      <label>Kontonummer</label>
      <input class="input" :value="modelValue.account_number" @input="onInput('account_number', $event)" />
    </div>
    <div v-if="visibleFields.has('depot_number')">
      <label>Deponummer</label>
      <input class="input" :value="modelValue.depot_number" @input="onInput('depot_number', $event)" />
    </div>
    <div v-if="visibleFields.has('iban')">
      <label>IBAN</label>
      <input class="input" :value="modelValue.iban" @input="onInput('iban', $event)" />
    </div>
    <div v-if="visibleFields.has('opening_date')">
      <label>Eröffnungsdatum</label>
      <input class="input" :value="modelValue.opening_date" @input="onInput('opening_date', $event)" type="date" />
    </div>
    <div v-if="visibleFields.has('interest_rate')">
      <label>Zinssatz</label>
      <input
        class="input"
        :value="modelValue.interest_rate"
        @input="onInput('interest_rate', $event)"
        inputmode="decimal"
        placeholder="z. B. 2.1500"
      />
    </div>
    <div v-if="visibleFields.has('payout_account_iban')">
      <label>Auszahlungskonto-IBAN</label>
      <input class="input" :value="modelValue.payout_account_iban" @input="onInput('payout_account_iban', $event)" />
    </div>
    <div v-if="visibleFields.has('settlement_account_iban')">
      <label>Verrechnungskonto-IBAN</label>
      <input class="input" :value="modelValue.settlement_account_iban" @input="onInput('settlement_account_iban', $event)" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AccountFormState } from './accountForm'
import { accountTypeLabels, visibleFieldsForAccountType } from './accountForm'
import type { BankReadModel } from '../types/models'

const props = defineProps<{
  modelValue: AccountFormState
  bankOptions: BankReadModel[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: AccountFormState]
}>()

const visibleFields = computed(() => new Set(visibleFieldsForAccountType(props.modelValue.account_type)))

function updateField<Field extends keyof AccountFormState>(field: Field, value: AccountFormState[Field]) {
  emit('update:modelValue', {
    ...props.modelValue,
    [field]: value
  })
}

function onInput(field: keyof AccountFormState, event: Event) {
  const input = event.target as HTMLInputElement
  updateField(field, input.value)
}

function onSelect(field: keyof AccountFormState, event: Event) {
  const select = event.target as HTMLSelectElement
  updateField(field, select.value)
}
</script>
