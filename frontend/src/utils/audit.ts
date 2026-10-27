/** Textos da tela de auditoria: o motivo da falha, a situação do lote e os hashes encurtados. */

import type { AuditLot, AuditReason, CheckStatus, LotAudit } from "../types/audit";
import { formatDateTime } from "./dates";

const REASON_TEXT: Record<AuditReason, string> = {
  sequence_gap: "falta um lance na sequência",
  hash_mismatch: "o hash recalculado não confere com o gravado",
  chain_broken: "o lance não aponta para o hash do anterior",
  anchor_mismatch: "o número de lances ou o último hash não bate com a âncora do lote",
  bad_signature: "a assinatura da âncora não confere com a chave pública",
  anchor_rollback: "o histórico voltou a um estado antigo (a cópia externa tem lances que o banco não tem)",
  receipt_mismatch: "o comprovante não bate com o lote",
};

/** "hash_mismatch" → "o hash recalculado não confere com o gravado" */
export function reasonText(reason: AuditReason | null): string {
  return (reason && REASON_TEXT[reason]) ?? "uma das verificações falhou";
}

/** A frase abaixo do título vermelho: onde a cadeia quebra e por quê. */
export function tamperedSummary(audit: LotAudit): string {
  const why = `${reasonText(audit.reason)} (${audit.reason ?? "desconhecido"})`;
  return audit.first_broken_sequence === null
    ? `Problema encontrado: ${why}.`
    : `A cadeia quebra no lance #${audit.first_broken_sequence}: ${why}.`;
}

/** A frase abaixo do título verde. */
export function intactSummary(bidCount: number): string {
  if (bidCount === 0) return "Nenhum lance registrado ainda. Não há o que adulterar.";
  const bids = bidCount === 1 ? "1 lance verificado" : `${bidCount} lances verificados`;
  return `${bids}. Cadeia de hashes, âncora e assinatura conferem.`;
}

/** "ao vivo, termina em 23/10/2026 às 21:04", "agendado para …", "encerrado em …" ou "cancelado". */
export function lotSituation(lot: AuditLot): string {
  switch (lot.phase) {
    case "LIVE":
      return `ao vivo, termina em ${formatDateTime(lot.ends_at)}`;
    case "SCHEDULED":
      return `agendado para ${formatDateTime(lot.starts_at)}`;
    case "CANCELLED":
      return "cancelado";
    default:
      return `encerrado em ${formatDateTime(lot.closed_at ?? lot.ends_at)}`;
  }
}

/** "c41e9a…9b44": o começo e o fim do hash. O "GENESIS" do primeiro lance fica inteiro. */
export function abbreviateHash(hash: string): string {
  if (hash.length <= 12) return hash;
  return `${hash.slice(0, 6)}…${hash.slice(-4)}`;
}

export type CheckMark = { sign: string; background: string; label: string };

/** O círculo de cada verificação: o sinal, a cor de fundo e o que o leitor de tela fala. */
export const CHECK_MARKS: Record<CheckStatus, CheckMark> = {
  ok: { sign: "✓", background: "bg-green", label: "Confere" },
  fail: { sign: "×", background: "bg-red", label: "Falhou" },
  warn: { sign: "!", background: "bg-gold", label: "Atenção" },
  skipped: { sign: "–", background: "bg-muted", label: "Não se aplica" },
};
