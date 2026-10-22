import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The GUI talks to the local Python server (`uv run python -m server`, port 8000)
// over one WebSocket at /ws, which the dev server passes through.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/ws": { target: "ws://127.0.0.1:8000", ws: true },
    },
  },
});
