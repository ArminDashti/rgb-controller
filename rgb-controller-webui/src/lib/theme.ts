export type Theme = 'light' | 'dark'

const THEME_KEY = 'rgb-controller-theme'

export function getTheme(): Theme {
  const stored = localStorage.getItem(THEME_KEY)
  if (stored === 'light') return 'light'
  return 'dark'
}

export function initTheme(): void {
  applyTheme(getTheme())
}

export function toggleTheme(): Theme {
  const next: Theme = getTheme() === 'dark' ? 'light' : 'dark'
  localStorage.setItem(THEME_KEY, next)
  applyTheme(next)
  return next
}

function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark')
}
