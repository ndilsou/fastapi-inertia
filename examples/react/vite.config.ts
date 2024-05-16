import { fileURLToPath } from "node:url";
import { dirname } from "path";

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const projectRoot = dirname(fileURLToPath(import.meta.url));

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": `${projectRoot}/ui`,
    },
  },
  build: {
    manifest: true,
    outDir: "dist",
    rollupOptions: {
      input:  "./ui/main.tsx",
    },
  },
});
