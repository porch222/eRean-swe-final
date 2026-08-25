import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    // 0.0.0.0 so the dev server is reachable from outside the container.
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    // Accept whatever hostname or IP the browser used to get here.
    allowedHosts: true,
    // The app runs in the user's browser, which cannot resolve the container's
    // 127.0.0.1. Proxying means the browser only ever talks to this port and
    // Vite forwards API calls to Django inside the container — so only port
    // 3000 needs to be published.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/django-admin': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
