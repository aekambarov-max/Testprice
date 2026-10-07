// Имитатор backend для кликабельного демо. Повторяет логику apps/marketing_analysis на сервере:
// статусы и переходы, права и available_actions, расчёт маркетинговой цены, маршрут согласования,
// каталог цен, уведомления и журнал. Данные хранятся только в браузере зрителя.

const STORAGE_KEY = 'price-demo-v1'
const PASSWORD = 'Demo12345!'
export const DEMO_PASSWORD = PASSWORD
const VAT = 16
const MIN_KP = 1
const DEVIATION_THRESHOLD = 15
const RATES = { KZT: 1, USD: 505.2, EUR: 590.4, RUB: 6.25, CNY: 70.8 }
const ALLOWED_EXT = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png']

const ROLE_TITLES = {
  marketer: 'Маркетолог (Ответственный за маркетинг цен ДЗО)',
  db_specialist: 'Специалист ДБ Холдинга',
  db_director: 'Директор ДБ Холдинга',
  ma_admin: 'Администратор',
}
const STAGE_LABELS = { 1: 'Согласующие ДЗО', 2: 'Департамент бюджетирования Холдинга', 3: 'Директор департамента бюджетирования Холдинга' }
const STAGE_STATUS = { 1: 'on_approval_dzo', 2: 'on_approval_db', 3: 'on_final_approval' }
const STAGE_ROLE = { 2: 'db_specialist', 3: 'db_director' }
const STATUS_LABELS = {
  draft: 'Черновик', collecting_kp: 'Сбор КП', on_approval_dzo: 'На согласовании (ДЗО)', on_approval_db: 'На согласовании ДБ Холдинга',
  on_final_approval: 'На утверждении директора ДБ Холдинга', rework: 'На доработке', approved: 'Утверждено', cancelled: 'Аннулировано',
}
const STEP_LABELS = { waiting: 'Ожидает очереди', pending: 'На рассмотрении', approved: 'Согласовано', returned: 'Возвращено на доработку', skipped: 'Не рассматривалось' }
const EDITABLE = ['draft', 'collecting_kp', 'rework']
const ON_APPROVAL = ['on_approval_dzo', 'on_approval_db', 'on_final_approval']
const TRANSITIONS = {
  draft: ['collecting_kp', 'cancelled'],
  collecting_kp: ['on_approval_dzo', 'on_approval_db', 'cancelled'],
  on_approval_dzo: ['on_approval_db', 'rework'],
  on_approval_db: ['on_final_approval', 'rework'],
  on_final_approval: ['approved', 'rework'],
  rework: ['on_approval_dzo', 'on_approval_db', 'on_final_approval', 'cancelled'],
  approved: [], cancelled: [],
}

export const DEMO_USERS = [
  { id: 1, username: 'marketer', last: 'Ахметова', first: 'Динара', middle: 'Серикболовна', position: 'Ответственный за маркетинг цен', department: 'Отдел закупок', dzo: 1, roles: ['marketer'], hint: 'Маркетолог: создаёт анализ' },
  { id: 2, username: 'approver1', last: 'Нурланов', first: 'Ерлан', middle: 'Каиргалиевич', position: 'Начальник отдела МТО', department: 'Отдел МТО', dzo: 1, roles: [], hint: 'Согласующий ДЗО (этап 1)' },
  { id: 3, username: 'approver2', last: 'Сейткалиева', first: 'Айгерим', middle: 'Маратовна', position: 'Главный экономист', department: 'Планово-экономический отдел', dzo: 1, roles: [], hint: 'Согласующий ДЗО (этап 1)' },
  { id: 5, username: 'db_specialist', last: 'Касымова', first: 'Гульнар', middle: 'Ертаевна', position: 'Главный специалист ДБ', department: 'Департамент бюджетирования', dzo: 4, roles: ['db_specialist'], hint: 'Специалист ДБ (этап 2)' },
  { id: 6, username: 'db_director', last: 'Тлеуов', first: 'Бауыржан', middle: 'Кайратович', position: 'Директор департамента бюджетирования', department: 'Департамент бюджетирования', dzo: 4, roles: ['db_director'], hint: 'Директор ДБ (этап 3, утверждение)' },
  { id: 7, username: 'ma_admin', last: 'Администратор', first: 'Системы', middle: '', position: 'Администратор ИС Price', department: 'ДИТ', dzo: 4, roles: ['ma_admin'], hint: 'Администратор: видит всё' },
  { id: 4, username: 'initiator', last: 'Жумабаев', first: 'Арман', middle: 'Болатович', position: 'Главный механик', department: 'Управление добычи', dzo: 1, roles: [], hint: 'Инициатор потребности' },
  { id: 9, username: 'approver3', last: 'Оспанов', first: 'Даурен', middle: 'Маратович', position: 'Главный инженер', department: 'Техническая служба', dzo: 1, roles: [], hint: 'Сотрудник ДЗО' },
  { id: 8, username: 'marketer2', last: 'Иманова', first: 'Салтанат', middle: 'Ерболовна', position: 'Ответственный за маркетинг цен', department: 'Отдел закупок', dzo: 2, roles: ['marketer'], hint: 'Маркетолог другого ДЗО' },
]

const DZOS = [
  { id: 1, code: 'BTS', name_ru: 'ДЗО «Батыс» (демо)', name_kk: '«Батыс» ЕТҰ (демо)' },
  { id: 2, code: 'SHG', name_ru: 'ДЗО «Шығыс» (демо)', name_kk: '«Шығыс» ЕТҰ (демо)' },
  { id: 3, code: 'ONT', name_ru: 'ДЗО «Оңтүстік» (демо)', name_kk: '«Оңтүстік» ЕТҰ (демо)' },
  { id: 4, code: 'KC', name_ru: 'Корпоративный центр Холдинга (демо)', name_kk: 'Холдингтің корпоративтік орталығы (демо)' },
]

