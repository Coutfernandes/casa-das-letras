/** Os lotes em que o licitante deu lance e os que ele venceu. */

import type { MyBidsResponse } from "../types/myBids";
import { apiRequest } from "./api";

export function fetchMyBids(signal?: AbortSignal) {
  return apiRequest<MyBidsResponse>("/api/me/bids/", { signal });
}
