/** "Meus arremates" como a API devolve (GET /api/me/bids/). Valores em centavos. */

import type { Lot } from "./lot";

/** Um lote aberto em que a pessoa deu lance. */
export interface MyOpenBid {
  lot: Lot;
  my_max_bid: number;
  winning: boolean;
}

/** Um lote que a pessoa venceu, com o token do comprovante público. */
export interface MyWonLot {
  lot: Lot;
  final_price: number;
  closed_at: string;
  bid_count: number;
  receipt_token: string;
}

export interface MyBidsResponse {
  bids: MyOpenBid[];
  won: MyWonLot[];
  counts: { bids: number; won: number };
}