const PRODUCTS = [
  [1, '1010101001', '222011.100.000001', 'Труба стальная бесшовная 89х6 мм', 'ГОСТ 8732-78, сталь 20', 'м'],
  [2, '1010101002', '222011.100.000002', 'Труба насосно-компрессорная 73х5,5 мм', 'ГОСТ 633-80, группа прочности Д', 'м'],
  [3, '2020202001', '281314.300.000010', 'Насос штанговый скважинный НН2Б-44', 'Для добычи нефти, ход 3 м', 'шт'],
  [4, '2020202002', '281314.300.000011', 'Штанга насосная ШН-22', 'Сталь 20Н2М, длина 8 м', 'шт'],
  [5, '3030303001', '192029.900.000005', 'Масло моторное 10W-40', 'Канистра 20 л, API CI-4', 'л'],
  [6, '3030303002', '201513.500.000001', 'Ингибитор коррозии', 'Для нефтепромысловых сред', 'кг'],
  [7, '4040404001', '141210.000.000015', 'Костюм рабочий летний', 'Хлопок 100%, СИЗ, со световозвращающими полосами', 'компл'],
  [8, '4040404002', '152012.000.000003', 'Ботинки кожаные с металлическим подноском', 'ГОСТ 28507-90', 'пара'],
].map(([id, nsi_code, enstru_code, name, short_description, unit]) => ({ id, nsi_code, enstru_code, name, short_description, unit }))

const SUPPLIERS = [
  [1, '050140000011', 'ТОО «ТрубСнаб» (демо)', 'sales@trubsnab.example'],
  [2, '060240000027', 'ТОО «НефтеМаш Сервис» (демо)', 'kp@neftemash.example'],
  [3, '070340000032', 'ТОО «Каспий Ойл Сервис» (демо)', 'offers@caspianos.example'],
  [4, '080440000048', 'ТОО «Спецодежда» (демо)', 'tender@spec.example'],
  [5, '090540000053', 'ТОО «Мунай Химия» (демо)', 'info@munaychem.example'],
].map(([id, bin, name, email]) => ({ id, bin, name, email }))

// ---------------------------------------------------------------- состояние

let state = null
let fakeNow = null
const nowDate = () => (fakeNow ? new Date(fakeNow) : new Date())
const nowIso = () => nowDate().toISOString()
const today = () => nowDate().toISOString().slice(0, 10)
const daysAgo = (d, h = 10) => { const x = new Date(); x.setDate(x.getDate() - d); x.setHours(h, 15, 0, 0); return x }

function save() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)) } catch { /* хранилище недоступно — демо работает в памяти */ }
}

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) { state = JSON.parse(raw); return true }
  } catch { /* нет доступа к хранилищу */ }
  return false
}

export function resetDemo() {
  try { localStorage.removeItem(STORAGE_KEY) } catch { /* ignore */ }
  state = null
  init()
}

function nextId(kind) { state.seq[kind] = (state.seq[kind] || 0) + 1; return state.seq[kind] }

class MockError extends Error {
  constructor(status, data) { super(data.detail); this.status = status; this.data = data }
}
const fail = (status, code, detail, errors = []) => { throw new MockError(status, { code, detail, errors }) }
const forbidden = () => fail(403, undefined, 'У вас недостаточно прав для выполнения данного действия.')
const notFound = () => fail(404, undefined, 'Не найдено.')

// ---------------------------------------------------------------- пользователи и права

const userById = (id) => DEMO_USERS.find((u) => u.id === id)
const fullName = (u) => (u ? [u.last, u.first, u.middle].filter(Boolean).join(' ') : '')
const dzoById = (id) => DZOS.find((d) => d.id === id)
const me = () => (state.currentUserId ? userById(state.currentUserId) : null)
const isAdmin = (u) => u.roles.includes('ma_admin')
const hasRole = (u, r) => u.roles.includes(r)
const marketerDzoIds = (u) => (isAdmin(u) ? DZOS.map((d) => d.id) : [u.dzo])

function userShort(u) {
  if (!u) return null
  return { id: u.id, username: u.username, full_name: fullName(u), position: u.position, department: u.department, dzo: dzoById(u.dzo) }
}

function visible(u, a) {
  if (['ma_admin', 'db_specialist', 'db_director'].some((r) => hasRole(u, r))) return true
  if (a.steps.some((s) => s.assignee_user === u.id) || a.approvers.includes(u.id)) return true
  return hasRole(u, 'marketer') && marketerDzoIds(u).includes(a.dzo)
}

const canEdit = (u, a) => EDITABLE.includes(a.status) && hasRole(u, 'marketer') && marketerDzoIds(u).includes(a.dzo)
const currentStep = (a) => (ON_APPROVAL.includes(a.status) ? a.steps.find((s) => s.iteration === a.iteration && s.status === 'pending') : null)
const isExecutor = (u, step) => !!step && (step.assignee_user ? step.assignee_user === u.id : hasRole(u, step.assignee_role))

function availableActions(u, a) {
  const actions = []
  if (canEdit(u, a)) {
    actions.push('edit', 'manage_items', 'request_kp', 'upload_offer', 'calculate', 'set_approvers')
    if (a.status === 'draft') actions.push('start_collecting', 'delete')
    if (['collecting_kp', 'rework'].includes(a.status)) actions.push('submit')
    actions.push('cancel')
  }
  if (ON_APPROVAL.includes(a.status) && isExecutor(u, currentStep(a))) actions.push('approve', 'rework')
  if (a.status === 'approved') actions.push('download_pdf')
  return actions
}

// ---------------------------------------------------------------- сериализация

const money = (v) => Math.round(Number(v) * 100) / 100
const initiatorDisplay = (a) => (a.initiator_user ? fullName(userById(a.initiator_user)) : a.initiator_full_name)

function stepOut(s) {
  return {
    id: s.id, iteration: s.iteration, stage: s.stage, stage_display: STAGE_LABELS[s.stage], order: s.order,
    assignee: s.assignee_user ? fullName(userById(s.assignee_user)) : ROLE_TITLES[s.assignee_role],
    assignee_role: s.assignee_role || '', status: s.status, status_display: STEP_LABELS[s.status],
    decided_by_name: s.decided_by_name || '', decided_by_position: s.decided_by_position || '', comment: s.comment || '',
    activated_at: s.activated_at, decided_at: s.decided_at,
  }
}

