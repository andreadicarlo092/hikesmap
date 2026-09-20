import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),

  kit: {
    adapter: adapter(),
    // Prerendering disabled globally: the map is fully client-side.
    // Individual SSR pages (trail detail) are handled per-route.
    prerender: {
      handleMissingId: 'warn',
      entries: []
    }
  }
};

export default config;
