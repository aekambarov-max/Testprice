<template>
  <div>
    <div v-if="editable" class="row toolbar">
      <button class="btn" @click="requestOpen = true">{{ $t('offers.requestKp') }}</button>
      <button class="btn" @click="openUpload">+ {{ $t('offers.upload') }}</button>
      <div class="spacer" />
      <button class="btn primary" :disabled="!analysis.offers.length || busy" @click="calculate">
        <span v-if="busy" class="spinner" />{{ $t('offers.calculate') }}
      </button>
    </div>
    <div v-if="notice" class="alert success">{{ notice }}</div>
    <ErrorAlert :error="error" />

    <!-- Таблица КП по позициям -->
    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>{{ $t('offers.supplier') }}<span class="sub">{{ $t('offers.bin') }}</span></th>
            <th>{{ $t('offers.date') }}</th>
            <th>{{ $t('offers.currency') }}<span class="sub">{{ $t('offers.rate') }}</span></th>
            <th v-for="item in analysis.items" :key="item.id" class="num" :title="item.name">
              {{ item.line_no }}. {{ short(item.name) }}<span class="sub">{{ $t('offers.priceKzt') }}</span>
            </th>
            <th v-if="editable" />
          </tr>
        </thead>
        <tbody>
          <tr v-for="offer in analysis.offers" :key="offer.id">
            <td>{{ offer.supplier_name }}<span class="sub">{{ offer.supplier_bin }} · {{ offer.source === 'system' ? $t('offers.sourceSystem') : $t('offers.sourceManual') }}</span>
              <a :href="api.offerUrl(analysis.id, offer.id)" class="small file-link">📄 {{ offer.original_name }}</a></td>
            <td class="nowrap">{{ date(offer.offer_date) }}</td>
            <td class="nowrap">{{ offer.currency }}, {{ offer.vat_included ? $t('offers.withVat') : $t('offers.withoutVat') }}
              <span v-if="offer.currency !== 'KZT'" class="sub">{{ offer.exchange_rate }}</span></td>
            <td v-for="item in analysis.items" :key="item.id" class="num">
              <template v-if="priceOf(offer, item)">
                {{ money(priceOf(offer, item).price_kzt_wo_vat) }}
                <span v-if="offer.currency !== 'KZT' || offer.vat_included" class="sub">{{ money(priceOf(offer, item).price) }} {{ offer.currency }}</span>
              </template>
              <span v-else class="muted">—</span>
            </td>
            <td v-if="editable"><button class="icon-btn" :title="$t('common.delete')" @click="removeOffer(offer)">🗑</button></td>
          </tr>
        </tbody>
        <tfoot v-if="analysis.offers.length">
          <tr>
            <td colspan="3">{{ $t('offers.marketing') }}</td>
            <td v-for="item in analysis.items" :key="item.id" class="num">
              {{ item.marketing_price ? money(item.marketing_price) : $t('offers.notCalculated') }}
            </td>
            <td v-if="editable" />
          </tr>
        </tfoot>
      </table>
    </div>
    <div v-if="!analysis.offers.length" class="empty-state">{{ $t('offers.empty') }}</div>

    <!-- Окно аналитики -->
    <template v-if="stats && analysis.offers.length">
      <h2 class="mt">{{ $t('offers.analytics') }}</h2>
      <div class="row small muted">
        <span>{{ $t('offers.participants') }}: <b>{{ stats.participants }}</b></span>
        <span>{{ $t('offers.method') }}: {{ $t(`offers.methods.${stats.calc_method}`) }}, {{ $t('offers.withoutVat') }} ({{ stats.vat_rate_percent }}%)</span>
      </div>
      <div v-for="it in stats.items" :key="it.item_id" class="an-item">
        <h3>{{ it.line_no }}. {{ it.name }} <span class="muted small">({{ it.nsi_code }})</span></h3>
        <div class="an-grid">
          <div>
            <div class="small muted">{{ $t('offers.chart') }}</div>
            <BarChart :items="it.offers.map((o) => ({ key: o.offer_id, label: o.supplier_name, value: o.price_kzt_wo_vat }))"
              :references="[{ label: $t('offers.marketing'), value: it.marketing_price, color: 'var(--price-blue-dark)' },
                            { label: $t('offers.kmgAvg'), value: it.kmg_average, color: 'var(--warning)' }]" />
          </div>
          <dl class="kv">
            <dt>{{ $t('offers.min') }}</dt><dd>{{ money(it.min) }}</dd>
            <dt>{{ $t('offers.max') }}</dt><dd>{{ money(it.max) }}</dd>
            <dt>{{ $t('offers.avg') }}</dt><dd>{{ money(it.average) }}</dd>
            <dt>{{ $t('offers.marketing') }}</dt><dd><b>{{ money(it.marketing_price) }}</b></dd>
            <dt>{{ $t('offers.kmgAvg') }}</dt><dd>{{ money(it.kmg_average) }} <span v-if="it.kmg_count" class="muted small">(n={{ it.kmg_count }})</span></dd>
            <dt>{{ $t('offers.deviation') }}</dt>
            <dd><span :class="{ 'badge warning': it.deviation_exceeds_threshold }">{{ percent(it.deviation_from_kmg_percent) }}</span></dd>
          </dl>
        </div>
        <details class="history">
          <summary class="small">{{ $t('offers.history') }} ({{ it.history.length }})</summary>
          <table v-if="it.history.length" class="table small-table">
            <thead><tr><th>{{ $t('registry.dzo') }}</th><th>{{ $t('registry.number') }}</th><th>{{ $t('route.date') }}</th><th class="num">{{ $t('items.price') }}</th></tr></thead>
            <tbody>
              <tr v-for="(h, i) in it.history" :key="i">
                <td>{{ h.dzo }}</td><td>{{ h.source_number }}</td><td>{{ date(h.approved_at) }}</td><td class="num">{{ money(h.price_wo_vat) }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else class="muted small">{{ $t('offers.noHistory') }}</p>
        </details>
      </div>

      <h3 class="mt">{{ $t('offers.summary') }}</h3>
      <table class="table">
        <thead><tr><th>№</th><th>{{ $t('items.name') }}</th><th>{{ $t('items.unit') }}</th><th class="num">{{ $t('items.quantity') }}</th>
          <th class="num">{{ $t('items.price') }}</th><th class="num">{{ $t('items.sum') }}</th></tr></thead>
        <tbody>
          <tr v-for="item in analysis.items" :key="item.id">
            <td>{{ item.line_no }}</td><td>{{ item.name }}</td><td>{{ item.unit }}</td><td class="num">{{ qty(item.quantity) }}</td>
            <td class="num">{{ money(item.marketing_price) }}</td><td class="num">{{ money(item.total_wo_vat) }}</td>
          </tr>
        </tbody>
        <tfoot><tr><td colspan="5">{{ $t('offers.total') }}, ₸</td><td class="num">{{ money(analysis.total_wo_vat) }}</td></tr></tfoot>
      </table>
    </template>

    <div class="field mt">
      <label>{{ $t('general.justification') }}</label>
      <textarea v-if="editable" v-model="justification" class="input" rows="3" @change="saveJustification" />
      <div v-else>{{ analysis.price_justification || '—' }}</div>
    </div>

    <div v-if="editable" class="row mt">
      <button class="btn" @click="$emit('go', 1)">{{ $t('common.back') }}</button>
      <div class="spacer" />
      <button class="btn primary" @click="$emit('go', 3)">{{ $t('common.next') }}</button>
    </div>

    <!-- Запрос КП -->
    <Modal :open="requestOpen" :title="$t('offers.requestTitle')" width="620px" @close="requestOpen = false">
      <p class="muted small">{{ $t('offers.requestHint') }}</p>
      <div class="supplier-list">
        <label v-for="s in suppliers" :key="s.id" class="checkbox">
          <input v-model="selectedSuppliers" type="checkbox" :value="s.id" />
          <span>{{ s.name }} <span class="muted small">{{ s.bin }} · {{ s.email || '—' }}</span></span>
        </label>
      </div>
      <div class="field mt"><label>{{ $t('offers.message') }}</label><textarea v-model="requestMessage" class="input" rows="3" /></div>
      <ErrorAlert :error="modalError" />
      <template #footer>
        <button class="btn" @click="requestOpen = false">{{ $t('common.cancel') }}</button>
        <button class="btn primary" :disabled="!selectedSuppliers.length || busy" @click="sendRequests">{{ $t('offers.send') }}</button>
      </template>
    </Modal>

    <!-- Загрузка КП -->
    <Modal :open="uploadOpen" :title="$t('offers.uploadTitle')" width="680px" @close="uploadOpen = false">
      <div class="field">
        <label>{{ $t('offers.supplierPick') }}</label>
        <select v-model="offer.supplierId" class="input" @change="pickSupplier">
          <option value="">—</option>
          <option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }} ({{ s.bin }})</option>
        </select>
      </div>
      <div class="grid-2">
        <div class="field"><label>{{ $t('offers.bin') }}<span class="req"> *</span></label>
          <input v-model="offer.supplier_bin" class="input" maxlength="12" inputmode="numeric" :class="{ invalid: fieldError('supplier_bin') }" />
          <span v-if="fieldError('supplier_bin')" class="field-error">{{ fieldError('supplier_bin') }}</span></div>
        <div class="field"><label>{{ $t('offers.supplierName') }}<span class="req"> *</span></label><input v-model="offer.supplier_name" class="input" /></div>
        <div class="field"><label>{{ $t('offers.date') }}<span class="req"> *</span></label><input v-model="offer.offer_date" type="date" class="input" :max="today" /></div>
        <div class="field"><label>{{ $t('offers.currency') }}</label>
          <select v-model="offer.currency" class="input"><option v-for="c in currencies" :key="c">{{ c }}</option></select></div>
      </div>
      <label class="checkbox"><input v-model="offer.vat_included" type="checkbox" /> {{ $t('offers.withVat') }}</label>
      <div class="field mt">
        <label>{{ $t('offers.file') }}<span class="req"> *</span> <span class="muted">({{ $t('offers.fileHint') }})</span></label>
        <FileInput :label="$t('offers.file')" @change="(f) => (offer.file = f)" />
      </div>
      <h3>{{ $t('offers.pricesTitle') }}</h3>
      <div v-for="item in analysis.items" :key="item.id" class="price-row">
        <span>{{ item.line_no }}. {{ item.name }} <span class="muted small">{{ qty(item.quantity) }} {{ item.unit }}</span></span>
        <input v-model="offer.prices[item.id]" class="input price-input" inputmode="decimal" :placeholder="`${$t('offers.pricePerUnit')}, ${offer.currency}`" />
      </div>
      <ErrorAlert :error="modalError" />
      <template #footer>
        <button class="btn" @click="uploadOpen = false">{{ $t('common.cancel') }}</button>
        <button class="btn primary" :disabled="busy" @click="uploadOffer">{{ $t('common.save') }}</button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { api } from '../../api'
