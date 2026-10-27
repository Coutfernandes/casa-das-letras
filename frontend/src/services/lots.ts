/** Chamadas da API de lotes: vitrine, detalhe e painel do leiloeiro. */

import type { DashboardResponse, Lot, NewLot, ShowcaseFilters, ShowcaseResponse } from "../types/lot";
import { apiRequest, withQuery } from "./api";

export function fetchShowcase(filters: ShowcaseFilters, signal?: AbortSignal) {
  const path = withQuery("/api/lots/", {
    phase: filters.phase,
    q: filters.q,
    min_price: filters.min_price,
    max_price: filters.max_price,
  });
  return apiRequest<ShowcaseResponse>(path, { signal });
}

export function fetchLot(lotId: string, signal?: AbortSignal) {
  return apiRequest<Lot>(`/api/lots/${lotId}/`, { signal });
}

export function fetchDashboard(signal?: AbortSignal) {
  return apiRequest<DashboardResponse>("/api/auctioneer/lots/", { signal });
}

export function createLot(newLot: NewLot) {
  return apiRequest<Lot>("/api/auctioneer/lots/", { method: "POST", body: newLot });
}

export function cancelLot(lotId: string) {
  return apiRequest<Lot>(`/api/auctioneer/lots/${lotId}/cancel/`, { method: "POST" });
}
