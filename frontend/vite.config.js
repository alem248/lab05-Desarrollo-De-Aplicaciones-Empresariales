import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// La SPA corre en el 5173 y la API de Django en el 8000.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
  },
})
