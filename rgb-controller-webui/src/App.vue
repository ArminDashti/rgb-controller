<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import AppFooter from '@/components/AppFooter.vue'
import { Button } from '@/components/ui/button'
import { getTheme, toggleTheme, type Theme } from '@/lib/theme'

const theme = ref<Theme>(getTheme())

const navLinkClass =
  'rounded-md px-2.5 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground'
const navLinkActiveClass = 'bg-muted text-foreground'

function syncTheme() {
  theme.value = getTheme()
}

function onToggleTheme() {
  theme.value = toggleTheme()
}

let themeObserver: MutationObserver | null = null

onMounted(() => {
  themeObserver = new MutationObserver(syncTheme)
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class'],
  })
})

onBeforeUnmount(() => {
  themeObserver?.disconnect()
  themeObserver = null
})
</script>

<template>
  <div class="flex h-full w-full flex-col bg-background text-foreground">
    <header
      class="sticky top-0 z-40 flex shrink-0 items-center justify-between gap-4 border-b border-border/80 bg-background/95 px-4 py-3.5 backdrop-blur supports-[backdrop-filter]:bg-background/80"
    >
      <nav class="flex min-w-0 flex-wrap items-center gap-1 sm:gap-1.5" aria-label="Main">
        <RouterLink
          to="/devices"
          class="mr-2 flex shrink-0 items-center gap-2 text-base font-semibold tracking-tight text-foreground"
        >
          <span
            class="inline-flex h-8 w-8 items-center justify-center rounded-md border border-dashed border-muted-foreground/50 bg-muted/40 text-[10px] font-medium uppercase tracking-wide text-muted-foreground"
            aria-label="RGB Controller"
            role="img"
          >
            RGB
          </span>
          <span>RGB Controller</span>
        </RouterLink>
        <RouterLink :class="navLinkClass" :active-class="navLinkActiveClass" to="/devices">Devices</RouterLink>
        <RouterLink :class="navLinkClass" :active-class="navLinkActiveClass" to="/modes">Modes</RouterLink>
        <RouterLink :class="navLinkClass" :active-class="navLinkActiveClass" to="/create-mode">Create-mode</RouterLink>
        <RouterLink :class="navLinkClass" :active-class="navLinkActiveClass" to="/settings">Settings</RouterLink>
      </nav>
      <div class="flex shrink-0 items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          :aria-label="theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'"
          @click="onToggleTheme"
        >
          {{ theme === 'dark' ? 'Light' : 'Dark' }}
        </Button>
      </div>
    </header>
    <main class="min-h-0 flex-1 overflow-auto">
      <RouterView />
    </main>
    <AppFooter />
  </div>
</template>
