<template>
  <Teleport to="body" :disabled="!teleport">
    <div v-if="open" class="overlay" @mousedown.self="$emit('close')">
      <div class="modal" role="dialog" aria-modal="true" :style="{ maxWidth: width }">
        <div class="head">
          <h2>{{ title }}</h2>
          <button class="icon-btn" :aria-label="$t('common.close')" @click="$emit('close')">✕</button>
        </div>
        <div class="body"><slot /></div>
        <div v-if="$slots.footer" class="foot"><slot name="footer" /></div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { onBeforeUnmount, onMounted } from 'vue'

defineProps({ open: Boolean, title: String, width: { type: String, default: '560px' }, teleport: { type: Boolean, default: true } })
const emit = defineEmits(['close'])
const onKey = (e) => { if (e.key === 'Escape') emit('close') }
onMounted(() => document.addEventListener('keydown', onKey))
onBeforeUnmount(() => document.removeEventListener('keydown', onKey))
</script>

<style scoped>
.overlay { position: fixed; inset: 0; background: rgba(16, 24, 40, 0.45); display: flex; align-items: flex-start;
  justify-content: center; padding: 60px 16px; z-index: 100; overflow: auto; }
.modal { background: #fff; border-radius: var(--radius); width: 100%; box-shadow: 0 20px 40px rgba(16, 24, 40, 0.2); }
.head { display: flex; justify-content: space-between; align-items: center; padding: 18px 24px 8px; }
.head h2 { margin: 0; }
.body { padding: 8px 24px 16px; }
.foot { display: flex; justify-content: flex-end; gap: 10px; padding: 14px 24px; border-top: 1px solid var(--border); }
</style>
