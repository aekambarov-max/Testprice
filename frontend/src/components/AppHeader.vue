<template>
  <header class="app-header">
    <div class="container bar">
      <RouterLink to="/" class="logo" aria-label="Price">
        <svg width="34" height="34" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="7" fill="var(--price-blue)"/><text x="16" y="22" font-size="16" font-weight="700" fill="#fff" text-anchor="middle" font-family="Arial">P</text></svg>
        <span class="logo-text"><b>Price</b><small>{{ $t('app.title') }}</small></span>
      </RouterLink>
      <nav v-if="session.user" class="nav">
        <RouterLink to="/requests">{{ $t('menu.requests') }}</RouterLink>
        <RouterLink to="/suppliers">{{ $t('menu.suppliers') }}</RouterLink>
        <RouterLink to="/catalog">{{ $t('menu.catalog') }}</RouterLink>
        <RouterLink to="/analytics">{{ $t('menu.analytics') }}</RouterLink>
        <RouterLink v-if="showMa" to="/marketing-analyses">{{ $t('menu.ma') }}</RouterLink>
      </nav>
      <div class="spacer" />
      <div class="lang" role="group" aria-label="Язык">
        <button :class="{ active: $i18n.locale === 'ru' }" @click="setLocale('ru')">RU</button>
        <button :class="{ active: $i18n.locale === 'kk' }" @click="setLocale('kk')">KZ</button>
      </div>
      <template v-if="session.user">
        <div class="bell-wrap">
          <button class="icon-btn bell" :title="$t('app.notifications')" @click="toggleBell">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg><span v-if="session.unread" class="bell-count">{{ session.unread }}</span>
          </button>
          <div v-if="bellOpen" class="bell-menu card">
            <div v-if="!notifications.length" class="muted small">{{ $t('app.noNotifications') }}</div>
            <RouterLink v-for="n in notifications" :key="n.id" :to="n.link || '/'" class="notif" :class="{ unread: !n.is_read }" @click="bellOpen = false">
              <b>{{ n.title }}</b><span class="small muted">{{ n.body }}</span>
            </RouterLink>
          </div>
        </div>
        <div class="user">
          <span class="user-name">{{ session.user.full_name }}</span>
          <button class="btn ghost sm" @click="logout">{{ $t('app.logout') }}</button>
        </div>
      </template>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { setLocale } from '../i18n'
import { canSeeMarketingAnalysis, session } from '../store'

const router = useRouter()
const bellOpen = ref(false)
const notifications = ref([])
const showMa = computed(() => canSeeMarketingAnalysis())

async function loadNotifications() {
  if (!session.user) return
  try {
    const data = await api.notifications()
    notifications.value = data.results.slice(0, 8)
    session.unread = data.unread
  } catch { /* колокольчик не критичен */ }
}

async function toggleBell() {
  bellOpen.value = !bellOpen.value
  if (bellOpen.value) {
    await loadNotifications()
    if (session.unread) { await api.readNotifications(); session.unread = 0 }
  }
}

async function logout() {
  await api.logout()
  session.user = null
  router.push('/login')
}

onMounted(loadNotifications)
</script>

<style scoped>
.app-header { background: var(--surface); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 20; }
.bar { display: flex; align-items: center; gap: 24px; height: 64px; }
.logo { display: flex; align-items: center; gap: 10px; color: var(--text); text-decoration: none; }
.logo-text { display: flex; flex-direction: column; line-height: 1.1; }
.logo-text b { font-size: 18px; color: var(--price-blue); }
.logo-text small { font-size: 11px; color: var(--text-muted); }
.nav { display: flex; gap: 4px; }
.nav a { padding: 8px 12px; border-radius: var(--radius-sm); color: var(--text); font-weight: 500; text-decoration: none; }
.nav a:hover { background: var(--price-blue-lighter); color: var(--price-blue); }
.nav a.router-link-active { color: var(--price-blue); box-shadow: inset 0 -2px 0 var(--price-blue); border-radius: 0; }
.lang { display: flex; border: 1px solid var(--border); border-radius: var(--radius-sm); overflow: hidden; }
.lang button { border: none; background: #fff; padding: 5px 9px; font-size: 12px; cursor: pointer; color: var(--text-muted); }
.lang button.active { background: var(--price-blue); color: #fff; }
.user { display: flex; align-items: center; gap: 8px; }
.user-name { font-weight: 500; max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bell-wrap { position: relative; }
.bell { position: relative; font-size: 18px; }
.bell-count { position: absolute; top: -2px; right: -4px; background: var(--danger); color: #fff; font-size: 10px; border-radius: 999px; padding: 0 5px; }
.bell-menu { position: absolute; right: 0; top: 40px; width: 360px; max-height: 420px; overflow: auto; padding: 8px; z-index: 30; }
.notif { display: flex; flex-direction: column; padding: 8px; border-radius: var(--radius-sm); color: var(--text); text-decoration: none; }
.notif:hover { background: var(--price-blue-lighter); }
.notif.unread b::before { content: '●'; color: var(--price-blue); margin-right: 6px; font-size: 10px; }
@media (max-width: 1100px) { .nav { display: none; } .user-name { display: none; } }
@media (max-width: 600px) { .bar { gap: 12px; } .logo-text small { display: none; } }
</style>
