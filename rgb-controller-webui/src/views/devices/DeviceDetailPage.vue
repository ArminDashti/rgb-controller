<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { fetchDevice, setDeviceMode, type DeviceDetail } from '@/lib/api'

const route = useRoute()
const deviceId = computed(() => Number(route.params.id))
const device = ref<DeviceDetail | null>(null)
const error = ref('')
const message = ref('')

onMounted(async () => {
  try {
    device.value = await fetchDevice(deviceId.value)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Could not load device'
  }
})

async function applyNative(name: string) {
  message.value = ''
  error.value = ''
  try {
    await setDeviceMode(deviceId.value, name)
    message.value = `Applied ${name}`
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Apply failed'
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-4 px-4 py-8">
    <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
    <Card v-if="device">
      <CardHeader>
        <CardTitle>{{ device.name }}</CardTitle>
        <CardDescription>{{ device.type }} · {{ device.led_count }} LEDs · {{ device.active_mode || 'no mode' }}</CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <p v-if="message" class="text-sm text-muted-foreground">{{ message }}</p>
        <div>
          <h2 class="mb-2 text-sm font-medium">Native modes</h2>
          <div class="flex flex-wrap gap-2">
            <Button
              v-for="mode in device.modes"
              :key="mode.id"
              variant="outline"
              size="sm"
              @click="applyNative(mode.name)"
            >
              {{ mode.name }}
            </Button>
          </div>
        </div>
        <div v-if="device.zones.length">
          <h2 class="mb-2 text-sm font-medium">Zones</h2>
          <ul class="space-y-1 text-sm text-muted-foreground">
            <li v-for="zone in device.zones" :key="zone.id">
              {{ zone.name }} · {{ zone.led_count }} LEDs
              <span v-if="zone.matrix"> · matrix {{ zone.matrix.width }}×{{ zone.matrix.height }}</span>
            </li>
          </ul>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
