/** A verificação pública de um lote como a API devolve. Valores em centavos. */

import type { LotPhase } from "./lot";

export type AuditStatus = "INTEGRO" | "ADULTERADO";

export type CheckStatus = "ok" | "fail" | "warn" | "skipped";

export type AuditReason =
  | "sequence_gap"
  | "hash_mismatch"
  | "chain_broken"
  | "anchor_mismatch"
  | "bad_signature"
  | "anchor_rollback"
  | "receipt_mismatch";

export interface AuditLot {
  id: string;
  title: string;
  authors: string[];
  first_publish_year: number | null;
  phase: LotPhase;
  starts_at: string;
  ends_at: string;
  closed_at: string | null;
  bid_count: number;
}

export interface AuditCheck {
  key: string;
  label: string;
  status: CheckStatus;
  note: string;
}

export interface AuditBid {
  sequence: number;
  /** Só o pseudônimo: a auditoria nunca mostra nome nem e-mail. */
  bidder_alias: string;
  amount: number;
  created_at: string;
  prev_hash: string;
  hash: string;
  ok: boolean;
}

export interface LotAudit {
  lot: AuditLot;
  status: AuditStatus;
  reason: AuditReason | null;
  first_broken_sequence: number | null;
  warnings: { code: string; message: string }[];
  /** Sempre as 7 verificações, na mesma ordem. */
  checks: AuditCheck[];
  bids: AuditBid[];
  checked_at: string;
}

export interface PublicKey {
  algorithm: "Ed25519";
  public_key: string;
}
