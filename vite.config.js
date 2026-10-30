import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// GitHub Pages project site: https://<user>.github.io/tea_assistant/
// Для Vercel / Netlify с корнем домена верните base: '/'
export default defineConfig({
  base: '/tea_assistant/',
  plugins: [react()],
})
