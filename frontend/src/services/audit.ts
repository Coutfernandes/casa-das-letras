/** A auditoria pública dos lotes e a chave que confere as assinaturas. Não precisa de login. */

import type { LotAudit, PublicKey } from "../types/audit";
import { apiRequest } from "./api";

export function fetchLotAudit(lotId: string, signal?: AbortSignal) {
  return apiRequest<LotAudit>(`/api/audit/lots/${encodeURIComponent(lotId)}/`, { signal });
}

export function fetchPublicKey(signal?: AbortSignal) {
  return apiRequest<PublicKey>("/api/audit/public-key/", { signal });
}
