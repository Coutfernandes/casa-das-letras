/** Chamadas de lances na sala do lote. */

import type { PlacedBid } from "../types/bid";
import { apiRequest } from "./api";

export function placeBid(lotId: string, amount: number) {
  return apiRequest<PlacedBid>(`/api/lots/${lotId}/bids/`, { method: "POST", body: { amount } });
}
