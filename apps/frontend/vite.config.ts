// TanStack Start + Vite config for MoneyOS frontend.
import { defineConfig } from "vite";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  resolve: {
    tsconfigPaths: true,
  },
  plugins: [tailwindcss(), tanstackStart()],
  server: {
    port: 3000,
  },
});
