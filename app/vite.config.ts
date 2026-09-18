import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'
export default defineConfig({ plugins: [react(), tailwindcss()], server: {
    proxy: {
      '/evaluate': { target: 'http://localhost:8000', changeOrigin: true, timeout: 0, proxyTimeout: 0 },
      '/history': { target: 'http://localhost:8000', changeOrigin: true },
      '/stats': { target: 'http://localhost:8000', changeOrigin: true },
      '/health': { target: 'http://localhost:8000', changeOrigin: true },
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  }, resolve: { alias: { '@': new URL('./src', import.meta.url).pathname, 'cn': new URL('./src/lib/utils.ts', import.meta.url).pathname } } })
