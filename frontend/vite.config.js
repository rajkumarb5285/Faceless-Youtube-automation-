import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3001,
    host: true,
    proxy: {
      '/jobs': 'http://127.0.0.1:8000',
      '/channels': 'http://127.0.0.1:8000',
      '/calendar': 'http://127.0.0.1:8000',
      '/kill-switch': 'http://127.0.0.1:8000',
      '/media': 'http://127.0.0.1:8000'
    }
  }
});
