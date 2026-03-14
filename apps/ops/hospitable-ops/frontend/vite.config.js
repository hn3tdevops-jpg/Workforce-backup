import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    }
  },
  preview: {
    port: 4173,
    host: '0.0.0.0',
    allowedHosts: [
      'localhost',
      '4173-i54x7ylxa1lxvxe2d686r-bfc900df.us2.manus.computer',
      '.manus.computer',
    ],
  }
})
