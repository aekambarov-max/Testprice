<template>
  <div>
    <h3>{{ $t('approvers.stage1') }}</h3>
    <p v-if="editable" class="muted small">{{ $t('approvers.stage1Hint') }}</p>
    <div v-if="editable" class="add">
      <Autocomplete :fetcher="(q) => api.searchUsers(q, analysis.dzo.id)" :item-label="(u) => u.full_name"
        :item-sub="(u) => [u.position, u.department].filter(Boolean).join(' · ')" :placeholder="$t('approvers.searchPh')"
        @select="addUser" />
    </div>
    <ol class="approvers" data-test="approvers">
      <li v-for="(u, i) in list" :key="u.id" class="approver" :draggable="editable"
        :class="{ over: overIndex === i }" @dragstart="dragIndex = i" @dragover.prevent="overIndex = i"
        @dragleave="overIndex = null" @drop.prevent="drop(i)">
        <span v-if="editable" class="handle" aria-hidden="true">⋮⋮</span>
        <span class="order">{{ i + 1 }}</span>
        <div class="who"><b>{{ u.full_name }}</b><span class="small muted">{{ [u.position, u.department].filter(Boolean).join(' · ') }}</span></div>
        <template v-if="editable">
          <button class="icon-btn" :title="$t('approvers.up')" :disabled="i === 0" @click="move(i, -1)">↑</button>
          <button class="icon-btn" :title="$t('approvers.down')" :disabled="i === list.length - 1" @click="move(i, 1)">↓</button>
          <button class="icon-btn" :title="$t('common.delete')" @click="list.splice(i, 1); dirty = true">✕</button>
        </template>
      </li>
    </ol>
    <p v-if="!list.length" class="muted">{{ $t('approvers.empty') }}</p>

    <div v-for="fs in analysis.fixed_stages" :key="fs.stage" class="fixed">
      <h3>{{ $t(`approvers.stage${fs.stage}`) }}</h3>
      <div class="approver locked">
        <span class="order">🔒</span>
        <div class="who"><b>{{ fs.assignee }}</b><span class="small muted">{{ $t('approvers.fixed') }}</span></div>
      </div>
    </div>

    <ErrorAlert :error="error" :title="error && error.code === 'validation_failed' ? $t('card.submitErrors') : ''" />

    <div v-if="editable" class="row mt">
      <button class="btn" @click="$emit('go', 2)">{{ $t('common.back') }}</button>
      <div class="spacer" />
      <button class="btn" :disabled="!dirty || busy" @click="save">{{ $t('approvers.saveOrder') }}</button>
      <button v-if="canSubmit" class="btn primary" :disabled="busy" data-test="submit" @click="submit">
        <span v-if="busy" class="spinner" />{{ $t('card.submit') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { api } from '../../api'
import Autocomplete from '../../components/Autocomplete.vue'
import ErrorAlert from '../../components/ErrorAlert.vue'

const props = defineProps({ analysis: { type: Object, required: true }, editable: Boolean })
const emit = defineEmits(['updated', 'go', 'submitted'])

const list = ref(props.analysis.approvers.map((a) => a.user))
const dirty = ref(false)
const busy = ref(false)
const error = ref(null)
const dragIndex = ref(null)
const overIndex = ref(null)
const canSubmit = computed(() => props.analysis.available_actions.includes('submit'))

watch(() => props.analysis.approvers, (v) => { if (!dirty.value) list.value = v.map((a) => a.user) })

function addUser(u) {
  if (!list.value.some((x) => x.id === u.id)) { list.value.push(u); dirty.value = true }
}

function move(i, d) {
  const [u] = list.value.splice(i, 1)
  list.value.splice(i + d, 0, u)
  dirty.value = true
}

function drop(i) {
  if (dragIndex.value !== null && dragIndex.value !== i) move(dragIndex.value, i - dragIndex.value)
  dragIndex.value = overIndex.value = null
}

async function save() {
  busy.value = true
  error.value = null
  try {
    emit('updated', await api.setApprovers(props.analysis.id, list.value.map((u) => u.id)))
    dirty.value = false
    return true
  } catch (e) {
    error.value = e
    return false
  } finally {
    busy.value = false
  }
}

async function submit() {
  if (dirty.value && !(await save())) return
  busy.value = true
  error.value = null
  try {
    emit('submitted', await api.submit(props.analysis.id))
  } catch (e) {
    error.value = e
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.add { max-width: 520px; margin-bottom: 12px; }
.approvers { list-style: none; padding: 0; margin: 0 0 12px; display: flex; flex-direction: column; gap: 8px; max-width: 720px; }
.approver { display: flex; align-items: center; gap: 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 8px 12px; background: #fff; }
.approver.over { border-color: var(--price-blue); background: var(--price-blue-lighter); }
.approver.locked { background: #f6f8fb; max-width: 720px; }
.handle { cursor: grab; color: var(--text-muted); letter-spacing: -2px; }
.order { width: 26px; height: 26px; border-radius: 50%; background: var(--price-blue-light); color: var(--price-blue); display: inline-flex; align-items: center; justify-content: center; font-weight: 600; font-size: 12px; }
.who { display: flex; flex-direction: column; flex: 1; }
.fixed { margin-top: 18px; }
</style>
