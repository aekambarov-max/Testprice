<template>
  <span class="file-input">
    <input ref="input" type="file" :accept="accept" hidden @change="onChange" />
    <button type="button" class="btn sm" :disabled="disabled" @click="input.click()">{{ label }}</button>
    <span v-if="showName && name" class="small muted name">{{ name }}</span>
  </span>
</template>

<script setup>
import { ref } from 'vue'

defineProps({ label: String, disabled: Boolean, showName: { type: Boolean, default: true },
  accept: { type: String, default: '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png' } })
const emit = defineEmits(['change'])
const input = ref(null)
const name = ref('')

function onChange(e) {
  const file = e.target.files[0]
  if (!file) return
  name.value = file.name
  emit('change', file)
  e.target.value = ''
}
</script>

<style scoped>
.file-input { display: inline-flex; align-items: center; gap: 8px; }
.name { max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
