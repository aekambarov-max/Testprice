<template>
  <Breadcrumbs :items="[{ label: $t('registry.title'), to: '/marketing-analyses' }, { label: analysis ? analysis.number : $t('card.new') }]" />

  <div v-if="loading" class="card"><div class="skeleton" style="width: 40%" /><div class="skeleton mt" /><div class="skeleton mt" /></div>
  <div v-else-if="loadError" class="card"><ErrorAlert :error="loadError" /></div>

  <template v-else>
    <div class="row between head">
      <div>
        <h1>{{ analysis ? `${$t('card.number')} ${analysis.number}` : $t('card.new') }}</h1>
        <div v-if="analysis" class="row small">
          <span class="badge" :class="statusBadge">{{ $t(`status.${analysis.status}`) }}</span>
          <span class="muted">{{ analysis.dzo.name_ru }}</span>
          <span v-if="analysis.iteration" class="muted">{{ $t('card.iteration') }}{{ analysis.iteration }}</span>
          <span v-if="analysis.total_wo_vat" class="muted">{{ $t('offers.total') }}: <b>{{ money(analysis.total_wo_vat) }} ₸</b></span>
        </div>
      </div>
      <div v-if="analysis" class="row">
        <template v-if="analysis.status === 'approved'">
          <template v-if="analysis.pdf_status === 'ready'">
            <button v-if="DEMO" class="btn primary" data-test="pdf" @click="previewOpen = true">{{ $t('card.pdf') }}</button>
            <a v-else class="btn primary" :href="api.pdfUrl(analysis.id)" :download="analysis.pdf_name" data-test="pdf">⬇ {{ $t('card.pdf') }}</a>
          </template>
          <template v-else-if="analysis.pdf_status === 'failed'">
            <span class="alert error small">{{ $t('card.pdfFailed') }}</span>
            <button v-if="can('regenerate_pdf')" class="btn" @click="act(() => api.regeneratePdf(analysis.id))">{{ $t('card.regeneratePdf') }}</button>
          </template>
          <span v-else class="muted"><span class="spinner" /> {{ $t('card.pdfPending') }}</span>
        </template>
        <button v-if="can('start_collecting')" class="btn" @click="act(() => api.startCollecting(analysis.id))">{{ $t('card.startCollecting') }}</button>
        <button v-if="can('delete')" class="btn danger" @click="deleteOpen = true">{{ $t('card.deleteDraft') }}</button>
        <button v-else-if="can('cancel')" class="btn danger" @click="cancelOpen = true">{{ $t('card.cancelAnalysis') }}</button>
      </div>
    </div>

    <div v-if="message" class="alert success">{{ message }}</div>
    <ErrorAlert :error="actionError" />
    <div v-if="analysis && analysis.status === 'rework' && lastReturn" class="alert warning">
      <b>{{ $t('card.reworkNote') }}:</b> {{ lastReturn.decided_by_name }} — «{{ lastReturn.comment }}»
    </div>

    <DecisionPanel v-if="analysis" :analysis="analysis" :submit="decide" />

    <div class="layout">
      <div class="card main">
        <Stepper v-model="step" :steps="steps" />
        <div v-if="analysis && analysis.status.startsWith('on_')" class="alert info small">{{ $t('card.readOnly') }}</div>
        <StepGeneral v-if="step === 0" :key="`g${analysis?.updated_at}`" :analysis="analysis" :editable="!analysis || editable" @saved="onGeneralSaved" />
        <StepItems v-else-if="step === 1" :analysis="analysis" :editable="editable" @refresh="refresh" @go="go" />
        <StepOffers v-else-if="step === 2" :analysis="analysis" :editable="editable" @refresh="refresh" @updated="setAnalysis" @go="go" />
        <StepApprovers v-else-if="step === 3" :analysis="analysis" :editable="editable" @updated="setAnalysis" @go="go" @submitted="onSubmitted" />
      </div>

      <aside v-if="analysis" class="side">
        <div class="card">
          <div class="side-tabs">
            <button :class="{ active: sideTab === 'route' }" @click="sideTab = 'route'">{{ $t('card.route') }}</button>
            <button :class="{ active: sideTab === 'history' }" @click="openHistory">{{ $t('card.history') }}</button>
          </div>
          <RouteTimeline v-if="sideTab === 'route'" :analysis="analysis" />
          <div v-else>
            <div v-if="!history" class="skeleton" />
            <ul v-else class="events">
              <li v-for="ev in history.events" :key="ev.id">
                <div class="small muted">{{ datetime(ev.created_at) }} · {{ ev.user_name }}</div>
                <div>{{ eventLabel(ev) }}</div>
                <div v-if="ev.comment" class="small"><i>«{{ ev.comment }}»</i></div>
              </li>
            </ul>
          </div>
        </div>
      </aside>
    </div>

    <Modal :open="deleteOpen" :title="$t('card.deleteDraft')" @close="deleteOpen = false">
      <p>{{ $t('card.deleteConfirm') }}</p>
      <template #footer>
        <button class="btn" @click="deleteOpen = false">{{ $t('common.cancel') }}</button>
        <button class="btn danger" @click="removeDraft">{{ $t('common.delete') }}</button>
      </template>
    </Modal>

    <Modal v-if="DEMO && analysis" :open="previewOpen" :title="analysis.pdf_name" width="1000px" @close="previewOpen = false">
      <p class="alert info small">{{ $t('card.demoPdfNote') }}</p>
      <ConclusionPreview :analysis="analysis" />
    </Modal>

    <Modal :open="cancelOpen" :title="$t('card.cancelAnalysis')" @close="cancelOpen = false">
      <p>{{ $t('card.cancelConfirm') }}</p>
      <div class="field"><label>{{ $t('card.cancelReason') }}</label><textarea v-model="cancelReason" class="input" /></div>
      <template #footer>
        <button class="btn" @click="cancelOpen = false">{{ $t('common.cancel') }}</button>
        <button class="btn danger" @click="cancelAnalysis">{{ $t('common.confirm') }}</button>
      </template>
    </Modal>
  </template>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import Breadcrumbs from '../components/Breadcrumbs.vue'
