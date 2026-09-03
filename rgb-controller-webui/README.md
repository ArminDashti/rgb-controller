# rgb-controller-webui

Vue 3 + Vite + Tailwind + shadcn-vue (new-york, slate) + Inter. PWA via `vite-plugin-pwa`.

Controls RGB devices through `rgb-controller-api` (OpenRGB SDK).

## Quick start

```bash
copy .env.example .env
npm install
npm run dev
```

Dev URL: `http://localhost:5182`

API base URL: leave `VITE_API_BASE_URL` empty in `.env` so Vite proxies `/api` and `/health` to `http://127.0.0.1:8132`.

No login. Set OpenRGB SDK host and port on the Settings page.