function listOut(a) {
  return {
    id: a.id, number: a.number, status: a.status, status_display: STATUS_LABELS[a.status], dzo: dzoById(a.dzo),
    author_name: fullName(userById(a.author)), initiator: initiatorDisplay(a), created_at: a.created_at,
    submitted_at: a.submitted_at, approved_at: a.approved_at, total_wo_vat: a.total_wo_vat,
    items_count: a.items.length, first_item_name: a.items[0]?.name || null, current_stage: a.current_stage,
  }
}

function detailOut(u, a) {
  const step = currentStep(a)
  return {
    ...listOut(a),
    initiator_user: userShort(userById(a.initiator_user)),
    initiator_full_name: a.initiator_full_name, initiator_position: a.initiator_position, initiator_department: a.initiator_department,
    price_justification: a.price_justification, iteration: a.iteration, returned_from_stage: a.returned_from_stage,
    cancelled_at: a.cancelled_at, updated_at: a.updated_at,
    items: a.items.map((i) => ({ ...i, attachments: i.attachments.map(({ id, original_name, uploaded_at }) => ({ id, original_name, uploaded_at })),
      offers_count: a.offers.filter((o) => o.prices.some((p) => p.item === i.id)).length })),
    offers: a.offers.map((o) => ({ ...o, exchange_rate: Number(o.exchange_rate).toFixed(4) })),
    approvers: a.approvers.map((id, i) => ({ order: i + 1, user: userShort(userById(id)) })),
    route: a.iteration ? a.steps.filter((s) => s.iteration === a.iteration).map(stepOut) : [],
    current_step_id: step ? step.id : null,
    available_actions: availableActions(u, a),
    fixed_stages: [
      { stage: 2, title: STAGE_LABELS[2], assignee: ROLE_TITLES.db_specialist },
      { stage: 3, title: STAGE_LABELS[3], assignee: ROLE_TITLES.db_director },
    ],
    pdf_status: a.pdf_status, pdf_sha256: a.pdf_sha256, pdf_generated_at: a.pdf_generated_at,
    pdf_name: `Маркетинговое_заключение_${a.number}.pdf`,
  }
}

// ---------------------------------------------------------------- сервисы

function audit(a, action, { from = '', to = '', comment = '', user } = {}) {
  a.audit.push({ id: nextId('audit'), created_at: nowIso(), user: user === undefined ? state.currentUserId : user, action, from_status: from, to_status: to, comment })
  a.updated_at = nowIso()
}

function notify(userIds, event, title, body, a) {
  ;[...new Set(userIds.filter(Boolean))].forEach((uid) => {
    state.notifications.unshift({ id: nextId('notif'), user: uid, event, title, body, link: `/marketing-analyses/${a.id}`, is_read: false, created_at: nowIso() })
  })
}

function transition(a, to, action, opts = {}) {
  if (!TRANSITIONS[a.status].includes(to)) fail(400, 'transition_forbidden', `Переход ${a.status} → ${to} запрещён`)
  const from = a.status
  a.status = to
  audit(a, action, { from, to, ...opts })
}

function expect(a, statuses) {
  if (!statuses.includes(a.status)) fail(409, 'status_changed', `Действие недоступно: анализ уже в статусе «${STATUS_LABELS[a.status]}». Обновите страницу.`)
}

function editable(a) {
  expect(a, EDITABLE)
  if (!canEdit(me(), a)) forbidden()
}

function executors(step) {
  return step.assignee_user ? [step.assignee_user] : DEMO_USERS.filter((u) => u.roles.includes(step.assignee_role)).map((u) => u.id)
}

function notifyStep(a, step) {
  notify(executors(step), 'ma_step_assigned', `Маркетинговый анализ ${a.number} ожидает вашего решения`,
    `Этап: ${STAGE_LABELS[step.stage]}. ДЗО: ${dzoById(a.dzo).name_ru}.`, a)
}

function recalcTotal(a) {
  a.total_wo_vat = a.items.length && a.items.every((i) => i.total_wo_vat !== null) ? money(a.items.reduce((s, i) => s + i.total_wo_vat, 0)) : null
}

function invalidate(a, itemIds) {
  a.items.filter((i) => itemIds.includes(i.id)).forEach((i) => { i.marketing_price = null; i.total_wo_vat = null; i.calc_method = '' })
  recalcTotal(a)
}

function isValidBin(v) {
  if (!/^\d{12}$/.test(v)) return false
  const d = [...v].map(Number)
  const w1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
  const w2 = [3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2]
  let c = w1.reduce((s, w, i) => s + w * d[i], 0) % 11
  if (c === 10) { c = w2.reduce((s, w, i) => s + w * d[i], 0) % 11; if (c === 10) return false }
  return c === d[11]
}

const parseNum = (v) => {
  const n = Number(String(v ?? '').replace(',', '.').replace(/\s/g, ''))
  return Number.isFinite(n) ? n : NaN
}

function checkFile(name) {
  if (!name) fail(400, 'file_required', 'Приложите файл', [{ field: 'file', code: 'file_required', message: 'Приложите файл' }])
  const ext = name.split('.').pop().toLowerCase()
  if (!ALLOWED_EXT.includes(ext)) fail(400, 'file_type', `Недопустимый тип файла. Разрешены: ${ALLOWED_EXT.join(', ').toUpperCase()}`, [{ field: 'file', code: 'file_type', message: 'Недопустимый тип файла' }])
}

