<template>
  <div>
    <div v-if="editable" class="add-box">
      <h3>{{ $t('items.addItem') }}</h3>
      <div class="add-grid">
        <div class="field product">
          <label>{{ $t('items.search') }}<span class="req"> *</span></label>
          <div v-if="draft.product" class="picked">
            <div><b>{{ draft.product.nsi_code }}</b> {{ draft.product.name }}
              <div class="small muted">{{ $t('items.enstru') }}: {{ draft.product.enstru_code || '—' }} · {{ draft.product.unit }} · {{ draft.product.short_description }}</div>
            </div>
            <button class="icon-btn" @click="draft.product = null">✕</button>
          </div>
          <Autocomplete v-else :fetcher="api.searchProducts" :item-label="(p) => `${p.nsi_code} — ${p.name}`"
            :item-sub="(p) => `${p.enstru_code || ''} · ${p.unit}`" :placeholder="$t('items.searchPh')"
            @select="(p) => (draft.product = p)" />
        </div>
        <div class="field"><label>{{ $t('items.quantity') }}<span class="req"> *</span></label><input v-model="draft.quantity" class="input" inputmode="decimal" /></div>
        <div class="field"><label>{{ $t('items.place') }}</label><input v-model="draft.delivery_place" class="input" /></div>
        <div class="field"><label>{{ $t('items.term') }}</label><input v-model="draft.delivery_term" class="input" /></div>
        <div class="field"><label>&nbsp;</label><button class="btn primary" :disabled="!draft.product || !draft.quantity || busy" @click="add">{{ $t('common.add') }}</button></div>
      </div>
    </div>
    <ErrorAlert :error="error" />

    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>№</th><th>{{ $t('items.nsiCode') }}<span class="sub">{{ $t('items.enstru') }}</span></th>
            <th>{{ $t('items.name') }}</th><th>{{ $t('items.unit') }}</th><th class="num">{{ $t('items.quantity') }}</th>
            <th>{{ $t('items.place') }}</th><th>{{ $t('items.term') }}</th><th>{{ $t('items.attachments') }}</th><th v-if="editable" />
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in analysis.items" :key="item.id">
            <td>{{ item.line_no }}</td>
            <td class="nowrap">{{ item.nsi_code }}<span class="sub">{{ item.enstru_code }}</span></td>
            <td>{{ item.name }}<span class="sub">{{ item.characteristics }}</span></td>
            <td>{{ item.unit }}</td>
            <td class="num">
              <input v-if="editable" class="input cell num-input" :value="item.quantity" @change="(e) => patch(item, { quantity: e.target.value })" />
              <template v-else>{{ qty(item.quantity) }}</template>
            </td>
            <td>
              <input v-if="editable" class="input cell" :value="item.delivery_place" @change="(e) => patch(item, { delivery_place: e.target.value })" />
              <template v-else>{{ item.delivery_place || '—' }}</template>
            </td>
            <td>
              <input v-if="editable" class="input cell" :value="item.delivery_term" @change="(e) => patch(item, { delivery_term: e.target.value })" />
              <template v-else>{{ item.delivery_term || '—' }}</template>
            </td>
            <td>
              <div v-for="att in item.attachments" :key="att.id" class="att">
                <a :href="api.attachmentUrl(analysis.id, item.id, att.id)">{{ att.original_name }}</a>
                <button v-if="editable" class="icon-btn" @click="removeAttachment(item, att)">✕</button>
              </div>
              <FileInput v-if="editable" :label="$t('items.attach')" :show-name="false" @change="(f) => upload(item, f)" />
            </td>
            <td v-if="editable"><button class="icon-btn" :title="$t('common.delete')" @click="remove(item)">🗑</button></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="!analysis.items.length" class="empty-state">{{ $t('items.empty') }}</div>
    <div v-if="editable" class="row mt">
      <button class="btn" @click="$emit('go', 0)">{{ $t('common.back') }}</button>
      <div class="spacer" />
      <button class="btn primary" :disabled="!analysis.items.length" @click="$emit('go', 2)">{{ $t('common.next') }}</button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { api } from '../../api'
import Autocomplete from '../../components/Autocomplete.vue'
import ErrorAlert from '../../components/ErrorAlert.vue'
import FileInput from '../../components/FileInput.vue'
import { qty } from '../../format'

const props = defineProps({ analysis: { type: Object, required: true }, editable: Boolean })
const emit = defineEmits(['refresh', 'go'])
const draft = reactive({ product: null, quantity: '', delivery_place: '', delivery_term: '' })
const busy = ref(false)
const error = ref(null)

async function run(fn) {
  busy.value = true
  error.value = null
  try {
    await fn()
    emit('refresh')
  } catch (e) {
    error.value = e
  } finally {
    busy.value = false
  }
}

const add = () => run(async () => {
  await api.addItem(props.analysis.id, { nsi_product: draft.product.id, quantity: draft.quantity,
    delivery_place: draft.delivery_place, delivery_term: draft.delivery_term })
  Object.assign(draft, { product: null, quantity: '' })
})
const patch = (item, data) => run(() => api.updateItem(props.analysis.id, item.id, data))
const remove = (item) => run(() => api.deleteItem(props.analysis.id, item.id))
const upload = (item, file) => run(() => api.addAttachment(props.analysis.id, item.id, file))
const removeAttachment = (item, att) => run(() => api.deleteAttachment(props.analysis.id, item.id, att.id))
</script>

<style scoped>
.add-box { background: var(--price-blue-lighter); border-radius: var(--radius); padding: 14px 16px 2px; margin-bottom: 16px; }
.add-grid { display: grid; grid-template-columns: 2.4fr 0.8fr 1.2fr 1fr auto; gap: 12px; align-items: start; }
@media (max-width: 1000px) { .add-grid { grid-template-columns: 1fr; } }
.picked { display: flex; justify-content: space-between; align-items: center; border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 6px 10px; background: #fff; }
.cell { height: 32px; min-width: 110px; }
.num-input { width: 100px; text-align: right; }
.att { display: flex; align-items: center; gap: 4px; font-size: 13px; }
</style>
