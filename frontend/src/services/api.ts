/**
 * Cliente da API do backend.
 *
 * Toda requisição passa por aqui: envia o cookie de sessão, coloca o token
 * CSRF nos métodos que alteram dados e transforma erros em ApiError.
 */

const UNSAFE_METHODS = ["POST", "PUT", "PATCH", "DELETE"];

/** Erro de uma resposta da API, com o código e o corpo devolvidos. */
export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, data: unknown) {
    super(`Erro ${status} na API`);
    this.status = status;
    this.data = data;
  }
}

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

type QueryValue = string | number | undefined;

/** Novo: monta "/api/lots/?phase=live&q=machado", ignorando os filtros vazios. */
export function withQuery(path: string, params: Record<string, QueryValue>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  }
  const text = query.toString();
  return text ? `${path}?${text}` : path;
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  /** Novo: permite cancelar a requisição, como quando a pessoa digita outra busca. */
  signal?: AbortSignal;
};

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method ?? "GET";
  const headers: Record<string, string> = { Accept: "application/json" };

  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (UNSAFE_METHODS.includes(method)) {
    const csrfToken = readCookie("csrftoken");
    if (csrfToken) {
      headers["X-CSRFToken"] = csrfToken;
    }
  }

  const response = await fetch(path, {
    method,
    headers,
    credentials: "same-origin",
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    signal: options.signal,
  });

  // 204 (sem conteúdo) não tem corpo para ler.
  const data = response.status === 204 ? null : await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(response.status, data);
  }
  return data as T;
}