function createOffer(a, data, source = 'manual') {
  checkFile(data.fileName)
  const supplier = SUPPLIERS.find((s) => s.bin === (data.supplier_bin || '').trim())
  const bin = (data.supplier_bin || '').trim()
  if (!isValidBin(bin)) fail(400, 'invalid_bin', 'Некорректный БИН поставщика (12 цифр, контрольный разряд)', [{ field: 'supplier_bin', code: 'invalid_bin', message: 'Некорректный БИН' }])
  const name = (data.supplier_name || supplier?.name || '').trim()
  if (!name) fail(400, 'supplier_name_required', 'Укажите наименование поставщика', [{ field: 'supplier_name', code: 'required', message: 'Укажите поставщика' }])
  if (!data.offer_date) fail(400, 'offer_date_required', 'Укажите дату КП')
  if (data.offer_date > today()) fail(400, 'offer_date_future', 'Дата КП не может быть в будущем')
  const currency = (data.currency || 'KZT').toUpperCase()
  const rate = RATES[currency]
  if (!rate) fail(400, 'rate_missing', `Нет курса НБ РК для ${currency} на ${data.offer_date}`)
  const vat = ['true', '1', 'on', true].includes(data.vat_included)
  const prices = typeof data.prices === 'string' ? JSON.parse(data.prices || '{}') : data.prices || {}
  const entries = Object.entries(prices).filter(([, v]) => String(v).trim() !== '')
  if (!entries.length) fail(400, 'prices_required', 'Укажите цену хотя бы по одной позиции', [{ field: 'prices', code: 'required', message: 'Укажите цены' }])
  const offer = {
    id: nextId('offer'), supplier: supplier?.id || null, supplier_name: name, supplier_bin: bin, offer_date: data.offer_date,
    currency, exchange_rate: rate, vat_included: vat, original_name: data.fileName, source, created_at: nowIso(), prices: [],
  }
  for (const [itemId, raw] of entries) {
    const item = a.items.find((i) => i.id === Number(itemId))
    if (!item) fail(400, 'unknown_items', 'Цены указаны для позиций, которых нет в анализе')
    const price = parseNum(raw)
    if (!(price > 0)) fail(400, 'must_be_positive', 'Цена должна быть больше нуля', [{ field: `prices.${itemId}`, code: 'must_be_positive', message: 'Должно быть больше нуля' }])
    const kzt = vat ? (price * rate) / (1 + VAT / 100) : price * rate
    offer.prices.push({ item: item.id, price: money(price), price_kzt_wo_vat: money(kzt) })
  }
  a.offers.push(offer)
  invalidate(a, offer.prices.map((p) => p.item))
  return offer
}

function validateForSubmit(a) {
  const errors = []
  if (!initiatorDisplay(a)) errors.push({ field: 'initiator', code: 'initiator_required', message: 'Не указан инициатор потребности' })
  if (!a.items.length) errors.push({ field: 'items', code: 'items_required', message: 'Добавьте хотя бы одну позицию' })
  for (const item of a.items) {
    const n = a.offers.filter((o) => o.prices.some((p) => p.item === item.id)).length
    if (n < MIN_KP) errors.push({ field: 'offers', item_id: item.id, code: 'not_enough_offers', message: `Позиция ${item.line_no} (${item.name}): загружено КП ${n}, требуется не менее ${MIN_KP}` })
    if (item.marketing_price === null) errors.push({ field: 'calculation', item_id: item.id, code: 'price_not_calculated', message: `Позиция ${item.line_no} (${item.name}): не рассчитана маркетинговая цена` })
  }
  if (!a.approvers.length) errors.push({ field: 'approvers', code: 'approvers_required', message: 'Выберите хотя бы одного согласующего этапа 1' })
  return errors
}

function catalogAverage(nsi, excludeId) {
  const list = state.catalog.filter((e) => e.nsi_code === nsi && e.is_active && e.source_id !== excludeId)
  if (!list.length) return [null, 0]
  return [money(list.reduce((s, e) => s + e.price_wo_vat, 0) / list.length), list.length]
}

function analytics(a) {
  const items = a.items.map((item) => {
    const offers = a.offers.flatMap((o) => o.prices.filter((p) => p.item === item.id).map((p) => ({
      offer_id: o.id, supplier_name: o.supplier_name, supplier_bin: o.supplier_bin, price: p.price, currency: o.currency,
      vat_included: o.vat_included, price_kzt_wo_vat: p.price_kzt_wo_vat,
    })))
    const values = offers.map((o) => o.price_kzt_wo_vat)
    const [kmg, n] = catalogAverage(item.nsi_code, `ma-${a.id}`)
    const deviation = item.marketing_price !== null && kmg ? money(((item.marketing_price - kmg) / kmg) * 100) : null
    const history = state.catalog.filter((e) => e.nsi_code === item.nsi_code && e.source_id !== `ma-${a.id}`)
      .sort((x, y) => y.approved_at.localeCompare(x.approved_at)).slice(0, 10)
      .map((e) => ({ dzo: dzoById(e.dzo).name_ru, dzo_code: dzoById(e.dzo).code, price_wo_vat: e.price_wo_vat, approved_at: e.approved_at, source_number: e.source_number, is_active: e.is_active }))
    return {
      item_id: item.id, line_no: item.line_no, nsi_code: item.nsi_code, name: item.name, unit: item.unit, quantity: item.quantity, offers,
      min: values.length ? Math.min(...values) : null, max: values.length ? Math.max(...values) : null,
      average: values.length ? money(values.reduce((s, v) => s + v, 0) / values.length) : null,
      marketing_price: item.marketing_price, total_wo_vat: item.total_wo_vat, kmg_average: kmg, kmg_count: n,
      deviation_from_kmg_percent: deviation, deviation_exceeds_threshold: deviation !== null && Math.abs(deviation) > DEVIATION_THRESHOLD, history,
    }
  })
  return { calc_method: 'average', vat_rate_percent: VAT, participants: new Set(a.offers.map((o) => o.supplier_bin)).size, total_wo_vat: a.total_wo_vat, items }
}

async function sha256(text) {
  try {
    const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
    return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('')
  } catch {
    let h = 0
    for (const ch of text) h = (h * 31 + ch.charCodeAt(0)) >>> 0
    return h.toString(16).padStart(64, '0')
  }
}

async function finishPdf(a) {
  if (a.pdf_status !== 'pending') return
  a.pdf_sha256 = await sha256(JSON.stringify({ n: a.number, items: a.items, offers: a.offers, steps: a.steps }))
  a.pdf_status = 'ready'
  a.pdf_generated_at = nowIso()
  notify([a.author, a.initiator_user], 'ma_pdf_ready', `Маркетинговое заключение ${a.number} сформировано`, 'Заключение доступно в карточке анализа.', a)
}

// ---------------------------------------------------------------- операции

