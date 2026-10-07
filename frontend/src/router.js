import { createMemoryHistory, createRouter, createWebHistory } from 'vue-router'
import { DEMO } from './demo/flag'
import { loadSession, session } from './store'

const routes = [
  { path: '/', redirect: '/marketing-analyses' },
  { path: '/login', component: () => import('./views/LoginView.vue'), meta: { public: true } },
  { path: '/kp/:token', component: () => import('./views/KpResponseView.vue'), meta: { public: true, bare: true } },
  { path: '/marketing-analyses', component: () => import('./views/RegistryView.vue'), meta: { feature: 'marketing_analysis' } },
  { path: '/marketing-analyses/new', component: () => import('./views/AnalysisView.vue'), meta: { feature: 'marketing_analysis' } },
  { path: '/marketing-analyses/:id', component: () => import('./views/AnalysisView.vue'), props: true, meta: { feature: 'marketing_analysis' } },
  { path: '/requests', component: () => import('./views/PlaceholderView.vue'), meta: { section: 'menu.requests' } },
  { path: '/suppliers', component: () => import('./views/PlaceholderView.vue'), meta: { section: 'menu.suppliers' } },
  { path: '/catalog', component: () => import('./views/PlaceholderView.vue'), meta: { section: 'menu.catalog' } },
  { path: '/analytics', component: () => import('./views/PlaceholderView.vue'), meta: { section: 'menu.analytics' } },
]

export const router = createRouter({ history: DEMO ? createMemoryHistory() : createWebHistory(), routes })

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  if (!session.loaded) {
    try { await loadSession() } catch { return true }
  }
  if (!session.user) return { path: '/login', query: { next: to.fullPath } }
  if (to.meta.feature && !session.features[to.meta.feature]) return '/requests'
  return true
})
