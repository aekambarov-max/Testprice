<template>
  <div v-if="error" class="alert error" role="alert">
    <div>{{ title || text }}</div>
    <ul v-if="error.errors && error.errors.length">
      <li v-for="(e, i) in error.errors" :key="i">{{ e.message }}</li>
    </ul>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { errorText } from '../i18n'

const props = defineProps({ error: { type: Object, default: null }, title: String })
const text = computed(() => errorText(props.error))
</script>
