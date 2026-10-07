<template>
  <div>
    <div class="grid-2">
      <div>
        <div class="field">
          <label>{{ $t('general.initiator') }}<span class="req"> *</span></label>
          <template v-if="!editable">
            <div>{{ initiatorText }}</div>
          </template>
          <template v-else-if="mode === 'directory'">
            <div v-if="form.initiator_user" class="picked">
              <div><b>{{ form.initiator_user.full_name }}</b><div class="small muted">{{ userSub(form.initiator_user) }}</div></div>
              <button class="icon-btn" @click="form.initiator_user = null">✕</button>
            </div>
            <Autocomplete v-else :fetcher="(q) => api.searchUsers(q)" :item-label="(u) => u.full_name" :item-sub="userSub"
              :placeholder="$t('general.initiatorPh')" @select="(u) => (form.initiator_user = u)" />
            <a href="#" class="small" @click.prevent="mode = 'manual'">{{ $t('general.manual') }}</a>
          </template>
          <template v-else>
            <input v-model="form.initiator_full_name" class="input" :class="{ invalid: touched && !form.initiator_full_name.trim() }" :placeholder="$t('general.initiatorPh')" />
            <span v-if="touched && !form.initiator_full_name.trim()" class="field-error">{{ $t('common.required') }}</span>
            <a href="#" class="small" @click.prevent="mode = 'directory'">{{ $t('general.fromDirectory') }}</a>
          </template>
        </div>
        <template v-if="editable && mode === 'manual'">
          <div class="field"><label>{{ $t('general.position') }}</label><input v-model="form.initiator_position" class="input" /></div>
          <div class="field"><label>{{ $t('general.department') }}</label><input v-model="form.initiator_department" class="input" /></div>
        </template>
      </div>
      <div>
        <div class="field">
          <label>{{ $t('general.dzo') }}<span class="req"> *</span></label>
          <select v-if="!analysis" v-model="form.dzo" class="input">
            <option v-for="d in allowedDzos" :key="d.id" :value="d.id">{{ d.name_ru }}</option>
          </select>
          <template v-else>
            <div>{{ analysis.dzo.name_ru }}</div>
            <span v-if="editable" class="small muted">{{ $t('general.dzoLocked') }}</span>
          </template>
        </div>
        <template v-if="analysis">
          <div class="field"><label>{{ $t('general.author') }}</label><div>{{ analysis.author_name }}</div></div>
          <div class="field"><label>{{ $t('general.created') }}</label><div>{{ datetime(analysis.created_at) }}</div></div>
        </template>
      </div>
    </div>
    <ErrorAlert :error="error" />
    <div v-if="editable" class="row">
      <div class="spacer" />
      <button class="btn primary" :disabled="busy" @click="save">{{ analysis ? $t('common.next') : $t('general.create') }}</button>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { api } from '../../api'
import Autocomplete from '../../components/Autocomplete.vue'
import ErrorAlert from '../../components/ErrorAlert.vue'
import { datetime } from '../../format'
import { session } from '../../store'

const props = defineProps({ analysis: Object, editable: Boolean })
const emit = defineEmits(['saved'])

const a = props.analysis
const allowedDzos = computed(() => session.user?.allowed_dzos || [])
const form = reactive({
  initiator_user: a?.initiator_user || null,
  initiator_full_name: a?.initiator_full_name || '',
  initiator_position: a?.initiator_position || '',
  initiator_department: a?.initiator_department || '',
  dzo: a?.dzo?.id || session.user?.dzo?.id || allowedDzos.value[0]?.id,
})
const mode = ref(a && !a.initiator_user && a.initiator_full_name ? 'manual' : 'directory')
const touched = ref(false)
const busy = ref(false)
const error = ref(null)

const userSub = (u) => [u.position, u.department, u.dzo?.code].filter(Boolean).join(' · ')
const initiatorText = computed(() => {
  if (!a) return '—'
  if (a.initiator_user) return `${a.initiator_user.full_name} (${userSub(a.initiator_user)})`
  return [a.initiator_full_name, a.initiator_position, a.initiator_department].filter(Boolean).join(', ') || '—'
})

async function save() {
  touched.value = true
  const payload = mode.value === 'directory'
    ? { initiator_user: form.initiator_user?.id || null }
    : { initiator_user: null, initiator_full_name: form.initiator_full_name.trim(),
        initiator_position: form.initiator_position, initiator_department: form.initiator_department }
  if (mode.value === 'manual' && !payload.initiator_full_name) return
  busy.value = true
  error.value = null
  try {
    const result = a ? await api.update(a.id, payload) : await api.create({ ...payload, dzo: form.dzo })
    emit('saved', result)
  } catch (e) {
    error.value = e
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.picked { display: flex; justify-content: space-between; align-items: center; border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 8px 12px; background: var(--price-blue-lighter); }
</style>
