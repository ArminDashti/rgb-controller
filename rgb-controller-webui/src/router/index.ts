import { createRouter, createWebHistory } from 'vue-router'
import DevicesPage from '@/views/devices/DevicesPage.vue'
import DeviceDetailPage from '@/views/devices/DeviceDetailPage.vue'
import ModesPage from '@/views/modes/ModesPage.vue'
import CreateModePage from '@/views/create-mode/CreateModePage.vue'
import SettingsPage from '@/views/settings/SettingsPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/devices' },
    { path: '/devices', name: 'devices', component: DevicesPage },
    { path: '/devices/:id', name: 'device-detail', component: DeviceDetailPage },
    { path: '/modes', name: 'modes', component: ModesPage },
    { path: '/create-mode', name: 'create-mode', component: CreateModePage },
    { path: '/settings', name: 'settings', component: SettingsPage },
  ],
})

export default router
