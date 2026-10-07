<template>
  <nav class="crumbs" aria-label="breadcrumbs">
    <template v-for="(item, i) in items" :key="i">
      <RouterLink v-if="item.to && i < items.length - 1" :to="item.to">{{ item.label }}</RouterLink>
      <span v-else class="current">{{ item.label }}</span>
      <span v-if="i < items.length - 1" class="sep">/</span>
    </template>
  </nav>
</template>

<script setup>
defineProps({ items: { type: Array, required: true } })
</script>

<style scoped>
.crumbs { font-size: 13px; color: var(--text-muted); display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 4px; }
.current { color: var(--text); }
.sep { opacity: 0.6; }
</style>