import ConclusionPreview from '../components/ConclusionPreview.vue'
import { DEMO } from '../demo/flag'
import DecisionPanel from '../components/DecisionPanel.vue'
import ErrorAlert from '../components/ErrorAlert.vue'
import Modal from '../components/Modal.vue'
import RouteTimeline from '../components/RouteTimeline.vue'
import Stepper from '../components/Stepper.vue'
import { datetime, money } from '../format'
import { errorText, t } from '../i18n'
import StepApprovers from './steps/StepApprovers.vue'
import StepGeneral from './steps/StepGeneral.vue'
import StepItems from './steps/StepItems.vue'
import StepOffers from './steps/StepOffers.vue'

const props = defineProps({ id: String })
const route = useRoute()
const router = useRouter()

const analysis = ref(null)
const loading = ref(!!props.id)
const loadError = ref(null)
const actionError = ref(null)
const message = ref('')
const step = ref(0)
const sideTab = ref('route')
const history = ref(null)
const cancelOpen = ref(false)
const cancelReason = ref('')
const deleteOpen = ref(false)
const previewOpen = ref(false)
let pdfTimer = null

const can = (a) => !!analysis.value && analysis.value.available_actions.includes(a)
const editable = computed(() => can('edit'))
const statusBadge = computed(() => ({ approved: 'success', rework: 'warning', cancelled: 'gray' }[analysis.value?.status] || ''))
const lastReturn = computed(() => analysis.value?.route.find((s) => s.status === 'returned'))

