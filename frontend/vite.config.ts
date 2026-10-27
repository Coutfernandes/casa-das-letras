import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Repassa /api para o Django, como o rewrite da Vercel faz em produção.
    // Para o navegador, front e API ficam no mesmo endereço, e os cookies
    // de sessão e de CSRF funcionam sem configuração extra.
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/media": "http://127.0.0.1:8000",
    },
  },
});
