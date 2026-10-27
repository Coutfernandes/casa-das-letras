/** Os lances e os eventos da sala do lote como o backend envia. Valores em centavos. */

import type { Lot } from "./lot";

export interface Bid {
  sequence: number;
  amount: number;
  bidder_alias: string;
  created_at: string;
  prev_hash: string;
  hash: string;
}

/** A resposta de um lance aceito (201). */
export interface PlacedBid {
  bid: Bid;
  lot: Lot;
  extended: boolean;
}

/** Todo evento do WebSocket traz o horário do servidor, para acertar o relógio. */
type RoomEventBase = { server_now: string };

export type RoomEvent = RoomEventBase &
  (
    | { type: "lot.snapshot"; lot: Lot; bids: Bid[]; viewer: { alias: string } | null }
    | { type: "bid.accepted"; bid: Bid; lot: Lot }
    | { type: "lot.extended"; ends_at: string; original_ends_at: string }
    | { type: "lot.cancelled"; reason: string; lot: Lot }
    | { type: "lot.closed"; winner_alias: string | null; final_price: number | null; lot: Lot }
    | { type: "user.outbid"; amount: number; minimum_next_bid: number }
  );
