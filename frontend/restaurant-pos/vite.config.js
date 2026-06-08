import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  base: '/restoran/',
  build: {
    outDir: path.resolve(__dirname, '../../restaurant/static/restaurant-spa'),
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/restoran/api': 'http://127.0.0.1:8000',
      '/media': 'http://127.0.0.1:8000',
      '/w': 'http://127.0.0.1:8000',
      '/giris': 'http://127.0.0.1:8000',
      '/kayit': 'http://127.0.0.1:8000',
      '/yonetim': 'http://127.0.0.1:8000',
    },
  },
})
