<template>
  <div v-if="canDecide" class="decision card">
    <div class="row between">
      <div>
        <h3>{{ $t('decision.awaiting') }}</h3>
        <div class="muted small">{{ $t(`status.${analysis.status}`) }}</div>
      </div>
      <div class="row">
        <button class="btn danger" data-test="rework" @click="openModal('rework')">{{ $t('decision.rework') }}</button>
        <button class="btn success" data-test="approve" @click="openModal('approve')">{{ approveLabel }}</button>
      </div>
    </div>
    <Modal :open="!!mode" :title="mode === 'rework' ? $t('decision.rework') : approveLabel" :teleport="teleport" @close="mode = null">
      <div class="field">
        <label>{{ mode === 'rework' ? $t('decision.comment') : $t('decision.commentOptional') }}<span v-if="mode === 'rework'" class="req"> *</span></label>
        <textarea v-model="comment" class="input" :class="{ invalid: showError }" data-test="comment" rows="4" />
        <span v-if="showError" class="field-error" data-test="comment-error">{{ $t('decision.commentRequired') }}</span>
      </div>
      <div v-if="error" class="alert error">{{ error }}</div>
      <template #footer>
        <button class="btn" @click="mode = null">{{ $t('common.cancel') }}</button>
        <button class="btn" :class="mode === 'rework' ? 'danger' : 'success'" data-test="confirm" :disabled="busy" @click="confirm">
          <span v-if="busy" class="spinner" />{{ mode === 'rework' ? $t('decision.rework') : approveLabel }}
        </button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { t } from '../i18n'
import Modal from './Modal.vue'

const props = defineProps({
  analysis: { type: Object, required: true },
  // async (decision, comment, stepId) => void; ошибка — исключение с текстом
  submit: { type: Function, required: true },
  teleport: { type: Boolean, default: true },
})
const mode = ref(null)
const comment = ref('')
const touched = ref(false)
const busy = ref(false)
const error = ref('')

const canDecide = computed(() => props.analysis.available_actions.includes('approve'))
const approveLabel = computed(() => (props.analysis.current_stage === 3 ? t('decision.approveFinal') : t('decision.approve')))
const showError = computed(() => mode.value === 'rework' && touched.value && !comment.value.trim())

function openModal(m) {
  mode.value = m
  comment.value = ''
  touched.value = false
  error.value = ''
}

async function confirm() {
  touched.value = true
  if (mode.value === 'rework' && !comment.value.trim()) return
  busy.value = true
  error.value = ''
  try {
    await props.submit(mode.value, comment.value.trim(), props.analysis.current_step_id)
    mode.value = null
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.decision { border-left: 4px solid var(--price-blue); }
.decision h3 { margin: 0 0 2px; }
</style>
