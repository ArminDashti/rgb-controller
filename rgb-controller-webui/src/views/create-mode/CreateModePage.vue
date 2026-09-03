<script setup lang="ts">
import { computed, ref } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { applyMode, createCustomMode } from '@/lib/api'

const GRID = 8
const symbolName = ref('Symbol')
const textName = ref('Text')
const textValue = ref('RGB')
const color = ref('#00a3e0')
const brightness = ref(100)
const speed = ref(40)
const direction = ref('left')
const animate = ref(false)
const pixels = ref<number[][]>(Array.from({ length: GRID }, () => Array.from({ length: GRID }, () => 0)))
const message = ref('')
const error = ref('')

function toggleCell(y: number, x: number) {
  const next = pixels.value.map((row) => row.slice())
  next[y][x] = next[y][x] ? 0 : 1
  pixels.value = next
}

const payloadSymbol = computed(() => ({
  pixels: pixels.value,
  animate: animate.value,
  speed: speed.value,
}))

async function saveSymbol() {
  error.value = ''
  try {
    const mode = await createCustomMode({
      kind: 'symbol',
      name: symbolName.value,
      payload: payloadSymbol.value,
    })
    message.value = `Saved ${mode.name}`
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Save failed'
  }
}

async function applySymbol() {
  const mode = await createCustomMode({
    kind: 'symbol',
    name: symbolName.value,
    payload: payloadSymbol.value,
  })
  await applyMode({ mode_id: mode.id, color: color.value, brightness: brightness.value, speed: speed.value })
  message.value = 'Applied symbol'
}

async function saveText() {
  error.value = ''
  try {
    const mode = await createCustomMode({
      kind: 'text',
      name: textName.value,
      payload: { text: textValue.value, direction: direction.value, speed: speed.value },
    })
    message.value = `Saved ${mode.name}`
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Save failed'
  }
}

async function applyText() {
  const mode = await createCustomMode({
    kind: 'text',
    name: textName.value,
    payload: { text: textValue.value, direction: direction.value, speed: speed.value },
  })
  await applyMode({ mode_id: mode.id, color: color.value, brightness: brightness.value, speed: speed.value })
  message.value = 'Applied text'
}
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-6 px-4 py-8">
    <h1 class="text-2xl font-semibold tracking-tight">Create-mode</h1>
    <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
    <p v-if="message" class="text-sm text-muted-foreground">{{ message }}</p>
    <div class="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Display symbol</CardTitle>
          <CardDescription>Click cells, then save or apply. Uses the device matrix when OpenRGB provides one.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <label class="block space-y-1 text-sm">
            <span>Name</span>
            <Input v-model="symbolName" />
          </label>
          <div class="inline-grid gap-1" :style="{ gridTemplateColumns: `repeat(${GRID}, 1.5rem)` }">
            <template v-for="(row, y) in pixels" :key="y">
              <button
                v-for="(cell, x) in row"
                :key="`${y}-${x}`"
                type="button"
                class="h-6 w-6 rounded-sm border border-border"
                :class="cell ? 'bg-primary' : 'bg-muted'"
                :aria-label="`Cell ${x + 1},${y + 1}`"
                @click="toggleCell(y, x)"
              />
            </template>
          </div>
          <label class="flex items-center gap-2 text-sm">
            <input v-model="animate" type="checkbox" />
            Pulse animation
          </label>
          <div class="flex gap-2">
            <Button size="sm" @click="saveSymbol">Save</Button>
            <Button size="sm" variant="outline" @click="applySymbol">Apply</Button>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Display texts</CardTitle>
          <CardDescription>Text is drawn onto LEDs and can scroll.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <label class="block space-y-1 text-sm">
            <span>Name</span>
            <Input v-model="textName" />
          </label>
          <label class="block space-y-1 text-sm">
            <span>Text</span>
            <Input v-model="textValue" />
          </label>
          <label class="block space-y-1 text-sm">
            <span>Direction</span>
            <select v-model="direction" class="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="left">Left</option>
              <option value="right">Right</option>
            </select>
          </label>
          <div class="flex gap-2">
            <Button size="sm" @click="saveText">Save</Button>
            <Button size="sm" variant="outline" @click="applyText">Apply</Button>
          </div>
        </CardContent>
      </Card>
    </div>
    <Card>
      <CardHeader>
        <CardTitle>Shared adjustment</CardTitle>
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
  </div>
</template>
