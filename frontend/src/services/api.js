/**
 * SmartWatt India — API Service Layer
 * All backend calls are centralised here.
 * Base URL read from VITE_API_BASE_URL env var (default: http://localhost:8000).
 */

const BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')
const API = `${BASE}/api/v1`

async function get(path) {
  const res = await fetch(`${API}${path}`)
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`API ${res.status}: ${text || res.statusText}`)
  }
  return res.json()
}

export const api = {
  health: () => get('/health'),
  metadata: () => get('/metadata'),
  summary: () => get('/summary'),
  households: () => get('/households'),
  household: (id) => get(`/households/${id}`),
  timeseries: (id, { dateFrom, dateTo, limit } = {}) => {
    const params = new URLSearchParams()
    if (dateFrom) params.set('date_from', dateFrom)
    if (dateTo) params.set('date_to', dateTo)
    if (limit) params.set('limit', limit)
    const qs = params.toString()
    return get(`/households/${id}/timeseries${qs ? '?' + qs : ''}`)
  },
  anomalies: (id, { minMethods = 1 } = {}) =>
    get(`/households/${id}/anomalies?min_methods=${minMethods}`),
  predict: (body) => {
    const BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')
    return fetch(`${BASE}/api/v1/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(async (res) => {
      if (!res.ok) {
        const text = await res.text().catch(() => '')
        throw new Error(`API ${res.status}: ${text || res.statusText}`)
      }
      return res.json()
    })
  },
}
