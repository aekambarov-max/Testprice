<template>
  <div v-if="pages > 1" class="pager">
    <span class="muted small">{{ from }}–{{ to }} {{ $t('common.of') }} {{ count }}</span>
    <div class="pages">
      <button class="icon-btn" :disabled="page <= 1" @click="$emit('update:page', page - 1)">‹</button>
      <button v-for="p in visible" :key="p" class="pg" :class="{ active: p === page }" @click="$emit('update:page', p)">{{ p }}</button>
      <button class="icon-btn" :disabled="page >= pages" @click="$emit('update:page', page + 1)">›</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ page: Number, count: Number, pageSize: { type: Number, default: 20 } })
defineEmits(['update:page'])
const pages = computed(() => Math.max(1, Math.ceil(props.count / props.pageSize)))
const from = computed(() => (props.page - 1) * props.pageSize + 1)
const to = computed(() => Math.min(props.count, props.page * props.pageSize))
const visible = computed(() => {
  const start = Math.max(1, Math.min(props.page - 2, pages.value - 4))
  return Array.from({ length: Math.min(5, pages.value) }, (_, i) => start + i)
})
</script>

<style scoped>
.pager { display: flex; justify-content: space-between; align-items: center; margin-top: 14px; }
.pages { display: flex; gap: 4px; align-items: center; }
.pg { min-width: 32px; height: 32px; border: 1px solid var(--border); background: #fff; border-radius: var(--radius-sm); cursor: pointer; }
.pg.active { background: var(--price-blue); border-color: var(--price-blue); color: #fff; }
</style>
