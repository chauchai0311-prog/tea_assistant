import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Vercel / Netlify: base = '/'.
// Для GitHub Pages project-site замените на '/<repo-name>/'.
export default defineConfig({
  base: '/',
  plugins: [react()],
})
