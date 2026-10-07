const nf = new Intl.NumberFormat('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const qf = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 3 })

export const money = (v) => (v === null || v === undefined || v === '' ? '—' : nf.format(Number(v)))
export const qty = (v) => (v === null || v === undefined || v === '' ? '—' : qf.format(Number(v)))
export const date = (v) => (v ? new Date(v).toLocaleDateString('ru-RU') : '—')
export const time = (v) => (v ? new Date(v).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }) : '')
export const datetime = (v) => (v ? `${date(v)} ${time(v)}` : '—')
export const percent = (v) => (v === null || v === undefined ? '—' : `${Number(v) > 0 ? '+' : ''}${nf.format(Number(v))} %`)
