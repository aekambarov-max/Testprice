<template>
  <Breadcrumbs :items="[{ label: $t('registry.title') }]" />
  <div class="row between">
    <h1>{{ $t('registry.title') }}</h1>
    <RouterLink v-if="isMarketer" to="/marketing-analyses/new" class="btn primary">+ {{ $t('registry.create') }}</RouterLink>
  </div>

  <StatusTabs v-model="tab" :tabs="tabs" />

  <div class="card">
    <div class="filters">
      <input v-model="filters.q" class="input search" :placeholder="$t('registry.searchPh')" @keyup.enter="reload" />
      <select v-model="filters.dzo" class="input dzo" @change="reload">
        <option value="">{{ $t('registry.dzo') }}: {{ $t('common.all') }}</option>
        <option v-for="d in dzos" :key="d.id" :value="d.id">{{ dzoName(d) }}</option>
      </select>
      <label class="small muted">{{ $t('common.from') }}</label>
      <input v-model="filters.date_from" type="date" class="input date" @change="reload" />
      <label class="small muted">{{ $t('common.to') }}</label>
      <input v-model="filters.date_to" type="date" class="input date" @change="reload" />
      <button class="btn" @click="reload">{{ $t('common.search') }}</button>
      <button v-if="hasFilters" class="btn ghost" @click="resetFilters">{{ $t('common.reset') }}</button>
    </div>

    <ErrorAlert :error="error" />
    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>{{ $t('registry.number') }}</th>
            <th>{{ $t('registry.subject') }}</th>
            <th>{{ $t('registry.dzo') }}</th>
            <th>{{ $t('registry.initiator') }}</th>
            <th>{{ $t('registry.author') }}</th>
            <th>{{ $t('registry.status') }}</th>
            <th class="num">{{ $t('registry.total') }}</th>
            <th>{{ $t('registry.created') }}</th>
          </tr>
        </thead>
        <tbody v-if="loading">
          <tr v-for="i in 5" :key="i"><td v-for="j in 8" :key="j"><div class="skeleton" /></td></tr>
        </tbody>
        <tbody v-else>
          <tr v-for="row in rows" :key="row.id">
            <td class="nowrap"><RouterLink :to="`/marketing-analyses/${row.id}`">{{ row.number }}</RouterLink></td>
            <td>{{ row.first_item_name || '—' }}<span v-if="row.items_count > 1" class="sub">+{{ row.items_count - 1 }} {{ $t('registry.positions') }}</span></td>
            <td>{{ dzoName(row.dzo) }}</td>
            <td>{{ row.initiator || '—' }}</td>
            <td>{{ row.author_name }}</td>
            <td><span class="status-text">{{ $t(`status.${row.status}`) }}</span></td>
            <td class="num">{{ money(row.total_wo_vat) }}</td>
            <td class="nowrap">{{ date(row.created_at) }}<span class="sub">{{ time(row.created_at) }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="!loading && !rows.length" class="empty-state">
      <div class="icon">📄</div>
      {{ hasFilters || tab !== 'all' ? $t('registry.emptyFiltered') : $t('registry.empty') }}
    </div>
    <Pagination v-model:page="page" :count="count" :page-size="20" />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import Breadcrumbs from '../components/Breadcrumbs.vue'
import ErrorAlert from '../components/ErrorAlert.vue'
import Pagination from '../components/Pagination.vue'
import StatusTabs from '../components/StatusTabs.vue'
import { date, money, time } from '../format'
import { i18nState, t } from '../i18n'
import { hasRole } from '../store'

const route = useRoute()
const router = useRouter()
const isMarketer = computed(() => hasRole('marketer'))

const tab = ref(route.query.tab || (isMarketer.value ? 'all' : 'awaiting_me'))
const page = ref(Number(route.query.page) || 1)
const filters = reactive({ q: '', dzo: '', date_from: '', date_to: '' })
const rows = ref([])
const counts = ref({})
const count = ref(0)
const loading = ref(true)
const error = ref(null)
const dzos = ref([])

const TAB_KEYS = ['draft', 'collecting_kp', 'on_approval', 'rework', 'approved', 'all']
const tabs = computed(() => {
  const keys = [...TAB_KEYS]
  // «Ожидают моего решения» — для согласующих (в т.ч. согласующих ДЗО без роли, у кого есть такие анализы).
  if (!isMarketer.value || counts.value.awaiting_me) keys.unshift('awaiting_me')
  return keys.map((key) => ({ key, label: t(`tabs.${key}`), count: counts.value[key] }))
})
const hasFilters = computed(() => Object.values(filters).some(Boolean))
const dzoName = (d) => (d ? (i18nState.locale === 'kk' && d.name_kk) || d.name_ru : '—')

async function load() {
  loading.value = true
  error.value = null
  try {
    const data = await api.list({ tab: tab.value, page: page.value, ...filters })
    rows.value = data.results
    count.value = data.count
    counts.value = data.counts
  } catch (e) {
    error.value = e
    rows.value = []
  } finally {
    loading.value = false
  }
}

function reload() {
  if (page.value !== 1) page.value = 1
  else load()
}

function resetFilters() {
  Object.keys(filters).forEach((k) => { filters[k] = '' })
  reload()
}

watch(tab, () => { router.replace({ query: { tab: tab.value } }); reload() })
watch(page, load)
onMounted(async () => {
  load()
  try { dzos.value = await api.dzos() } catch { /* фильтр по ДЗО необязателен */ }
})
</script>

<style scoped>
.filters { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 16px; }
.filters .search { flex: 1; min-width: 240px; }
.filters .dzo { width: 240px; }
.filters .date { width: 150px; }
</style>
