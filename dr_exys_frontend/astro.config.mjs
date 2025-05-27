import { defineConfig } from 'astro/config';
import react from '@astrojs/react';

export default defineConfig({
  integrations: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000
  },
  output: 'static'
});