const ops = {
  create(data) {
    const u = me()
    if (!hasRole(u, 'marketer')) forbidden()
    const dzoId = Number(data.dzo || u.dzo)
    if (!marketerDzoIds(u).includes(dzoId)) forbidden()
    const dzo = dzoById(dzoId)
    const key = `${nowDate().getFullYear()}.${dzo.code}`
    state.numbers[key] = (state.numbers[key] || 0) + 1
    const a = {
      id: nextId('analysis'), number: `ID${key}.${String(state.numbers[key]).padStart(4, '0')}`, dzo: dzoId, author: u.id,
      initiator_user: null, initiator_full_name: '', initiator_position: '', initiator_department: '',
      status: 'draft', current_stage: null, iteration: 0, returned_from_stage: null, price_justification: '', total_wo_vat: null,
      created_at: nowIso(), updated_at: nowIso(), submitted_at: null, approved_at: null, cancelled_at: null,
      pdf_status: 'none', pdf_sha256: '', pdf_generated_at: null, ready_at: null,
      items: [], offers: [], approvers: [], steps: [], audit: [],
    }
    applyInitiator(a, data)
    state.analyses.push(a)
    audit(a, 'created', { to: 'draft' })
    return a
  },
  update(a, data) {
    editable(a)
    if (data.dzo && Number(data.dzo) !== a.dzo) fail(400, 'dzo_immutable', 'ДЗО нельзя изменить после создания анализа (номер уже присвоен)')
    applyInitiator(a, data)
    audit(a, 'updated')
  },
  addItem(a, data) {
    editable(a)
    const p = PRODUCTS.find((x) => x.id === Number(data.nsi_product))
    if (!p) fail(400, 'nsi_product_required', 'Выберите товар из справочника АСУ НСИ')
    const qty = parseNum(data.quantity)
    if (!(qty > 0)) fail(400, 'must_be_positive', 'Количество должно быть больше нуля', [{ field: 'quantity', code: 'must_be_positive', message: 'Должно быть больше нуля' }])
    const item = {
      id: nextId('item'), line_no: Math.max(0, ...a.items.map((i) => i.line_no)) + 1, nsi_product: p.id, nsi_code: p.nsi_code,
      enstru_code: p.enstru_code, name: p.name, characteristics: p.short_description, unit: p.unit, quantity: qty,
      delivery_place: (data.delivery_place || '').trim(), delivery_term: (data.delivery_term || '').trim(),
      marketing_price: null, total_wo_vat: null, calc_method: '', price_justification: '', attachments: [],
    }
    a.items.push(item)
    recalcTotal(a)
    audit(a, 'item_added')
    return item
  },
  addOffer(a, data) {
    editable(a)
    const offer = createOffer(a, data)
    if (a.status === 'draft') transition(a, 'collecting_kp', 'collecting_started')
    audit(a, 'offer_uploaded')
    return offer
  },
  calculate(a) {
    editable(a)
    a.items.forEach((item) => {
      const values = a.offers.flatMap((o) => o.prices.filter((p) => p.item === item.id).map((p) => p.price_kzt_wo_vat))
      item.marketing_price = values.length ? money(values.reduce((s, v) => s + v, 0) / values.length) : null
      item.total_wo_vat = item.marketing_price !== null ? money(item.marketing_price * item.quantity) : null
      item.calc_method = item.marketing_price !== null ? 'average' : ''
    })
    recalcTotal(a)
    audit(a, 'calculated')
  },
  setApprovers(a, ids) {
    editable(a)
    ids = (ids || []).map(Number)
    if (new Set(ids).size !== ids.length) fail(400, 'duplicate_approvers', 'Согласующий указан дважды')
    const errors = []
    ids.forEach((id) => {
      const u = userById(id)
      if (!u) errors.push({ user_id: id, code: 'not_found', message: 'Пользователь не найден' })
      else if (u.id === a.author) errors.push({ user_id: id, code: 'author', message: `${fullName(u)}: автор не может быть согласующим` })
      else if (u.dzo !== a.dzo) errors.push({ user_id: id, code: 'other_dzo', message: `${fullName(u)}: согласующий должен быть сотрудником ДЗО анализа` })
    })
    if (errors.length) fail(400, 'invalid_approvers', 'Некорректный список согласующих', errors)
    a.approvers = ids
    audit(a, 'approvers_set')
  },
  submit(a) {
    expect(a, ['collecting_kp', 'rework'])
    if (!canEdit(me(), a)) forbidden()
    const errors = validateForSubmit(a)
    if (errors.length) fail(400, 'validation_failed', 'Анализ не готов к отправке на согласование', errors)
    a.iteration += 1
    const at = nowIso()
    const steps = a.approvers.map((uid, i) => ({ stage: 1, order: i + 1, assignee_user: uid, assignee_role: '' }))
    steps.push({ stage: 2, order: 1, assignee_user: null, assignee_role: 'db_specialist' }, { stage: 3, order: 1, assignee_user: null, assignee_role: 'db_director' })
    steps.forEach((s, i) => a.steps.push({ id: nextId('step'), iteration: a.iteration, ...s, status: i === 0 ? 'pending' : 'waiting',
      activated_at: i === 0 ? at : null, decided_at: null, decided_by: null, decided_by_name: '', decided_by_position: '', comment: '' }))
    a.current_stage = 1
    a.submitted_at = at
    a.returned_from_stage = null
    transition(a, 'on_approval_dzo', 'submitted')
    notifyStep(a, currentStep(a))
  },
  decide(a, { decision, comment = '', step_id: stepId }) {
    comment = (comment || '').trim()
    if (decision === 'rework' && !comment) fail(400, 'comment_required', 'При возврате на доработку комментарий обязателен')
    expect(a, ON_APPROVAL)
    const step = currentStep(a)
    if (!step || (stepId && Number(stepId) !== step.id)) fail(409, 'step_already_processed', 'Шаг уже обработан. Обновите страницу.')
    const u = me()
    if (!isExecutor(u, step)) forbidden()
    Object.assign(step, { decided_by: u.id, decided_by_name: fullName(u), decided_by_position: u.position, comment, decided_at: nowIso() })
    if (decision === 'rework') {
      step.status = 'returned'
      a.steps.filter((s) => s.iteration === a.iteration && s.status === 'waiting').forEach((s) => { s.status = 'skipped' })
      a.returned_from_stage = step.stage
      a.current_stage = null
      transition(a, 'rework', 'returned_for_rework', { comment })
      notify([a.author], 'ma_returned', `Маркетинговый анализ ${a.number} возвращён на доработку`, `${step.decided_by_name}: ${comment}`, a)
      return
    }
    step.status = 'approved'
    const next = a.steps.filter((s) => s.iteration === a.iteration && s.status === 'waiting').sort((x, y) => x.stage - y.stage || x.order - y.order)[0]
    if (next) {
      next.status = 'pending'
      next.activated_at = nowIso()
      if (next.stage !== step.stage) { a.current_stage = next.stage; transition(a, STAGE_STATUS[next.stage], 'step_approved', { comment }) } else audit(a, 'step_approved', { from: a.status, to: a.status, comment })
      notifyStep(a, next)
      return
    }
    a.current_stage = null
    a.approved_at = nowIso()
    a.pdf_status = 'pending'
    a.ready_at = Date.now() + 2500
    transition(a, 'approved', 'approved', { comment })
    a.items.forEach((item) => {
      state.catalog.filter((e) => e.nsi_code === item.nsi_code && e.dzo === a.dzo && e.is_active).forEach((e) => { e.is_active = false })
      state.catalog.push({ nsi_code: item.nsi_code, dzo: a.dzo, price_wo_vat: item.marketing_price, approved_at: a.approved_at, source_id: `ma-${a.id}`, source_number: a.number, is_active: true })
    })
    notify([a.author, a.initiator_user], 'ma_approved', `Маркетинговый анализ ${a.number} утверждён`, `Утвердил: ${step.decided_by_name}`, a)
  },
}

