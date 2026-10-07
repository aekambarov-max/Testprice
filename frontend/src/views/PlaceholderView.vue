<template>
  <Breadcrumbs :items="[{ label: $t($route.meta.section) }]" />
  <h1>{{ $t($route.meta.section) }}</h1>
  <div class="card empty-state">
    <div class="icon">🗂</div>
    <h3>{{ $t('placeholder.title') }}</h3>
    <p>{{ $t('placeholder.text') }}</p>
  </div>
</template>

<script setup>
import Breadcrumbs from '../components/Breadcrumbs.vue'
</script>
