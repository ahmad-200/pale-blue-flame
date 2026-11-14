import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// In development, /api goes to the backend (../backend, LangGraph + FastAPI on port 8787). The API key lives there only.
// base './' so the built site works from any folder (GitHub Pages included)
export default defineConfig({
  plugins: [vue()],
  base: './',
  server: { proxy: { '/api': 'http://localhost:8787' } },
})
