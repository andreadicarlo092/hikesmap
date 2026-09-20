import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],

  optimizeDeps: {
    include: ['maplibre-gl', 'chart.js', 'pmtiles']
  },

  ssr: {
    // maplibre-gl and pmtiles are browser-only: exclude from SSR bundle
    noExternal: ['chart.js'],
    external: ['maplibre-gl', 'pmtiles']
  },

  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          maplibre: ['maplibre-gl'],
          chart: ['chart.js']
        }
      }
    }
  }
});
