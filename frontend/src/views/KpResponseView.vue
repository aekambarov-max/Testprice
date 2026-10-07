<template>
  <div class="kp-page">
    <div class="kp card">
      <div class="brand"><b>Price</b> · {{ $t('app.title') }}</div>
      <h1>{{ $t('kp.title') }}</h1>
      <div v-if="loadError" class="alert error">{{ errorText(loadError) }}</div>
      <div v-else-if="done" class="alert success">{{ $t('kp.done') }}</div>
      <template v-else-if="req">
        <p><b>{{ req.supplier }}</b></p>
        <p v-if="req.message" class="muted">{{ req.message }}</p>
        <div class="grid-2">
          <div class="field"><label>{{ $t('offers.date') }}</label><input v-model="form.offer_date" type="date" class="input" /></div>
          <div class="field"><label>{{ $t('offers.currency') }}</label>
            <select v-model="form.currency" class="input"><option v-for="c in ['KZT', 'USD', 'EUR', 'RUB', 'CNY']" :key="c">{{ c }}</option></select></div>
        </div>
        <label class="checkbox"><input v-model="form.vat_included" type="checkbox" /> {{ $t('offers.withVat') }}</label>
        <table class="table mt">
          <thead><tr><th>{{ $t('items.name') }}</th><th class="num">{{ $t('items.quantity') }}</th><th>{{ $t('offers.pricePerUnit') }}</th></tr></thead>
          <tbody>
            <tr v-for="item in req.items" :key="item.item_id">
              <td>{{ item.name }}<span class="sub">{{ item.nsi_code }} · {{ item.characteristics }}</span></td>
              <td class="num">{{ item.quantity }} {{ item.unit }}</td>
              <td><input v-model="form.prices[item.item_id]" class="input" inputmode="decimal" /></td>
            </tr>
          </tbody>
        </table>
        <div class="field mt"><label>{{ $t('offers.file') }} ({{ $t('offers.fileHint') }})</label><FileInput :label="$t('offers.file')" @change="(f) => (form.file = f)" /></div>
        <ErrorAlert :error="error" />
        <button class="btn primary" :disabled="busy || !form.file" @click="send">{{ $t('kp.submit') }}</button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import ErrorAlert from '../components/ErrorAlert.vue'
import FileInput from '../components/FileInput.vue'
import { errorText } from '../i18n'

const route = useRoute()
const req = ref(null)
const loadError = ref(null)
const error = ref(null)
const busy = ref(false)
const done = ref(false)
const form = reactive({ offer_date: new Date().toISOString().slice(0, 10), currency: 'KZT', vat_included: false, prices: {}, file: null })

onMounted(async () => {
  try { req.value = await api.kpRequest(route.params.token) } catch (e) { loadError.value = e }
})

async function send() {
  const fd = new FormData()
  fd.append('file', form.file)
  fd.append('offer_date', form.offer_date)
  fd.append('currency', form.currency)
  fd.append('vat_included', form.vat_included ? 'true' : 'false')
  fd.append('prices', JSON.stringify(Object.fromEntries(Object.entries(form.prices).filter(([, v]) => String(v).trim()))))
  busy.value = true
  error.value = null
  try { await api.kpRespond(route.params.token, fd); done.value = true } catch (e) { error.value = e } finally { busy.value = false }
}
</script>

<style scoped>
.kp-page { min-height: 100vh; padding: 40px 16px; }
.kp { max-width: 820px; margin: 0 auto; }
.brand { color: var(--price-blue); margin-bottom: 8px; }
</style>
