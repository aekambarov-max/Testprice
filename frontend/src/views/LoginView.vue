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
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import ErrorAlert from '../components/ErrorAlert.vue'
import { loadSession } from '../store'

const router = useRouter()
const route = useRoute()
const username = ref('')
const password = ref('')
const error = ref(null)
const busy = ref(false)

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
.login { max-width: 420px; margin: 48px auto; padding: 32px; }
</style>
