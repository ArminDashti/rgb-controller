<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  fetchModes,
  fetchOpenRgbStatus,
  fetchSettings,
  saveSettings,
  testOpenRgb,
  type Settings,
} from '@/lib/api'

const settings = ref<Settings | null>(null)
const host = ref('127.0.0.1')
const port = ref('6742')
const exePath = ref('')
const runStartup = ref(false)
const idleModeId = ref('')
const idleMinutesStr = ref('')
const backlight = ref(100)
const modeOptions = ref<{ id: string; name: string }[]>([])
const status = ref('')
const error = ref('')
const connected = ref(false)

onMounted(async () => {
  try {
    const [saved, sdk, modes] = await Promise.all([fetchSettings(), fetchOpenRgbStatus(), fetchModes()])
    settings.value = saved
    host.value = saved.openrgb_host
    port.value = String(saved.openrgb_port)
    exePath.value = saved.openrgb_exe_path
    runStartup.value = saved.run_startup
    idleModeId.value = saved.idle_mode_id
    idleMinutesStr.value = saved.idle_minutes > 0 ? String(saved.idle_minutes) : ''
    backlight.value = saved.backlight_percent
    connected.value = sdk.connected
    status.value = sdk.connected ? `Connected to ${sdk.host}:${sdk.port}` : sdk.last_error || 'Not connected'
    modeOptions.value = [
      { id: '', name: '(none)' },
      ...modes.predefined.map((m) => ({ id: m.id, name: m.name })),
      ...modes.custom.map((m) => ({ id: m.id, name: m.name })),
    ]
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Could not load settings'
  }
})

async function onSaveSdk() {
  error.value = ''
  try {
    await saveSettings({ openrgb_host: host.value, openrgb_port: Number(port.value) })
    status.value = 'Saved SDK address'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Save failed'
  }
}

async function onTest() {
  error.value = ''
  const result = await testOpenRgb({ host: host.value, port: Number(port.value) })
  connected.value = result.ok
  status.value = result.ok ? `Connected · ${result.device_count} devices` : result.error
}

async function onSaveStartup() {
  error.value = ''
  try {
    await saveSettings({
      openrgb_exe_path: exePath.value,
      run_startup: runStartup.value,
    })
    status.value = 'Saved startup'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Save failed'
  }
}

async function onSaveIdle() {
  error.value = ''
  const minutes = idleMinutesStr.value.trim() === '' ? 0 : Number(idleMinutesStr.value)
  const mode = idleModeId.value.trim()
  if ((mode && minutes < 1) || (!mode && minutes >= 1)) {
    error.value = 'Set both time-of-idle and its mode, or leave both empty to turn idle off.'
    return
  }
  try {
    await saveSettings({
      idle_mode_id: mode,
      idle_minutes: minutes,
    })
    status.value = mode ? `Idle after ${minutes} min → ${mode}` : 'Idle off'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Save failed'
  }
}

async function onSaveBacklight() {
  error.value = ''
  try {
    await saveSettings({ backlight_percent: backlight.value })
    status.value = 'Saved backlight'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Save failed'
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-4 px-4 py-8">
    <h1 class="text-2xl font-semibold tracking-tight">Settings</h1>
    <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
    <p v-if="status" class="text-sm text-muted-foreground">{{ status }}</p>
    <Card>
      <CardHeader>
        <CardTitle>OpenRGB SDK</CardTitle>
        <CardDescription>Host and port of the OpenRGB SDK server. This is where the API connects.</CardDescription>
      </CardHeader>
      <CardContent class="space-y-3">
        <label class="block space-y-1 text-sm">
          <span>Host</span>
          <Input v-model="host" />
        </label>
        <label class="block space-y-1 text-sm">
          <span>Port</span>
          <Input v-model="port" type="number" />
        </label>
        <div class="flex gap-2">
          <Button size="sm" @click="onSaveSdk">Save</Button>
          <Button size="sm" variant="outline" @click="onTest">Test connection</Button>
        </div>
      </CardContent>
    </Card>
    <Card>
      <CardHeader>
        <CardTitle>Run startup</CardTitle>
        <CardDescription>Register a Windows logon task for the API (and OpenRGB if a path is set).</CardDescription>
      </CardHeader>
      <CardContent class="space-y-3">
        <label class="flex items-center gap-2 text-sm">
          <input v-model="runStartup" type="checkbox" />
          Run at logon
        </label>
        <label class="block space-y-1 text-sm">
          <span>OpenRGB executable (optional)</span>
          <Input v-model="exePath" placeholder="C:\Program Files\OpenRGB\OpenRGB.exe" />
        </label>
        <Button size="sm" @click="onSaveStartup">Save</Button>
      </CardContent>
    </Card>
    <Card>
      <CardHeader>
        <CardTitle>Idle</CardTitle>
        <CardDescription>
          You must set both fields: how long the PC sits unused (time-of-idle), and which mode to apply. Leave both empty to disable idle.
        </CardDescription>
      </CardHeader>
      <CardContent class="space-y-3">
        <label class="block space-y-1 text-sm">
          <span>Time of idle (minutes)</span>
          <Input v-model="idleMinutesStr" type="number" min="1" placeholder="Required with mode" />
        </label>
        <label class="block space-y-1 text-sm">
          <span>Idle mode</span>
          <select v-model="idleModeId" class="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
            <option v-for="opt in modeOptions" :key="opt.id || 'none'" :value="opt.id">{{ opt.name }}</option>
          </select>
        </label>
        <Button size="sm" @click="onSaveIdle">Save</Button>
      </CardContent>
    </Card>
    <Card>
      <CardHeader>
        <CardTitle>Backlight</CardTitle>
        <CardDescription>Scales LED brightness from 0 to 100.</CardDescription>
      </CardHeader>
      <CardContent class="space-y-3">
        <label class="block space-y-1 text-sm">
          <span>{{ backlight }}</span>
          <input v-model.number="backlight" type="range" min="0" max="100" class="w-full" />
        </label>
        <Button size="sm" @click="onSaveBacklight">Save</Button>
      </CardContent>
    </Card>
  </div>
</template>
