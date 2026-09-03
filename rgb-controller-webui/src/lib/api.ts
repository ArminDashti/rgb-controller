export const API_BASE = (() => {
  const raw = import.meta.env.VITE_API_BASE_URL as string | undefined
  if (raw === undefined || raw === '') return ''
  return raw.replace(/\/$/, '')
})()

async function parseError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { error?: string; detail?: string }
    if (data.error) return data.error
    if (typeof data.detail === 'string') return data.detail
  } catch {
    /* ignore */
  }
  return `Request failed (${response.status})`
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!response.ok) {
    throw new Error(await parseError(response))
  }
  if (response.status === 204) {
    return undefined as T
  }
  return response.json() as Promise<T>
}

export type RgbColor = { r: number; g: number; b: number }

export type DeviceSummary = {
  id: number
  name: string
  type: string
  led_count: number
  active_mode: string
  colors: RgbColor[]
}

export type DeviceDetail = DeviceSummary & {
  modes: { id: number; name: string; speed: number | null }[]
  zones: {
    id: number
    name: string
    led_count: number
    matrix: { width: number; height: number; map: number[][] | null } | null
  }[]
}

export type PredefinedMode = {
  id: string
  name: string
  kind: string
  adjustments: string[]
}

export type CustomMode = {
  id: string
  kind: 'symbol' | 'text'
  name: string
  payload: Record<string, unknown>
}

export type Settings = {
  openrgb_host: string
  openrgb_port: number
  openrgb_exe_path: string
  run_startup: boolean
  idle_mode_id: string
  idle_minutes: number
  backlight_percent: number
}

export function fetchDevices() {
  return apiFetch<{ devices: DeviceSummary[] }>('/api/v1/devices')
}

export function fetchDevice(id: number) {
  return apiFetch<DeviceDetail>(`/api/v1/devices/${id}`)
}

export function setDeviceMode(id: number, name: string) {
  return apiFetch<{ ok: boolean }>(`/api/v1/devices/${id}/mode`, {
    method: 'POST',
    body: JSON.stringify({ name }),
  })
}

export function fetchModes() {
  return apiFetch<{ predefined: PredefinedMode[]; custom: CustomMode[] }>('/api/v1/modes')
}

export function applyMode(body: {
  mode_id: string
  device_ids?: number[]
  color?: string
  speed?: number
  brightness?: number
}) {
  return apiFetch<{ ok: boolean; mode_id: string }>('/api/v1/modes/apply', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function createCustomMode(body: { kind: string; name: string; payload: Record<string, unknown> }) {
  return apiFetch<CustomMode>('/api/v1/modes/custom', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function deleteCustomMode(id: string) {
  return apiFetch<{ ok: boolean }>(`/api/v1/modes/custom/${id}`, { method: 'DELETE' })
}

export function fetchSettings() {
  return apiFetch<Settings>('/api/v1/settings')
}

export function saveSettings(body: Partial<Settings>) {
  return apiFetch<Settings>('/api/v1/settings', {
    method: 'PUT',
    body: JSON.stringify(body),
  })
}

export function fetchOpenRgbStatus() {
  return apiFetch<{
    connected: boolean
    last_error: string
    host: string
    port: number
  }>('/api/v1/openrgb/status')
}

export function testOpenRgb(body?: { host?: string; port?: number }) {
  return apiFetch<{ ok: boolean; device_count: number; error: string }>('/api/v1/openrgb/test', {
    method: 'POST',
    body: JSON.stringify(body ?? {}),
  })
}

export function colorCss(c: RgbColor) {
  return `rgb(${c.r}, ${c.g}, ${c.b})`
}
