/** A carteira do licitante como a API devolve. Valores em centavos. */

import type { Lot } from "./lot";

export type WalletEntryKind = "DEPOSIT" | "SETTLEMENT_DEBIT" | "SETTLEMENT_CREDIT";

export interface WalletEntry {
  id: string;
  kind: WalletEntryKind;
  amount: number;
  lot_title: string | null;
  created_at: string;
}

export interface Wallet {
  total: number;
  committed: number;
  available: number;
  committed_lots: Lot[];
  entries: WalletEntry[];
}
