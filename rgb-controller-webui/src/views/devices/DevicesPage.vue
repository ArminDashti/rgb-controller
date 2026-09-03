<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { colorCss, fetchDevices, type DeviceSummary } from '@/lib/api'

const devices = ref<DeviceSummary[]>([])
const error = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    const data = await fetchDevices()
    devices.value = data.devices
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Could not load devices'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-4 px-4 py-8">
    <h1 class="text-2xl font-semibold tracking-tight">Devices</h1>
    <p v-if="loading" class="text-sm text-muted-foreground">Loading OpenRGB devices…</p>
    <p v-else-if="error" class="text-sm text-red-500">{{ error }}</p>
    <p v-else-if="!devices.length" class="text-sm text-muted-foreground">
      No devices. Open OpenRGB with SDK Server enabled, then set host and port on Settings.
    </p>
    <div v-else class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <RouterLink v-for="item in devices" :key="item.id" :to="`/devices/${item.id}`">
        <Card class="h-full transition-colors hover:bg-muted/40">
          <CardHeader>
            <CardTitle>{{ item.name }}</CardTitle>
            <CardDescription>{{ item.type }} · {{ item.led_count }} LEDs</CardDescription>
          </CardHeader>
          <CardContent class="space-y-2">
            <p class="text-sm text-muted-foreground">Mode: {{ item.active_mode || '—' }}</p>
            <div class="flex gap-1">
              <span
                v-for="(c, idx) in item.colors.slice(0, 6)"
                :key="idx"
                class="h-4 w-4 rounded-sm border border-border"
                :style="{ background: colorCss(c) }"
              />
            </div>
          </CardContent>
        </Card>
      </RouterLink>
    </div>
  </div>
</template>
