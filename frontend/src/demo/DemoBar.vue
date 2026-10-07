<template>
  <div class="demo-bar">
    <div class="container inner">
      <span class="tag">DEMO</span>
      <span class="text">{{ $t('demo.banner') }}</span>
      <label class="switch" for="demo-user">{{ $t('demo.switchUser') }}</label>
      <select id="demo-user" class="input sel" :value="session.user ? session.user.username : ''" @change="switchUser($event.target.value)">
        <option value="" disabled>—</option>
        <option v-for="u in DEMO_USERS" :key="u.username" :value="u.username">{{ u.last }} {{ u.first[0] }}. — {{ u.hint }}</option>
      </select>
      <button class="btn sm" @click="reset">{{ $t('demo.reset') }}</button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { api } from '../api'
import { loadSession, session } from '../store'
import { DEMO_PASSWORD, DEMO_USERS, resetDemo } from './mockServer'

const router = useRouter()

async function switchUser(username) {
  await api.login(username, DEMO_PASSWORD)
  await loadSession()
  session.unread = 0
  // Карточку оставляем открытой: удобно показать тот же анализ глазами следующего участника маршрута.
  if (!router.currentRoute.value.path.startsWith('/marketing-analyses')) router.push('/marketing-analyses')
}

async function reset() {
  resetDemo()
  session.user = null
  session.loaded = false
  router.push('/login')
}
</script>

<style scoped>
.demo-bar { background: #fff7e6; border-bottom: 1px solid #f5d9a8; color: #7a4b00; font-size: 13px; }
.inner { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding-block: 6px; }
.tag { background: #b54708; color: #fff; font-weight: 700; font-size: 11px; letter-spacing: .06em; padding: 2px 7px; border-radius: 4px; }
.text { flex: 1 1 280px; min-width: 0; }
.switch { font-weight: 600; }
.sel { height: 30px; width: auto; max-width: 100%; font-size: 13px; padding: 0 8px; }
</style>
