/** Transforma erros da API em uma mensagem por campo, para mostrar nos formulários. */

import { ApiError } from "./api";

/** Mensagem por nome de campo. A chave "form" guarda os erros gerais. */
export type FieldErrors = Record<string, string>;

const GENERIC_ERROR = "Algo deu errado. Tente de novo.";
const NETWORK_ERROR = "Não foi possível falar com o servidor. Tente de novo em instantes.";

// Chaves do DRF que não pertencem a um campo específico.
const GENERAL_KEYS = ["non_field_errors", "detail"];

export function toFieldErrors(error: unknown): FieldErrors {
  if (!(error instanceof ApiError)) {
    return { form: NETWORK_ERROR };
  }
  if (!error.data || typeof error.data !== "object") {
    return { form: GENERIC_ERROR };
  }

  const errors: FieldErrors = {};
  for (const [key, value] of Object.entries(error.data)) {
    const message = Array.isArray(value) ? value[0] : value;
    if (typeof message === "string") {
      errors[GENERAL_KEYS.includes(key) ? "form" : key] = message;
    }
  }
  return Object.keys(errors).length > 0 ? errors : { form: GENERIC_ERROR };
}

/**
 * A mensagem que o backend mandou num erro (o "message" das regras de negócio,
 * ou o "detail" do DRF nos 403 e 404). Sem mensagem, usa a de reserva.
 */
export function apiErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError && typeof error.data === "object" && error.data !== null) {
    const { message, detail } = error.data as { message?: unknown; detail?: unknown };
    if (typeof message === "string") return message;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}
