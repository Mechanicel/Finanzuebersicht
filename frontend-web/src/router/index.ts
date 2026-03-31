import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import DashboardView from '../views/DashboardView.vue'
import PersonsView from '../views/PersonsView.vue'
import PersonCreateView from '../views/PersonCreateView.vue'
import PersonDetailView from '../views/PersonDetailView.vue'
import BankAssignmentsView from '../views/BankAssignmentsView.vue'
import AllowancesView from '../views/AllowancesView.vue'
import AccountsView from '../views/AccountsView.vue'
import AccountsCreateView from '../views/AccountsCreateView.vue'
import BankCreateView from '../views/BankCreateView.vue'
import DepotHoldingsFlowView from '../views/DepotHoldingsFlowView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView },
    { path: '/dashboard', component: DashboardView },
    { path: '/persons', redirect: '/persons/select' },
    { path: '/persons/select', component: PersonsView },
    { path: '/persons/new', component: PersonCreateView },
    { path: '/persons/:personId', component: PersonDetailView, props: true },
    { path: '/bank-assignments', component: BankAssignmentsView },
    { path: '/banks/new', component: BankCreateView },
    { path: '/allowances', component: AllowancesView },
    { path: '/accounts', redirect: '/accounts/manage' },
    { path: '/accounts/new', component: AccountsCreateView },
    { path: '/accounts/manage', component: AccountsView },
    { path: '/accounts/depot-holdings', component: DepotHoldingsFlowView }
  ]
})
