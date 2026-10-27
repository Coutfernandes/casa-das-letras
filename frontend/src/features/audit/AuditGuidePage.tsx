import { Link } from "react-router";

import { AuditMethod } from "./AuditMethod";

/** A rota pública /auditoria: explica a verificação para quem chega sem um lote escolhido. */
export function AuditGuidePage() {
  return (
    <div className="mx-auto flex max-w-190 flex-col gap-6">
      <div>
        <p className="mb-2 text-[13px] tracking-[0.12em] text-muted uppercase">Auditoria</p>
        <h1 className="font-serif text-[40px] leading-tight font-bold">Como funciona a auditoria</h1>
      </div>

      {/* Um bloco comum em volta: o AuditMethod cresce como coluna quando está dentro de um flex. */}
      <div>
        <AuditMethod />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4 rounded-md border border-line bg-surface px-5 py-4">
        <p className="text-[15px]">
          Para auditar um lote, abra qualquer lote da vitrine e clique em Auditar histórico.
        </p>
        <Link to="/"
          className="flex h-11 items-center rounded-md bg-gold-dark px-5 text-[15px] font-semibold text-paper hover:opacity-90">
          Ir para a vitrine
        </Link>
      </div>
    </div>
  );
}
