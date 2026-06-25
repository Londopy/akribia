import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// `base` is "/" for local dev and the Tauri desktop build (assets served from
// the app root), and "/akribia/" for the GitHub Pages deploy (set via the
// AKRIBIA_BASE env var in .github/workflows/pages.yml).
export default defineConfig({
  base: process.env.AKRIBIA_BASE ?? "/",
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
  clearScreen: false,
  server: { port: 5173, strictPort: true },
});
