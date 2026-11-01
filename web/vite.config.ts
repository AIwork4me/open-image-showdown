import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Base path: GitHub Pages project site serves under /open-image-showdown/.
// Override with --base=/ for local preview or custom domains.
export default defineConfig(({ mode }) => ({
  base: mode === 'local' ? '/' : '/open-image-showdown/',
  plugins: [react()],
  build: {
    outDir: 'dist',
    assetsInlineLimit: 0, // keep gallery images addressable as files
  },
}));
