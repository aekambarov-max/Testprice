<template>
  <div class="bars">
    <div v-for="bar in bars" :key="bar.key" class="bar-row">
      <span class="bar-label" :title="bar.label">{{ bar.label }}</span>
      <div class="track">
        <div class="fill" :class="{ min: bar.isMin }" :style="{ width: `${bar.width}%` }" />
        <div v-for="m in markers" :key="m.label" class="marker" :style="{ left: `${pct(m.value)}%`, borderColor: m.color }" :title="`${m.label}: ${money(m.value)}`" />
      </div>
      <span class="bar-value">{{ money(bar.value) }}</span>
    </div>
    <div v-if="markers.length" class="legend small muted">
      <span v-for="m in markers" :key="m.label"><i :style="{ borderColor: m.color }" />{{ m.label }}: {{ money(m.value) }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { money } from '../format'

const props = defineProps({
  items: { type: Array, required: true }, // [{key,label,value}]
  references: { type: Array, default: () => [] }, // [{label,value,color}]
})
const markers = computed(() => props.references.filter((r) => r.value !== null && r.value !== undefined))
const all = computed(() => [...props.items, ...markers.value].map((x) => Number(x.value)))
const max = computed(() => Math.max(1, ...all.value))
// Шкала начинается не с нуля: цены участников обычно близки, и от нуля разница не видна.
const floor = computed(() => {
  const min = Math.min(...all.value)
  const spread = max.value - min
  return Math.max(0, min - Math.max(spread * 0.6, min * 0.03))
})
const pct = (v) => Math.max(2, ((Number(v) - floor.value) / (max.value * 1.02 - floor.value)) * 100)
const bars = computed(() => {
  const min = Math.min(...props.items.map((i) => Number(i.value)))
  return props.items.map((i) => ({ ...i, width: pct(i.value), isMin: Number(i.value) === min }))
})
</script>

<style scoped>
.bar-row { display: grid; grid-template-columns: 180px 1fr 120px; gap: 10px; align-items: center; margin-bottom: 8px; }
.bar-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; }
.track { position: relative; height: 18px; background: var(--price-blue-lighter); border-radius: 4px; }
.fill { height: 100%; background: #8db5e6; border-radius: 4px; }
.fill.min { background: var(--price-blue); }
.marker { position: absolute; top: -4px; bottom: -4px; border-left: 2px dashed; }
.bar-value { text-align: right; font-variant-numeric: tabular-nums; font-size: 13px; }
@media (max-width: 600px) { .bar-row { grid-template-columns: 96px minmax(0, 1fr) 92px; gap: 6px; } }
.legend { display: flex; gap: 18px; flex-wrap: wrap; margin-top: 6px; }
.legend i { display: inline-block; width: 0; height: 12px; border-left: 2px dashed; margin-right: 6px; vertical-align: middle; }
</style>
