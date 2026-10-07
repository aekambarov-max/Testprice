<template>
  <template v-if="$route.meta.bare"><RouterView /></template>
  <template v-else>
    <AppHeader />
    <main class="page"><div class="container"><RouterView /></div></main>
    <AppFooter />
  </template>
</template>

<script setup>
import AppFooter from './components/AppFooter.vue'
import AppHeader from './components/AppHeader.vue'
</script>
