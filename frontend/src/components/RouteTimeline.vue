<template>
  <div class="timeline">
    <p v-if="!analysis.route.length" class="muted small">{{ $t('route.notSubmitted') }}</p>
    <div v-for="stage in stages" :key="stage.stage" class="stage" :class="{ current: stage.stage === analysis.current_stage }">
      <div class="stage-title">{{ stage.title }}</div>
      <div v-for="row in stage.rows" :key="row.key" class="step" :class="row.status">
        <span class="dot" />
        <div class="step-body">
          <div class="row between">
            <b>{{ row.assignee }}</b>
            <span class="badge" :class="badgeClass(row.status)">{{ $t(`route.stepStatus.${row.status}`) }}</span>
          </div>
          <div v-if="row.decided_by_name && row.decided_by_name !== row.assignee" class="small">{{ row.decided_by_name }}<span v-if="row.decided_by_position" class="muted">, {{ row.decided_by_position }}</span></div>
          <div v-if="row.decided_at" class="small muted">{{ datetime(row.decided_at) }}</div>
          <div v-if="row.comment" class="comment">«{{ row.comment }}»</div>
          <div v-if="row.status === 'pending'" class="small current-label">{{ $t('route.current') }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { t } from '../i18n'
import { datetime } from '../format'

const props = defineProps({ analysis: { type: Object, required: true } })

const STAGE_TITLES = { 1: 'approvers.stage1', 2: 'approvers.stage2', 3: 'approvers.stage3' }

const stages = computed(() => {
  const a = props.analysis
  if (a.route.length) {
    const by = {}
    a.route.forEach((s) => { (by[s.stage] ||= []).push({ ...s, key: s.id }) })
    return Object.keys(by).map((k) => ({ stage: Number(k), title: t(STAGE_TITLES[k]), rows: by[k] }))
  }
  // До отправки показываем планируемый маршрут.
  const planned = [{
    stage: 1, title: t(STAGE_TITLES[1]),
    rows: a.approvers.map((ap) => ({ key: `u${ap.user.id}`, assignee: ap.user.full_name, status: 'waiting' })),
  }]
  a.fixed_stages.forEach((fs) => planned.push({ stage: fs.stage, title: t(STAGE_TITLES[fs.stage]),
    rows: [{ key: `s${fs.stage}`, assignee: fs.assignee, status: 'waiting' }] }))
  return planned.filter((s) => s.rows.length)
})

const badgeClass = (s) => ({ approved: 'success', returned: 'danger', pending: '', waiting: 'gray', skipped: 'gray' }[s])
</script>

<style scoped>
.stage { padding: 8px 0 4px; }
.stage-title { font-weight: 600; font-size: 13px; color: var(--text-muted); text-transform: uppercase; letter-spacing: .02em; margin-bottom: 6px; }
.stage.current .stage-title { color: var(--price-blue); }
.step { display: flex; gap: 12px; position: relative; padding: 0 0 12px 4px; }
.step::before { content: ''; position: absolute; left: 9px; top: 18px; bottom: 0; width: 2px; background: var(--border); }
.step:last-child::before { display: none; }
.dot { width: 12px; height: 12px; border-radius: 50%; background: #c8d3e1; margin-top: 4px; flex-shrink: 0; z-index: 1; }
.step.approved .dot { background: var(--success); }
.step.returned .dot { background: var(--danger); }
.step.pending .dot { background: var(--price-blue); box-shadow: 0 0 0 4px var(--price-blue-light); }
.step-body { flex: 1; min-width: 0; }
.step.pending .step-body { background: var(--price-blue-lighter); border-radius: var(--radius-sm); padding: 6px 8px; margin: -6px -8px 0; }
.comment { font-size: 13px; margin-top: 4px; font-style: italic; }
.current-label { color: var(--price-blue); font-weight: 600; margin-top: 2px; }
</style>
