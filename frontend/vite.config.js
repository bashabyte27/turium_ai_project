import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// During development the React app runs on :5173 and the API on :8000.
// The proxy forwards these paths to the API, so the frontend can just call "/items".
const api = 'http://localhost:8000'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/ingest': api,
      '/items': api,
      '/query': api,
    },
  },
})
