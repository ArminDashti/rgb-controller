<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  applyMode,
  deleteCustomMode,
  fetchModes,
  type CustomMode,
  type PredefinedMode,
} from '@/lib/api'

const predefined = ref<PredefinedMode[]>([])
const custom = ref<CustomMode[]>([])
const color = ref('#00a3e0')
const speed = ref(50)
const brightness = ref(100)
const error = ref('')
const message = ref('')

onMounted(async () => {
  try {
    const data = await fetchModes()
    predefined.value = data.predefined
    custom.value = data.custom
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Could not load modes'
  }
})

async function onApply(modeId: string) {
  error.value = ''
  message.value = ''
  try {
    await applyMode({
      mode_id: modeId,
      color: color.value,
      speed: speed.value,
      brightness: brightness.value,
    })
    message.value = 'Applied'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Apply failed'
  }
}

async function onDelete(id: string) {
  await deleteCustomMode(id)
  custom.value = custom.value.filter((item) => item.id !== id)
}
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-6 px-4 py-8">
    <h1 class="text-2xl font-semibold tracking-tight">Modes</h1>
    <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
    <p v-if="message" class="text-sm text-muted-foreground">{{ message }}</p>
    <Card>
      <CardHeader>
        <CardTitle>Adjustment</CardTitle>
        <CardDescription>Color, speed, and brightness used when you apply a mode.</CardDescription>
      </CardHeader>
      <CardContent class="grid gap-4 sm:grid-cols-3">
        <label class="space-y-1 text-sm">
          <span>Color</span>
          <input v-model="color" type="color" class="h-9 w-full cursor-pointer rounded-md border border-input bg-background" />
        </label>
        <label class="space-y-1 text-sm">
          <span>Speed {{ speed }}</span>
          <input v-model.number="speed" type="range" min="0" max="100" class="w-full" />
        </label>
        <label class="space-y-1 text-sm">
          <span>Brightness {{ brightness }}</span>
          <input v-model.number="brightness" type="range" min="0" max="100" class="w-full" />
        </label>
      </CardContent>
    </Card>
    <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <Card v-for="mode in predefined" :key="mode.id">
        <CardHeader>
          <CardTitle>{{ mode.name }}</CardTitle>
          <CardDescription>{{ mode.adjustments.join(', ') || 'no extra controls' }}</CardDescription>
        </CardHeader>
        <CardContent>
          <Button size="sm" @click="onApply(mode.id)">Apply</Button>
        </CardContent>
      </Card>
      <Card v-for="mode in custom" :key="mode.id">
        <CardHeader>
          <CardTitle>{{ mode.name }}</CardTitle>
          <CardDescription>{{ mode.kind }}</CardDescription>
        </CardHeader>
        <CardContent class="flex gap-2">
          <Button size="sm" @click="onApply(mode.id)">Apply</Button>
          <Button size="sm" variant="outline" @click="onDelete(mode.id)">Delete</Button>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
