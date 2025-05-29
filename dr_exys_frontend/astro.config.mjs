import { defineConfig } from 'astro/config';
import react from '@astrojs/react';

export default defineConfig({
  integrations: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000
  },
  vite: {
    server: {
      host: '0.0.0.0',
      allowedHosts: ['app.doctorexys.com.br', 'localhost', '192.168.1.4']
    }
  },
  output: 'static'
});