/** Os lotes e o catálogo como a API devolve. Valores em dinheiro sempre em centavos. */

export type LotPhase = "SCHEDULED" | "LIVE" | "ENDED" | "CLOSED" | "CANCELLED";

/** As abas da vitrine, no formato do parâmetro ?phase= da API. */
export type ShowcaseTab = "live" | "scheduled" | "finished";

export interface Lot {
  id: string;
  title: string;
  authors: string[];
  first_publish_year: number | null;
  edition_count: number | null;
  cover_url: string | null;
  description: string;
  auctioneer_name: string;
  phase: LotPhase;
  starting_price: number;
  min_increment: number;
  current_price: number | null;
  minimum_next_bid: number;
  bid_count: number;
  leader_alias: string | null;
  starts_at: string;
  ends_at: string;
  original_ends_at: string;
  winner_alias: string | null;
  final_price: number | null;
  closed_at: string | null;
}

export interface ShowcaseFilters {
  phase: ShowcaseTab;
  q?: string;
  min_price?: number;
  max_price?: number;
}

export interface ShowcaseResponse {
  counts: Record<ShowcaseTab, number>;
  results: Lot[];
}

export interface DashboardResponse {
  summary: {
    live: number;
    scheduled: number;
    finished: number;
    total_received: number;
  };
  results: Lot[];
}

export interface CatalogBook {
  work_key: string;
  title: string;
  authors: string[];
  first_publish_year: number | null;
  edition_count: number | null;
  cover_id: number;
  cover_url: string;
}

export interface CatalogSearchResponse {
  results: CatalogBook[];
  is_stale: boolean;
}

/** O que o painel envia para criar um lote. */
export interface NewLot {
  book: Omit<CatalogBook, "cover_url">;
  description: string;
  starting_price: number;
  min_increment: number;
  starts_at: string;
  ends_at: string;
}
