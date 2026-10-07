import { reactive } from 'vue'
import { api } from './api'

export const session = reactive({ user: null, features: {}, loaded: false, unread: 0 })

export async function loadSession() {
  const data = await api.me()
  session.user = data.user
  session.features = data.features || {}
  session.loaded = true
  return session
}

export const hasRole = (role) => !!session.user && session.user.roles.includes(role)

// Пункт меню «Маркетинговый анализ» видят роли из матрицы доступа (раздел 4 ТЗ).
// Согласующие ДЗО ролью не являются — им пункт виден, если они участвуют хотя бы в одном маршруте.
export const canSeeMarketingAnalysis = () =>
  !!session.features.marketing_analysis &&
  (['marketer', 'db_specialist', 'db_director', 'ma_admin'].some((r) => hasRole(r)) ||
    !!session.features.marketing_analysis_participant)
