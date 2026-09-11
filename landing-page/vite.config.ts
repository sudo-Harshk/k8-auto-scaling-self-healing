import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  // GitHub Pages base path. The site is served at
  // https://sudo-Harshk.github.io/k8-auto-scaling-self-healing/ so all
  // asset paths in the production build are prefixed with this string.
  // Local dev (vite dev) is unaffected - it serves from /.
  base: '/k8-auto-scaling-self-healing/',
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom'],
          charts: ['recharts'],
          icons: ['lucide-react'],
          motion: ['framer-motion'],
        },
      },
    },
  },
  server: {
    port: 3000,
  },
})
