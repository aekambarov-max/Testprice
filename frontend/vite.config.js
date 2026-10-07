import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => ({
  plugins: [vue()],
  // Демо-сборка: один JS-файл без чанков, относительные пути — для публикации статической страницей.
  ...(mode === 'demo' ? {
    base: './',
    build: { outDir: 'dist-demo', cssCodeSplit: false, rollupOptions: { output: { inlineDynamicImports: true } } },
  } : {}),
  server: {
    port: 5173,
    proxy: { '/api': { target: process.env.API_TARGET || 'http://localhost:8000', changeOrigin: false } },
  },
  test: { environment: 'jsdom', setupFiles: ['./tests/setup.js'] },
}))
