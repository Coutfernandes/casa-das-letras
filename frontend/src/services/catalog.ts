/** Busca de livros na Open Library, pelo backend. Só para leiloeiros. */

import type { CatalogSearchResponse } from "../types/lot";
import { apiRequest, withQuery } from "./api";

export function searchCatalog(q: string, page = 1, signal?: AbortSignal) {
  return apiRequest<CatalogSearchResponse>(withQuery("/api/catalog/search/", { q, page }), {
    signal,
  });
}
