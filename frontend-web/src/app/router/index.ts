import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/modules/dashboard/pages/HomePage.vue'
import DashboardView from '@/modules/dashboard/pages/DashboardPage.vue'
import PersonsView from '@/modules/persons/pages/PersonsSelectPage.vue'
import PersonCreateView from '@/modules/persons/pages/PersonCreatePage.vue'
import PersonDetailView from '@/modules/persons/pages/PersonDetailPage.vue'
import BankAssignmentsView from '@/modules/banks/pages/BankAssignmentsPage.vue'
import AllowancesView from '@/modules/allowances/pages/AllowancesPage.vue'
import AccountsView from '@/modules/accounts/pages/AccountsManagePage.vue'
import AccountDetailView from '@/modules/accounts/pages/AccountDetailPage.vue'
import AccountsCreateView from '@/modules/accounts/pages/AccountCreatePage.vue'
import BankCreateView from '@/modules/banks/pages/BankCreatePage.vue'
import DepotHoldingsFlowView from '@/modules/accounts/pages/DepotHoldingsFlowPage.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView },
    {
      path: '/dashboard',
      component: DashboardView,
      beforeEnter: (to) => {
        const personId = typeof to.query.personId === 'string' ? to.query.personId.trim() : ''
        return personId.length > 0 ? true : { path: '/' }
      }
    },
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
    { path: '/accounts/manage/:accountId', component: AccountDetailView },
    { path: '/accounts/depot-holdings', component: DepotHoldingsFlowView }
  ]
})
