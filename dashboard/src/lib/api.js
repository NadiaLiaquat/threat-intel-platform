/**
 * api.js — thin fetch wrapper. Always calls relative /api/... paths; the
 * Vite dev server proxy (local dev) or nginx (Docker Compose) is what
 * routes that to the actual backend — see vite.config.js / nginx.conf.
 */
async function request(path, options) {
  const res = await fetch(path, options)
  if (!res.ok) {
    throw new Error(`${options?.method || 'GET'} ${path} failed: ${res.status}`)
  }
  return res.json()
}

export const api = {
  summary: () => request('/api/stats/summary'),
  byRegion: () => request('/api/stats/by-region'),
  topSources: () => request('/api/stats/top-sources'),
  topMalwareFamilies: () => request('/api/stats/top-malware-families'),
  iocs: (params = {}) => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== '')),
    )
    return request(`/api/iocs?${qs}`)
  },
  triggerCollection: () => request('/api/collect/run', { method: 'POST' }),
}

export default api
