import { createApp } from 'vue'
import { registerSW } from 'virtual:pwa-register'
import App from './App.vue'
import router from './router'
import { initTheme } from './lib/theme'
import './assets/index.css'

registerSW({ immediate: true })
initTheme()
createApp(App).use(router).mount('#app')