const steps = computed(() => {
  const a = analysis.value
  return [
    { key: 'general', label: t('card.steps.general'), done: !!a },
    { key: 'items', label: t('card.steps.items'), done: !!a && a.items.length > 0, disabled: !a },
    { key: 'offers', label: t('card.steps.offers'), done: !!a && a.items.length > 0 && a.items.every((i) => i.marketing_price), disabled: !a },
    { key: 'approvers', label: t('card.steps.approvers'), done: !!a && (a.approvers.length > 0 || a.route.length > 0), disabled: !a },
  ]
})

function initialStep(a) {
  if (route.query.step) return Number(route.query.step)
  if (!a) return 0
  if (!editableOf(a)) return 2 // для согласующих — КП и аналитика
  if (!a.items.length) return 1
  return 2
}
const editableOf = (a) => a.available_actions.includes('edit')

function setAnalysis(a) {
  analysis.value = a
  history.value = null
  schedulePdfPoll()
}

async function refresh() {
  try { setAnalysis(await api.get(analysis.value.id)) } catch (e) { actionError.value = e }
}

async function load() {
  if (!props.id) return
  loading.value = true
  loadError.value = null
  try {
    setAnalysis(await api.get(props.id))
    step.value = initialStep(analysis.value)
  } catch (e) {
    loadError.value = e
  } finally {
    loading.value = false
  }
}

function schedulePdfPoll() {
  clearTimeout(pdfTimer)
  if (analysis.value?.status === 'approved' && analysis.value.pdf_status === 'pending') pdfTimer = setTimeout(refresh, 3000)
}

function go(i) { step.value = i }

function onGeneralSaved(a) {
  const isNew = !analysis.value
  setAnalysis(a)
  if (isNew) router.replace({ path: `/marketing-analyses/${a.id}`, query: { step: 1 } })
  else step.value = 1
}

function onSubmitted(a) {
  setAnalysis(a)
  message.value = t('card.submitted')
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function decide(decision, comment, stepId) {
  try {
    setAnalysis(await api.decision(analysis.value.id, decision, comment, stepId))
    message.value = t('decision.done')
  } catch (e) {
    if (e.code === 'step_already_processed' || e.code === 'status_changed') refresh()
    throw new Error(errorText(e))
  }
}

async function act(fn) {
  actionError.value = null
  try { setAnalysis(await fn()) } catch (e) { actionError.value = e }
}

async function cancelAnalysis() {
  cancelOpen.value = false
  await act(() => api.cancel(analysis.value.id, cancelReason.value))
}

async function removeDraft() {
  deleteOpen.value = false
  try { await api.remove(analysis.value.id); router.push('/marketing-analyses') } catch (e) { actionError.value = e }
}

async function openHistory() {
  sideTab.value = 'history'
  if (!history.value) history.value = await api.history(analysis.value.id)
}

const eventLabel = (ev) => {
  const key = `events.${ev.action}`
  const base = t(key) === key ? ev.action : t(key)
  return ev.to_status && ev.from_status !== ev.to_status ? `${base} → ${t(`status.${ev.to_status}`)}` : base
}

watch(() => props.id, () => { if (props.id && props.id !== String(analysis.value?.id)) load() })
watch(() => route.query.step, (s) => { if (s !== undefined) step.value = Number(s) })
load()
onBeforeUnmount(() => clearTimeout(pdfTimer))
</script>

<style scoped>
.head { align-items: flex-start; margin-bottom: 12px; }
.head h1 { margin-bottom: 6px; }
.layout { display: grid; grid-template-columns: minmax(0, 1fr) 340px; gap: 16px; align-items: start; }
@media (max-width: 1100px) { .layout { grid-template-columns: 1fr; } }
.side { position: sticky; top: 80px; }
.side-tabs { display: flex; gap: 4px; margin-bottom: 12px; border-bottom: 1px solid var(--border); }
.side-tabs button { border: none; background: none; padding: 8px 10px; font: inherit; cursor: pointer; color: var(--text-muted); }
.side-tabs button.active { color: var(--price-blue); box-shadow: inset 0 -2px 0 var(--price-blue); font-weight: 600; }
.events { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; max-height: 560px; overflow: auto; }
</style>
