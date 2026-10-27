/// <reference types="vite/client" />

/** As variáveis VITE_* que o código lê. Todas são públicas: vão dentro do JavaScript do site. */
interface ImportMetaEnv {
  /** Endereço do WebSocket em produção, ex.: wss://casa-das-letras.onrender.com. Vazio no desenvolvimento. */
  readonly VITE_WS_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