function applyInitiator(a, data) {
  if ('initiator_user' in data) {
    a.initiator_user = data.initiator_user ? Number(data.initiator_user) : null
    if (a.initiator_user) { a.initiator_full_name = ''; a.initiator_position = ''; a.initiator_department = '' }
  }
  for (const f of ['initiator_full_name', 'initiator_position', 'initiator_department']) {
    if (f in data && !a.initiator_user) a[f] = (data[f] || '').trim()
  }
  if ('price_justification' in data) a.price_justification = data.price_justification || ''
}

// ---------------------------------------------------------------- маршрутизация запросов

function formToObject(body) {
  if (!(body instanceof FormData)) return body || {}
  const obj = {}
  for (const [k, v] of body.entries()) {
    if (v instanceof File) obj.fileName = v.name
    else obj[k] = v
  }
  return obj
}

function getAnalysis(id) {
  const a = state.analyses.find((x) => x.id === Number(id))
  if (!a || !visible(me(), a)) notFound()
  return a
}

function awaitingMe(u, a) {
  const s = currentStep(a)
  return !!s && (s.assignee_user ? s.assignee_user === u.id : u.roles.includes(s.assignee_role))
}

const TABS = {
  draft: (a) => a.status === 'draft', collecting_kp: (a) => a.status === 'collecting_kp', on_approval: (a) => ON_APPROVAL.includes(a.status),
  rework: (a) => a.status === 'rework', approved: (a) => a.status === 'approved', cancelled: (a) => a.status === 'cancelled', all: () => true,
}

function list(params) {
  const u = me()
  let base = state.analyses.filter((a) => visible(u, a))
  const q = (params.get('q') || '').trim().toLowerCase()
  if (q) base = base.filter((a) => a.number.toLowerCase().includes(q) || a.items.some((i) => i.name.toLowerCase().includes(q) || i.nsi_code.startsWith(q)))
  if (params.get('dzo')) base = base.filter((a) => a.dzo === Number(params.get('dzo')))
  if (params.get('date_from')) base = base.filter((a) => a.created_at.slice(0, 10) >= params.get('date_from'))
  if (params.get('date_to')) base = base.filter((a) => a.created_at.slice(0, 10) <= params.get('date_to'))
  const counts = Object.fromEntries(Object.entries(TABS).map(([k, f]) => [k, base.filter(f).length]))
  counts.awaiting_me = base.filter((a) => awaitingMe(u, a)).length
  const tab = params.get('tab') || 'all'
  const rows = base.filter(tab === 'awaiting_me' ? (a) => awaitingMe(u, a) : TABS[tab] || TABS.all)
    .sort((x, y) => y.created_at.localeCompare(x.created_at) || y.id - x.id)
  const page = Number(params.get('page') || 1)
  return { count: rows.length, next: null, previous: null, results: rows.slice((page - 1) * 20, page * 20).map(listOut), counts }
}

function searchUsers(params) {
  const q = (params.get('q') || '').toLowerCase().split(/\s+/).filter(Boolean)
  const dzo = params.get('dzo')
  return DEMO_USERS.filter((u) => (!dzo || u.dzo === Number(dzo)) &&
    q.every((t) => [u.last, u.first, u.middle, u.username].some((f) => f.toLowerCase().includes(t)))).map(userShort)
}

function meOut() {
  const u = me()
  if (!u) return { user: null, features: { marketing_analysis: true, marketing_analysis_participant: false } }
  const participant = state.analyses.some((a) => a.approvers.includes(u.id) || a.steps.some((s) => s.assignee_user === u.id))
  return {
    user: { ...userShort(u), email: `${u.username}@demo.local`, roles: [...u.roles].sort(), allowed_dzos: marketerDzoIds(u).map(dzoById) },
    features: { marketing_analysis: true, marketing_analysis_participant: participant },
  }
}

