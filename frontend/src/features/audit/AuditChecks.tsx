import type { AuditCheck } from "../../types/audit";
import { CHECK_MARKS } from "../../utils/audit";

/** As 7 verificações, cada uma com o círculo do resultado e a explicação do servidor. */
export function AuditChecks({ checks }: { checks: AuditCheck[] }) {
  return (
    <section className="flex min-w-0 flex-[1_1_380px] flex-col gap-4 rounded-md border border-line bg-surface p-5">
      <h2 className="font-serif text-[22px] font-semibold">Verificações</h2>

      <ol className="flex flex-col gap-3.5">
        {checks.map((check) => {
          const mark = CHECK_MARKS[check.status];
          return (
            <li key={check.key} className="flex items-start gap-3">
              {/* O sinal é só visual; o leitor de tela ouve o texto do sr-only. */}
              <span aria-hidden="true"
                className={`mt-0.5 flex size-5.5 shrink-0 items-center justify-center rounded-full text-[13px] font-bold text-paper ${mark.background}`}>
                {mark.sign}
              </span>
              <div className="flex min-w-0 flex-col gap-0.5">
                <p className="font-semibold">
                  {check.label}
                  <span className="sr-only">: {mark.label}.</span>
                </p>
                <p className={`text-sm ${check.status === "fail" ? "text-red" : "text-muted"}`}>{check.note}</p>
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