import BarChart from '../../components/BarChart.vue'
import ErrorAlert from '../../components/ErrorAlert.vue'
import FileInput from '../../components/FileInput.vue'
import Modal from '../../components/Modal.vue'
import { date, money, percent, qty } from '../../format'
import { t } from '../../i18n'

const props = defineProps({ analysis: { type: Object, required: true }, editable: Boolean })
const emit = defineEmits(['refresh', 'updated', 'go'])

const currencies = ['KZT', 'USD', 'EUR', 'RUB', 'CNY']
const today = new Date().toISOString().slice(0, 10)
const busy = ref(false)
const error = ref(null)
const modalError = ref(null)
const notice = ref('')
const stats = ref(null)
const suppliers = ref([])
const requestOpen = ref(false)
const selectedSuppliers = ref([])
const requestMessage = ref('')
const uploadOpen = ref(false)
const justification = ref(props.analysis.price_justification)
const offer = reactive({})

const short = (s) => (s.length > 28 ? `${s.slice(0, 26)}…` : s)
const priceOf = (o, item) => o.prices.find((p) => p.item === item.id)
const fieldError = (field) => modalError.value?.errors?.find((e) => e.field === field)?.message

async function loadStats() {
  if (!props.analysis.offers.length) { stats.value = null; return }
  try { stats.value = await api.analytics(props.analysis.id) } catch (e) { error.value = e }
}

