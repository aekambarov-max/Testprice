<template>
  <ol class="stepper">
    <li v-for="(step, i) in steps" :key="step.key" class="step"
      :class="{ active: i === modelValue, done: step.done, disabled: step.disabled }">
      <button type="button" :disabled="step.disabled" :aria-current="i === modelValue ? 'step' : null" @click="select(i)">
        <span class="circle">{{ step.done && i !== modelValue ? '✓' : i + 1 }}</span>
        <span class="label">{{ step.label }}</span>
      </button>
      <span v-if="i < steps.length - 1" class="line" />
    </li>
  </ol>
</template>

<script setup>
const props = defineProps({ steps: { type: Array, required: true }, modelValue: { type: Number, default: 0 } })
const emit = defineEmits(['update:modelValue'])

function select(i) {
  if (props.steps[i].disabled || i === props.modelValue) return
  emit('update:modelValue', i)
}
</script>

<style scoped>
.stepper { display: flex; list-style: none; padding: 0; margin: 0 0 18px; gap: 0; }
.step { display: flex; align-items: center; flex: 1; min-width: 0; }
.step:last-child { flex: 0 0 auto; }
.step button { display: flex; align-items: center; gap: 10px; border: none; background: none; font: inherit; cursor: pointer;
  padding: 6px 4px; color: var(--text-muted); text-align: left; flex-shrink: 0; }
.label { max-width: 150px; line-height: 1.25; }
.step button:disabled { cursor: not-allowed; opacity: 0.55; }
.circle { width: 30px; height: 30px; border-radius: 50%; border: 2px solid var(--border); display: inline-flex; align-items: center;
  justify-content: center; font-weight: 600; background: #fff; flex-shrink: 0; }
.step.done .circle { border-color: var(--price-blue); color: var(--price-blue); }
.step.active .circle { background: var(--price-blue); border-color: var(--price-blue); color: #fff; }
.step.active .label { color: var(--text); font-weight: 600; }
.line { flex: 1; height: 2px; background: var(--border); margin: 0 12px; min-width: 16px; }
.step.done .line { background: var(--price-blue); }
@media (max-width: 760px) { .label { display: none; } }
</style>
