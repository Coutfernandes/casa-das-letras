import type { LotAudit } from "../../types/audit";
import { intactSummary, tamperedSummary } from "../../utils/audit";

/** A caixa verde ou vermelha com o resultado, e os avisos logo abaixo. */
export function AuditVerdict({ audit }: { audit: LotAudit }) {
  const isIntact = audit.status === "INTEGRO";

  return (
    <div className="flex flex-col gap-2">
      <div className={`rounded-md border px-5 py-4.5 ${isIntact ? "border-green bg-green-soft" : "border-red bg-red-soft"}`}>
        <p className={`font-serif text-[26px] leading-tight font-semibold ${isIntact ? "text-green" : "text-red"}`}>
          {isIntact ? "Histórico íntegro" : "Histórico adulterado"}
        </p>
        <p className="mt-1">{isIntact ? intactSummary(audit.bids.length) : tamperedSummary(audit)}</p>
      </div>

      {audit.warnings.length > 0 && (
        <p className="text-sm text-muted">{audit.warnings.map((warning) => warning.message).join(" ")}</p>
      )}
    </div>
  );
}