function openUpload() {
  Object.assign(offer, { supplierId: '', supplier_bin: '', supplier_name: '', offer_date: today, currency: 'KZT',
    vat_included: false, file: null, prices: {} })
  modalError.value = null
  uploadOpen.value = true
}

function pickSupplier() {
  const s = suppliers.value.find((x) => x.id === offer.supplierId)
  if (s) { offer.supplier_bin = s.bin; offer.supplier_name = s.name }
}

async function uploadOffer() {
  modalError.value = null
  if (!offer.file) { modalError.value = { status: 400, message: t('common.required'), errors: [{ message: t('offers.file') }] }; return }
  const prices = Object.fromEntries(Object.entries(offer.prices).filter(([, v]) => String(v).trim() !== ''))
  const fd = new FormData()
  fd.append('file', offer.file)
  fd.append('supplier_bin', offer.supplier_bin.trim())
  fd.append('supplier_name', offer.supplier_name.trim())
  fd.append('offer_date', offer.offer_date)
  fd.append('currency', offer.currency)
  fd.append('vat_included', offer.vat_included ? 'true' : 'false')
  fd.append('prices', JSON.stringify(prices))
  busy.value = true
  try {
    await api.addOffer(props.analysis.id, fd)
    uploadOpen.value = false
    emit('refresh')
  } catch (e) {
    modalError.value = e
  } finally {
    busy.value = false
  }
}

