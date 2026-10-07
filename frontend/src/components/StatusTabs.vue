<template>
  <div class="tabs" role="tablist">
    <button v-for="tab in tabs" :key="tab.key" role="tab" class="pill" :class="{ active: tab.key === modelValue }"
      :aria-selected="tab.key === modelValue" @click="$emit('update:modelValue', tab.key)">
      {{ tab.label }}<span v-if="tab.count !== undefined && tab.count !== null" class="count">{{ tab.count }}</span>
    </button>
  </div>
</template>

<script setup>
defineProps({ tabs: { type: Array, required: true }, modelValue: { type: String, default: 'all' } })
defineEmits(['update:modelValue'])
</script>

<style scoped>
.tabs { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
.pill { display: inline-flex; align-items: center; gap: 8px; height: 36px; padding: 0 16px; border-radius: 999px;
  border: 1px solid var(--price-blue); background: #fff; color: var(--price-blue); font: inherit; font-weight: 500; cursor: pointer; }
.pill:hover { background: var(--price-blue-lighter); }
.count { min-width: 22px; height: 22px; padding: 0 6px; border-radius: 999px; background: var(--price-blue); color: #fff;
  font-size: 12px; display: inline-flex; align-items: center; justify-content: center; }
.pill.active { background: var(--price-blue); color: #fff; }
.pill.active .count { background: #fff; color: var(--price-blue); }
</style>
