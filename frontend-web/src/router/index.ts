import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import PersonsView from '../views/PersonsView.vue'
import PersonDetailView from '../views/PersonDetailView.vue'
import BankAssignmentsView from '../views/BankAssignmentsView.vue'
import AllowancesView from '../views/AllowancesView.vue'
import AccountsView from '../views/AccountsView.vue'
import HoldingsView from '../views/HoldingsView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: DashboardView },
    { path: '/persons', component: PersonsView },
    { path: '/persons/:personId', component: PersonDetailView, props: true },
    { path: '/bank-assignments', component: BankAssignmentsView },
    { path: '/allowances', component: AllowancesView },
    { path: '/accounts', component: AccountsView },
    { path: '/holdings', component: HoldingsView }
  ]
})
