<template>
  <div class="ac" @focusout="onBlur">
    <input class="input" :placeholder="placeholder" :value="query" :disabled="disabled" @input="onInput"
      @keydown.down.prevent="move(1)" @keydown.up.prevent="move(-1)" @keydown.enter.prevent="pick(items[active])" />
    <span v-if="loading" class="spinner ac-spin" />
    <ul v-if="open && (items.length || searched)" class="ac-list">
      <li v-for="(item, i) in items" :key="itemKey(item)" :class="{ active: i === active }" @mousedown.prevent="pick(item)">
        <span>{{ itemLabel(item) }}</span>
        <span v-if="itemSub" class="small muted">{{ itemSub(item) }}</span>
      </li>
      <li v-if="!items.length" class="muted small none">{{ $t('common.empty') }}</li>
    </ul>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  fetcher: { type: Function, required: true },
  itemLabel: { type: Function, default: (i) => i.name },
  itemSub: { type: Function, default: null },
  itemKey: { type: Function, default: (i) => i.id },
  placeholder: String,
  minChars: { type: Number, default: 2 },
  clearOnSelect: { type: Boolean, default: true },
  disabled: Boolean,
})
const emit = defineEmits(['select'])
const query = ref('')
const items = ref([])
const open = ref(false)
const loading = ref(false)
const searched = ref(false)
const active = ref(0)
let timer = null
let seq = 0

function onInput(e) {
  query.value = e.target.value
  clearTimeout(timer)
  if (query.value.trim().length < props.minChars) { items.value = []; open.value = false; return }
  timer = setTimeout(search, 250)
}

async function search() {
  const my = ++seq
  loading.value = true
  try {
    const result = await props.fetcher(query.value.trim())
    if (my !== seq) return
    items.value = result
    active.value = 0
    open.value = true
    searched.value = true
  } finally {
    if (my === seq) loading.value = false
  }
}

function move(d) { if (items.value.length) active.value = (active.value + d + items.value.length) % items.value.length }

function pick(item) {
  if (!item) return
  emit('select', item)
  open.value = false
  query.value = props.clearOnSelect ? '' : props.itemLabel(item)
}

function onBlur() { setTimeout(() => { open.value = false }, 150) }
</script>

<style scoped>
.ac { position: relative; }
.ac-spin { position: absolute; right: 10px; top: 10px; }
.ac-list { position: absolute; left: 0; right: 0; top: 42px; background: #fff; border: 1px solid var(--border); border-radius: var(--radius-sm);
  box-shadow: var(--shadow); list-style: none; margin: 0; padding: 4px; z-index: 50; max-height: 300px; overflow: auto; }
.ac-list li { display: flex; flex-direction: column; padding: 8px 10px; border-radius: 4px; cursor: pointer; }
.ac-list li.active, .ac-list li:hover { background: var(--price-blue-lighter); }
.ac-list li.none { cursor: default; }
</style>
