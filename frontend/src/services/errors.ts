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