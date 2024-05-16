import { fileURLToPath } from "node:url";
import { dirname } from "path";

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const projectRoot = dirname(fileURLToPath(import.meta.url));

// https://vitejs.dev/config/
export default defineConfig(({ isSsrBuild }) => ({
  plugins: [react()],
  resolve: {
    alias: {
      "@": `${projectRoot}/ui`,
    },
  },
  build: {
    manifest: isSsrBuild ? false : true,
    outDir: isSsrBuild ? "dist/server" : "dist/client",
    rollupOptions: {
      input: isSsrBuild ? "./ui/entry-server.tsx" : "./ui/entry-client.tsx",
    },
  },
}));
