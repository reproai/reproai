import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  base: "/",
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        // multi-page: the landing page and the standalone /changelog/ page
        main: fileURLToPath(new URL("./index.html", import.meta.url)),
        changelog: fileURLToPath(new URL("./changelog/index.html", import.meta.url)),
      },
    },
  },
});