export async function handle(method, url, body) {
  if (!state) init()
  const { pathname, searchParams } = new URL(url, 'http://demo')
  const path = pathname.replace(/^\/api/, '')
  const data = formToObject(body)
  const m = (re) => path.match(re)
  let match
  const result = await (async () => {
    if (path === '/auth/me/') return meOut()
    if (path === '/auth/login/') {
      const u = DEMO_USERS.find((x) => x.username === (data.username || '').trim())
      if (!u || data.password !== PASSWORD) fail(400, 'invalid_credentials', 'Неверный логин или пароль')
      state.currentUserId = u.id
      return meOut()
    }
    if (path === '/auth/logout/') { state.currentUserId = null; return null }
    if (!me()) fail(403, 'not_authenticated', 'Учётные данные не были предоставлены.')
    if (path === '/dzos/') return DZOS
    if (path === '/users/search/') return searchUsers(searchParams)
    if (path === '/nsi/products/') {
      const q = (searchParams.get('q') || '').toLowerCase()
      return PRODUCTS.filter((p) => !q || p.nsi_code.startsWith(q) || p.enstru_code.startsWith(q) || p.name.toLowerCase().includes(q))
    }
    if (path === '/suppliers/') return SUPPLIERS
    if (path === '/notifications/') {
      const mine = state.notifications.filter((n) => n.user === me().id)
      return { count: mine.length, results: mine.slice(0, 20), unread: mine.filter((n) => !n.is_read).length }
    }
    if (path === '/notifications/read/') { state.notifications.filter((n) => n.user === me().id).forEach((n) => { n.is_read = true }); return null }

    if (path === '/marketing-analyses/' && method === 'GET') return list(searchParams)
    if (path === '/marketing-analyses/' && method === 'POST') return detailOut(me(), ops.create(data))
    if ((match = m(/^\/marketing-analyses\/(\d+)\/(.*)$/))) {
      const a = getAnalysis(match[1])
      const rest = match[2]
      const u = me()
      const detail = () => detailOut(u, a)
      if (rest === '' && method === 'GET') {
        if (a.pdf_status === 'pending' && a.ready_at !== null && Date.now() >= a.ready_at) await finishPdf(a)
        return detail()
      }
      if (rest === '' && method === 'PATCH') { ops.update(a, data); return detail() }
      if (rest === '' && method === 'DELETE') {
        expect(a, ['draft']); if (!canEdit(u, a)) forbidden()
        state.analyses = state.analyses.filter((x) => x.id !== a.id); return null
      }
      if (rest === 'items/' && method === 'POST') return ops.addItem(a, data)
      if ((match = rest.match(/^items\/(\d+)\/$/))) {
        editable(a)
        const item = a.items.find((i) => i.id === Number(match[1])) || notFound()
        if (method === 'DELETE') {
          a.items = a.items.filter((i) => i !== item)
          a.offers.forEach((o) => { o.prices = o.prices.filter((p) => p.item !== item.id) })
          recalcTotal(a); audit(a, 'item_deleted'); return null
        }
        if ('quantity' in data) {
          const q = parseNum(data.quantity)
          if (!(q > 0)) fail(400, 'must_be_positive', 'Количество должно быть больше нуля')
          item.quantity = q
          if (item.marketing_price !== null) item.total_wo_vat = money(item.marketing_price * q)
        }
        for (const f of ['delivery_place', 'delivery_term', 'price_justification']) if (f in data) item[f] = (data[f] || '').trim()
        recalcTotal(a); audit(a, 'item_updated'); return item
      }
      if ((match = rest.match(/^items\/(\d+)\/attachments\/$/))) {
        editable(a)
        const item = a.items.find((i) => i.id === Number(match[1])) || notFound()
        checkFile(data.fileName)
        const att = { id: nextId('att'), original_name: data.fileName, uploaded_at: nowIso() }
        item.attachments.push(att); audit(a, 'attachment_added'); return att
      }
      if ((match = rest.match(/^items\/(\d+)\/attachments\/(\d+)\/$/))) {
        editable(a)
        const item = a.items.find((i) => i.id === Number(match[1])) || notFound()
        item.attachments = item.attachments.filter((x) => x.id !== Number(match[2])); audit(a, 'attachment_deleted'); return null
      }
      if (rest === 'offers/' && method === 'POST') return ops.addOffer(a, data)
      if ((match = rest.match(/^offers\/(\d+)\/$/)) && method === 'DELETE') {
        editable(a)
        const offer = a.offers.find((o) => o.id === Number(match[1])) || notFound()
        a.offers = a.offers.filter((o) => o !== offer)
        invalidate(a, offer.prices.map((p) => p.item)); audit(a, 'offer_deleted'); return null
      }
      if (rest === 'request-kp/') {
        editable(a)
        const ids = (data.suppliers || []).map(Number)
        if (!ids.length) fail(400, 'suppliers_required', 'Выберите поставщиков из пула')
        if (!a.items.length) fail(400, 'items_required', 'Сначала добавьте позиции')
        if (a.status === 'draft') transition(a, 'collecting_kp', 'collecting_started')
        audit(a, 'kp_requested'); return { sent: ids.length }
      }
      if (rest === 'start-collecting/') { expect(a, ['draft']); if (!canEdit(u, a)) forbidden(); transition(a, 'collecting_kp', 'collecting_started'); return detail() }
      if (rest === 'calculate/') { ops.calculate(a); return detail() }
      if (rest === 'analytics/') return analytics(a)
      if (rest === 'approvers/') { ops.setApprovers(a, data.approvers); return detail() }
      if (rest === 'submit-check/') return { errors: validateForSubmit(a) }
      if (rest === 'submit/') { ops.submit(a); return detail() }
      if (rest === 'decision/') { ops.decide(a, data); return detail() }
      if (rest === 'cancel/') {
        expect(a, EDITABLE); if (!canEdit(u, a)) forbidden()
        a.cancelled_at = nowIso(); a.current_stage = null
        transition(a, 'cancelled', 'cancelled', { comment: data.comment || '' }); return detail()
      }
      if (rest === 'history/') {
        return {
          steps: a.steps.map(stepOut),
          events: a.audit.map((e) => ({ ...e, user_name: e.user ? fullName(userById(e.user)) : 'Система' })),
        }
      }
    }
    notFound()
  })()
  if (method !== 'GET' || path.startsWith('/marketing-analyses/')) save()
  return result === undefined ? null : JSON.parse(JSON.stringify(result))
}

// ---------------------------------------------------------------- начальные данные

function as(username, fn) {
  state.currentUserId = DEMO_USERS.find((u) => u.username === username).id
  return fn()
}

