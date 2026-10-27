import { useEffect, useState } from "react";
import { Link } from "react-router";

import { fetchLotAudit } from "../../services/audit";
import type { AuditStatus } from "../../types/audit";

/**
 * O selo "Histórico íntegro" do comprovante, com o link para a auditoria.
 * Enquanto carrega ou se a verificação falhar, não aparece: o comprovante funciona sem ele.
 */
export function AuditSeal({ lotId }: { lotId: string }) {
  const [status, setStatus] = useState<AuditStatus | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchLotAudit(lotId, controller.signal)
      .then((audit) => {
        if (!controller.signal.aborted) setStatus(audit.status);
      })
      .catch(() => {
        // Sem selo: o erro só esconde a pílula.
      });
    return () => controller.abort();
  }, [lotId]);

  if (!status) return null;

  const isIntact = status === "INTEGRO";
  return (
    <Link to={`/auditoria/${lotId}`}
      className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1 text-[13px] font-semibold hover:opacity-80 ${
        isIntact ? "border-green bg-green-soft text-green" : "border-red bg-red-soft text-red"
      }`}>
      <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6z" />
        {isIntact ? <path d="M9 12l2 2 4-4" /> : <path d="M10 10l4 4M14 10l-4 4" />}
      </svg>
      {isIntact ? "Histórico íntegro" : "Histórico adulterado"}
    </Link>
  );
}