async function sendRequests() {
  busy.value = true
  modalError.value = null
  try {
    const res = await api.requestKp(props.analysis.id, selectedSuppliers.value, requestMessage.value)
    notice.value = t('offers.sent', { n: res.sent })
    requestOpen.value = false
    selectedSuppliers.value = []
    emit('refresh')
  } catch (e) {
    modalError.value = e
  } finally {
    busy.value = false
  }
}

async function removeOffer(o) {
  error.value = null
  try { await api.deleteOffer(props.analysis.id, o.id); emit('refresh') } catch (e) { error.value = e }
}

async function calculate() {
  busy.value = true
  error.value = null
  try { emit('updated', await api.calculate(props.analysis.id)) } catch (e) { error.value = e } finally { busy.value = false }
}

async function saveJustification() {
  try { emit('updated', await api.update(props.analysis.id, { price_justification: justification.value })) } catch (e) { error.value = e }
}

watch(() => props.analysis, loadStats)
onMounted(async () => {
  loadStats()
  if (props.editable) {
    try { suppliers.value = await api.suppliers() } catch { /* пул недоступен — ручной ввод */ }
  }
})
</script>

<style scoped>
.toolbar { margin-bottom: 14px; }
.file-link { display: inline-block; margin-top: 2px; max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.an-item { border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; margin-top: 12px; }
.an-grid { display: grid; grid-template-columns: 1.6fr 1fr; gap: 24px; }
@media (max-width: 900px) { .an-grid { grid-template-columns: 1fr; } }
.kv { display: grid; grid-template-columns: auto 1fr; gap: 6px 14px; margin: 0; font-size: 13px; }
.kv dt { color: var(--text-muted); }
.kv dd { margin: 0; text-align: right; font-variant-numeric: tabular-nums; }
.history { margin-top: 10px; }
.history summary { cursor: pointer; color: var(--price-blue); }
.small-table { margin-top: 8px; font-size: 13px; }
.supplier-list { display: flex; flex-direction: column; gap: 8px; max-height: 260px; overflow: auto; }
.price-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 8px; }
.price-input { width: 180px; text-align: right; }
</style>
