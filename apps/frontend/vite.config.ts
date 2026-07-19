// TanStack Start + Vite config for MoneyOS frontend.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  resolve: {
    tsconfigPaths: true,
  },
  plugins: [tanstackStart(), react(), tailwindcss()],
  server: {
    port: 3000,
    // Proxy API calls to the backend so the browser talks same-origin
    // (/api/...). Avoids cross-origin (localhost vs 127.0.0.1) CORS blocks.
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
