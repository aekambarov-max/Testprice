// Обёртка над fetch: сессия Django + CSRF, единый формат ошибок {code, detail, errors}.
import { DEMO } from './demo/flag'

function csrfToken() {
  const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)
  return m ? decodeURIComponent(m[1]) : ''
}

export class ApiError extends Error {
  constructor(status, data) {
    super((data && (data.detail || data.message)) || `HTTP ${status}`)
    this.status = status
    this.code = data && data.code
    this.errors = (data && data.errors) || []
    this.data = data
  }
}

export async function request(method, url, body, { raw = false } = {}) {
  if (DEMO) {
    const { handle } = await import('./demo/mockServer')
    try {
      return await handle(method, url, body)
    } catch (e) {
      if (e.status) throw new ApiError(e.status, e.data)
      throw e
    }
  }
  const opts = { method, credentials: 'same-origin', headers: { 'X-CSRFToken': csrfToken() } }
  if (body instanceof FormData) {
    opts.body = body
  } else if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }
  const res = await fetch(url, opts)
  if (raw && res.ok) return res
  if (res.status === 204) return null
  const text = await res.text()
  let data = null
  try { data = text ? JSON.parse(text) : null } catch { data = { detail: text } }
  if (!res.ok) throw new ApiError(res.status, data)
  return data
}

const qs = (params) => {
  const p = new URLSearchParams()
  Object.entries(params || {}).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') p.append(k, v) })
  const s = p.toString()
  return s ? `?${s}` : ''
}

const MA = '/api/marketing-analyses'

export const api = {
  me: () => request('GET', '/api/auth/me/'),
  login: (username, password) => request('POST', '/api/auth/login/', { username, password }),
  logout: () => request('POST', '/api/auth/logout/'),
  dzos: () => request('GET', '/api/dzos/'),
  searchUsers: (q, dzo) => request('GET', `/api/users/search/${qs({ q, dzo })}`),
  searchProducts: (q) => request('GET', `/api/nsi/products/${qs({ q })}`),
  suppliers: (q) => request('GET', `/api/suppliers/${qs({ q })}`),
  notifications: () => request('GET', '/api/notifications/'),
  readNotifications: (ids) => request('POST', '/api/notifications/read/', { ids }),

  list: (params) => request('GET', `${MA}/${qs(params)}`),
  get: (id) => request('GET', `${MA}/${id}/`),
  create: (data) => request('POST', `${MA}/`, data),
  update: (id, data) => request('PATCH', `${MA}/${id}/`, data),
  remove: (id) => request('DELETE', `${MA}/${id}/`),
  addItem: (id, data) => request('POST', `${MA}/${id}/items/`, data),
  updateItem: (id, itemId, data) => request('PATCH', `${MA}/${id}/items/${itemId}/`, data),
  deleteItem: (id, itemId) => request('DELETE', `${MA}/${id}/items/${itemId}/`),
  addAttachment: (id, itemId, file) => {
    const fd = new FormData(); fd.append('file', file)
    return request('POST', `${MA}/${id}/items/${itemId}/attachments/`, fd)
  },
  deleteAttachment: (id, itemId, attId) => request('DELETE', `${MA}/${id}/items/${itemId}/attachments/${attId}/`),
  attachmentUrl: (id, itemId, attId) => (DEMO ? null : `${MA}/${id}/items/${itemId}/attachments/${attId}/`),
  addOffer: (id, formData) => request('POST', `${MA}/${id}/offers/`, formData),
  deleteOffer: (id, offerId) => request('DELETE', `${MA}/${id}/offers/${offerId}/`),
  offerUrl: (id, offerId) => (DEMO ? null : `${MA}/${id}/offers/${offerId}/`),
  requestKp: (id, suppliers, message) => request('POST', `${MA}/${id}/request-kp/`, { suppliers, message }),
  startCollecting: (id) => request('POST', `${MA}/${id}/start-collecting/`),
  calculate: (id) => request('POST', `${MA}/${id}/calculate/`),
  analytics: (id) => request('GET', `${MA}/${id}/analytics/`),
  setApprovers: (id, approvers) => request('PUT', `${MA}/${id}/approvers/`, { approvers }),
  submitCheck: (id) => request('GET', `${MA}/${id}/submit-check/`),
  submit: (id) => request('POST', `${MA}/${id}/submit/`),
  decision: (id, decision, comment, stepId) =>
    request('POST', `${MA}/${id}/decision/`, { decision, comment, step_id: stepId }),
  cancel: (id, comment) => request('POST', `${MA}/${id}/cancel/`, { comment }),
  history: (id) => request('GET', `${MA}/${id}/history/`),
  pdfUrl: (id) => `${MA}/${id}/conclusion.pdf`,
  regeneratePdf: (id) => request('POST', `${MA}/${id}/regenerate-pdf/`),

  kpRequest: (token) => request('GET', `/api/kp-responses/${token}/`),
  kpRespond: (token, formData) => request('POST', `/api/kp-responses/${token}/`, formData),
}