function seed() {
  state = { seq: {}, numbers: {}, analyses: [], notifications: [], catalog: [], currentUserId: null }
  const hist = [
    ['1010101001', 2, 7850, 200, false], ['1010101001', 2, 7920, 120, true], ['1010101001', 3, 8120, 60, true],
    ['2020202001', 2, 1450000, 150, true], ['2020202001', 3, 1395000, 400, true],
    ['3030303001', 3, 2150, 30, true], ['4040404001', 2, 18900, 90, true], ['1010101002', 3, 5600, 75, true],
  ]
  hist.forEach(([nsi, dzo, price, days, active], i) => state.catalog.push({
    nsi_code: nsi, dzo, price_wo_vat: price, approved_at: daysAgo(days).toISOString(), source_id: `legacy-${i}`,
    source_number: `ID${daysAgo(days).getFullYear()}.${dzoById(dzo).code}.${String(10 + i).padStart(4, '0')}`, is_active: active,
  }))

  const at = (d, h) => { fakeNow = daysAgo(d, h).getTime() }
  const offer = (a, supplierIdx, currency, vat, prices, d) => {
    const s = SUPPLIERS[supplierIdx]
    const priceMap = Object.fromEntries(a.items.map((it, i) => [it.id, prices[i]]).filter(([, p]) => p !== undefined))
    ops.addOffer(a, { supplier_bin: s.bin, supplier_name: s.name, offer_date: daysAgo(d).toISOString().slice(0, 10), currency, vat_included: vat ? 'true' : 'false', prices: priceMap, fileName: `КП_${s.name.replace(/[^А-Яа-яA-Za-z]+/g, '_')}.pdf` })
  }

  // 1. Утверждённый анализ с заключением
  as('marketer', () => {
    at(21, 9)
    const a = ops.create({ dzo: 1, initiator_user: 4 })
    ops.addItem(a, { nsi_product: 1, quantity: '1200', delivery_place: 'Склад НГДУ-1, г. Атырау', delivery_term: '60 календарных дней' })
    ops.addItem(a, { nsi_product: 3, quantity: '4', delivery_place: 'Склад НГДУ-1, г. Атырау', delivery_term: '90 календарных дней' })
    at(18, 11); offer(a, 0, 'KZT', false, [8200, 1520000], 18)
    at(17, 15); offer(a, 1, 'USD', true, [18.5, 3100], 17)
    at(16, 10); offer(a, 2, 'KZT', true, [9300, 1650000], 16)
    ops.calculate(a)
    a.price_justification = 'Цена определена как среднее арифметическое трёх коммерческих предложений, приведённых к тенге без НДС по курсу НБ РК на дату КП.'
    ops.setApprovers(a, [2, 3]); ops.submit(a)
    return a
  })
  at(15, 10); as('approver1', () => ops.decide(state.analyses[0], { decision: 'approve' }))
  at(15, 16); as('approver2', () => ops.decide(state.analyses[0], { decision: 'approve', comment: 'Объём соответствует плану закупок' }))
  at(14, 12); as('db_specialist', () => ops.decide(state.analyses[0], { decision: 'approve' }))
  at(13, 10); as('db_director', () => ops.decide(state.analyses[0], { decision: 'approve', comment: 'Утверждаю' }))
  state.analyses[0].pdf_status = 'pending'
  state.analyses[0].ready_at = 0

  // 2. На согласовании у approver1
  as('marketer', () => {
    at(6, 9)
    const a = ops.create({ dzo: 1, initiator_full_name: 'Мусин Талгат Ерланович', initiator_position: 'Начальник цеха добычи', initiator_department: 'ЦДНГ-3' })
    ops.addItem(a, { nsi_product: 5, quantity: '3600', delivery_place: 'ЦДНГ-3', delivery_term: '30 календарных дней' })
    ops.addItem(a, { nsi_product: 6, quantity: '12000', delivery_place: 'ЦДНГ-3', delivery_term: '45 календарных дней' })
    at(4, 12); offer(a, 4, 'KZT', true, [2380, 1650], 4)
    at(4, 15); offer(a, 2, 'RUB', false, [330, 255], 4)
    ops.calculate(a); ops.setApprovers(a, [2, 3])
    at(3, 10); ops.submit(a)
  })

  // 3. Возвращён на доработку специалистом ДБ
  as('marketer', () => {
    at(9, 10)
    const a = ops.create({ dzo: 1, initiator_user: 4 })
    ops.addItem(a, { nsi_product: 7, quantity: '450', delivery_place: 'Склад общего назначения', delivery_term: 'до 1 декабря' })
    at(8, 11); offer(a, 3, 'KZT', true, [24500], 8)
    ops.calculate(a); ops.setApprovers(a, [9]); ops.submit(a)
  })
  at(7, 10); as('approver3', () => ops.decide(state.analyses[2], { decision: 'approve' }))
  at(5, 15); as('db_specialist', () => ops.decide(state.analyses[2], { decision: 'rework', comment: 'По позиции одно КП. Запросите не менее двух дополнительных предложений у поставщиков из пула.' }))

  // 4. Сбор КП, цена ещё не рассчитана
  as('marketer', () => {
    at(2, 9)
    const a = ops.create({ dzo: 1, initiator_user: 9 })
    ops.addItem(a, { nsi_product: 2, quantity: '800', delivery_place: 'Месторождение «Демо-Север»', delivery_term: '75 календарных дней' })
    ops.addItem(a, { nsi_product: 4, quantity: '150', delivery_place: 'Месторождение «Демо-Север»', delivery_term: '75 календарных дней' })
    at(1, 14); offer(a, 0, 'KZT', false, [5750, 41800], 1)
  })

  // 5. Черновик
  as('marketer', () => {
    at(0, 9)
    ops.create({ dzo: 1, initiator_full_name: 'Бекова Алия Нурлановна', initiator_position: 'Инженер по охране труда' })
  })

  fakeNow = null
  state.currentUserId = null
  state.notifications.forEach((n, i) => { if (i > 6) n.is_read = true })
}

function init() {
  if (!load()) { seed(); save() }
}
