<template>
  <div class="doc">
    <div class="doc-head">
      <span class="doc-logo">P</span>
      <span class="small muted">ИС «Price» · Маркетинг цен<br>Документ сформирован автоматически</span>
    </div>
    <h2 class="doc-title">МАРКЕТИНГОВОЕ ЗАКЛЮЧЕНИЕ № {{ analysis.number }}</h2>
    <div class="center small">от {{ date(analysis.approved_at) }}</div>
    <dl class="info">
      <dt>ДЗО</dt><dd>{{ analysis.dzo.name_ru }}</dd>
      <dt>Инициатор потребности</dt><dd>{{ analysis.initiator }}</dd>
      <dt>Маркетолог</dt><dd>{{ analysis.author_name }}</dd>
      <dt>Методика расчёта</dt><dd>среднее арифметическое цен КП; цены приведены к KZT по курсу НБ РК на дату КП, без НДС (16%)</dd>
    </dl>
    <h3>1. Позиции</h3>
    <div class="table-wrap">
      <table class="table compact">
        <thead><tr><th>№</th><th>Код АСУ НСИ</th><th>Код ЕНС ТРУ</th><th>Наименование</th><th>Ед.</th><th class="num">Кол-во</th><th class="num">Цена за ед. без НДС, KZT</th><th class="num">Сумма без НДС, KZT</th></tr></thead>
        <tbody>
          <tr v-for="i in analysis.items" :key="i.id"><td>{{ i.line_no }}</td><td>{{ i.nsi_code }}</td><td>{{ i.enstru_code }}</td><td>{{ i.name }}</td><td>{{ i.unit }}</td>
            <td class="num">{{ qty(i.quantity) }}</td><td class="num">{{ money(i.marketing_price) }}</td><td class="num">{{ money(i.total_wo_vat) }}</td></tr>
        </tbody>
        <tfoot><tr><td colspan="7">Итого без НДС, KZT</td><td class="num">{{ money(analysis.total_wo_vat) }}</td></tr></tfoot>
      </table>
    </div>
    <h3>2. Коммерческие предложения</h3>
    <div class="table-wrap">
      <table class="table compact">
        <thead><tr><th>Поставщик</th><th>БИН</th><th>Дата КП</th><th>Позиция</th><th class="num">Цена за ед.</th><th>Валюта</th><th>НДС</th><th class="num">Курс НБ РК</th><th class="num">KZT без НДС</th></tr></thead>
        <tbody>
          <template v-for="o in analysis.offers" :key="o.id">
            <tr v-for="p in o.prices" :key="p.item"><td>{{ o.supplier_name }}</td><td>{{ o.supplier_bin }}</td><td>{{ date(o.offer_date) }}</td><td>{{ itemName(p.item) }}</td>
              <td class="num">{{ money(p.price) }}</td><td>{{ o.currency }}</td><td>{{ o.vat_included ? 'с НДС' : 'без НДС' }}</td><td class="num">{{ o.exchange_rate }}</td><td class="num">{{ money(p.price_kzt_wo_vat) }}</td></tr>
          </template>
        </tbody>
      </table>
    </div>
    <h3>3. Итоговая сумма и обоснование цены</h3>
    <p><b>Итоговая сумма без НДС: {{ money(analysis.total_wo_vat) }} KZT.</b></p>
    <p v-if="analysis.price_justification">{{ analysis.price_justification }}</p>
    <h3>4. Лист согласования</h3>
    <div class="table-wrap">
      <table class="table compact">
        <thead><tr><th>Этап</th><th>ФИО</th><th>Должность</th><th>Решение</th><th>Дата и время</th><th>Комментарий</th></tr></thead>
        <tbody>
          <tr v-for="s in approved" :key="s.id"><td>{{ s.stage_display }}</td><td>{{ s.decided_by_name }}</td><td>{{ s.decided_by_position }}</td>
            <td>{{ s.stage === 3 ? 'Утверждено' : 'Согласовано' }}</td><td class="nowrap">{{ datetime(s.decided_at) }}</td><td>{{ s.comment }}</td></tr>
        </tbody>
      </table>
    </div>
    <div v-if="final" class="final"><b>УТВЕРЖДЕНО:</b> {{ final.decided_by_position }} {{ final.decided_by_name }} — {{ datetime(final.decided_at) }}</div>
    <p class="small muted sha">SHA-256: {{ analysis.pdf_sha256 }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { date, datetime, money, qty } from '../format'

const props = defineProps({ analysis: { type: Object, required: true } })
const approved = computed(() => props.analysis.route.filter((s) => s.status === 'approved'))
const final = computed(() => approved.value.find((s) => s.stage === 3))
const itemName = (id) => { const i = props.analysis.items.find((x) => x.id === id); return i ? `${i.line_no}. ${i.name}` : '' }
</script>

<style scoped>
.doc { font-size: 13px; }
.doc-head { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--price-blue); padding-bottom: 8px; }
.doc-logo { width: 34px; height: 34px; border-radius: 7px; background: var(--price-blue); color: #fff; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; }
.doc-head .small { text-align: right; }
.doc-title { text-align: center; color: var(--price-blue); margin: 14px 0 2px; font-size: 17px; }
.center { text-align: center; margin-bottom: 12px; }
.info { display: grid; grid-template-columns: minmax(120px, 220px) 1fr; gap: 4px 12px; margin: 0 0 8px; }
.info dt { color: var(--text-muted); }
.info dd { margin: 0; }
h3 { color: var(--price-blue); margin: 16px 0 6px; font-size: 14px; }
.compact th, .compact td { padding: 6px 8px; font-size: 12px; }
.final { margin-top: 10px; padding: 8px 10px; border: 1px solid var(--price-blue); background: var(--price-blue-lighter); border-radius: 4px; }
.sha { word-break: break-all; margin-top: 12px; }
</style>
