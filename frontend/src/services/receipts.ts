/** O comprovante público de arremate. Não precisa de login. */

import type { Receipt } from "../types/receipt";
import { apiRequest } from "./api";

export function fetchReceipt(token: string, signal?: AbortSignal) {
  return apiRequest<Receipt>(`/api/receipts/${encodeURIComponent(token)}/`, { signal });
}
