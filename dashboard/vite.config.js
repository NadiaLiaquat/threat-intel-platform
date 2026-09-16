import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    host: true,
    // Local `npm run dev` proxies /api to the backend directly; in the
    // Docker Compose stack, nginx does the same job in front of the built
    // static files (see dashboard/nginx.conf) — the app always just calls
    // relative /api/... paths either way.
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
