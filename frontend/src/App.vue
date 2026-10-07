<template>
  <template v-if="$route.meta.bare"><RouterView /></template>
  <template v-else>
    <DemoBar v-if="DEMO" />
    <AppHeader :key="`h${userKey}`" />
    <main class="page"><div class="container"><RouterView :key="`v${userKey}${$route.fullPath}`" /></div></main>
    <AppFooter />
  </template>
</template>

<script setup>
import AppFooter from './components/AppFooter.vue'
import AppHeader from './components/AppHeader.vue'
import { computed, defineAsyncComponent } from 'vue'
import { DEMO } from './demo/flag'
import { session } from './store'

// Панель демо подгружается только в демо-сборке; при смене пользователя страницы перемонтируются.
const DemoBar = DEMO ? defineAsyncComponent(() => import('./demo/DemoBar.vue')) : null
const userKey = computed(() => (session.user ? session.user.id : 0))
</script>
