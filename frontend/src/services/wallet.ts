/** Chamadas da carteira do licitante. */

import type { Wallet } from "../types/wallet";
import { apiRequest } from "./api";

export function fetchWallet(signal?: AbortSignal) {
  return apiRequest<Wallet>("/api/wallet/", { signal });
}

export function depositMoney(amount: number) {
  return apiRequest<Wallet>("/api/wallet/deposit/", { method: "POST", body: { amount } });
}
