<template>
  <div class="login card">
    <h1>{{ $t('login.title') }}</h1>
    <p class="muted small">{{ $t('login.hint') }}</p>
    <form @submit.prevent="submit">
      <div class="field"><label>{{ $t('login.username') }}</label><input v-model="username" class="input" autocomplete="username" autofocus /></div>
      <div class="field"><label>{{ $t('login.password') }}</label><input v-model="password" type="password" class="input" autocomplete="current-password" /></div>
      <ErrorAlert :error="error" />
      <button class="btn primary" :disabled="busy" style="width:100%;justify-content:center">{{ $t('login.submit') }}</button>
    </form>
    <div v-if="DEMO" class="demo-users">
      <p class="small muted">{{ $t('demo.pickUser') }}</p>
      <button v-for="u in DEMO_USERS" :key="u.username" type="button" class="demo-user" @click="quick(u.username)">
        <b>{{ u.last }} {{ u.first }}</b><span class="small muted">{{ u.hint }} · {{ u.username }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import ErrorAlert from '../components/ErrorAlert.vue'
import { loadSession } from '../store'
import { DEMO } from '../demo/flag'

const router = useRouter()
const route = useRoute()
const username = ref('')
const password = ref('')
const error = ref(null)
const busy = ref(false)

const DEMO_USERS = ref([])
let demoPassword = ''
if (DEMO) import('../demo/mockServer').then((m) => { DEMO_USERS.value = m.DEMO_USERS; demoPassword = m.DEMO_PASSWORD })

async function quick(name) {
  username.value = name
  password.value = demoPassword
  await submit()
}

async function submit() {
  busy.value = true
  error.value = null
  try {
    await api.me() // получить CSRF-cookie
    await api.login(username.value, password.value)
    await loadSession()
    router.push(route.query.next || '/')
  } catch (e) {
    error.value = e
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.login { max-width: 460px; margin: 32px auto; padding: 28px; }
.demo-users { margin-top: 20px; border-top: 1px solid var(--border); padding-top: 12px; display: flex; flex-direction: column; gap: 6px; }
.demo-user { display: flex; flex-direction: column; align-items: flex-start; text-align: left; gap: 2px; border: 1px solid var(--border);
  background: #fff; border-radius: var(--radius-sm); padding: 8px 12px; cursor: pointer; font: inherit; color: var(--text); }
.demo-user:hover, .demo-user:focus-visible { border-color: var(--price-blue); background: var(--price-blue-lighter); }
</style>
