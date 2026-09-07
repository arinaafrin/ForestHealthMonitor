import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite bundles and code-splits automatically per lazy-loaded route (see App.jsx),
// so pages the user hasn't visited yet aren't downloaded.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Intercepts any frontend request starting with '/api'
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Removes '/api' from the URL before sending it to FastAPI
        rewrite: (path) => path.replace(/^\/api/, ''), 
      },
    },
  },
});
