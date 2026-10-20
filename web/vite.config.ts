import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base relativa: funciona em https://lubra-lucas.github.io/busca-leads/
export default defineConfig({
  base: './',
  plugins: [react()],
})
