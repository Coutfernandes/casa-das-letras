import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";

import { ApiError } from "../../services/api";
import { fetchLotAudit } from "../../services/audit";
import type { LotAudit } from "../../types/audit";
import { lotSituation } from "../../utils/audit";
import { formatClock } from "../../utils/dates";
import { bookByline } from "../../utils/lots";
import { AuditBidsTable } from "./AuditBidsTable";
import { AuditChecks } from "./AuditChecks";
import { AuditMethod } from "./AuditMethod";
import { AuditVerdict } from "./AuditVerdict";

type Failure = "notFound" | "tooMany" | "other";
type Loaded = { version: number; audit: LotAudit };
type Failed = { version: number; failure: Failure };

function failureOf(error: unknown): Failure {
  if (error instanceof ApiError && error.status === 404) return "notFound";
  if (error instanceof ApiError && error.status === 429) return "tooMany";
  return "other";
}

/** A rota pública /auditoria/:lotId. A chave recomeça do zero quando o lote muda. */
export function AuditPage() {
  const { lotId = "" } = useParams();
  return <AuditView key={lotId} lotId={lotId} />;
}

function AuditView({ lotId }: { lotId: string }) {
  const [version, setVersion] = useState(0);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [failed, setFailed] = useState<Failed | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchLotAudit(lotId, controller.signal)
      .then((audit) => {
        if (!controller.signal.aborted) setLoaded({ version, audit });
      })
      .catch((error) => {
        if (!controller.signal.aborted) setFailed({ version, failure: failureOf(error) });
      });
    return () => controller.abort();
  }, [lotId, version]);

  // O resultado antigo continua na tela enquanto o novo não chega: nada pisca para "carregando".
  const audit = loaded?.audit;
  const failure = failed?.version === version ? failed.failure : null;
  const isChecking = loaded?.version !== version && failure === null;

  if (failure === "notFound") {
    return (
      <section className="flex flex-col items-start gap-3">
        <h1 className="font-serif text-4xl font-bold">Lote não encontrado.</h1>
        <p className="text-muted">Confira se o endereço foi copiado inteiro.</p>
        <Link to="/" className="font-semibold text-gold-dark hover:text-ink">Ir para a vitrine</Link>
      </section>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {audit && (
        <>
          <header>
            <p className="mb-2 text-[13px] tracking-[0.12em] text-muted uppercase">Auditoria do lote</p>
            <h1 className="font-serif text-[40px] leading-tight font-bold">{audit.lot.title}</h1>
            <p className="mt-1 text-muted">
              {bookByline({ ...audit.lot, edition_count: null })} · {lotSituation(audit.lot)}
            </p>
          </header>

          <div className="flex flex-wrap items-center justify-between gap-4 rounded-md border border-line bg-surface px-5 py-4">
            <p className="max-w-160 text-[15px] text-muted">
              Qualquer pessoa pode abrir esta página, sem login. A verificação é recalculada no servidor a cada
              acesso e vale para lotes ao vivo, agendados e encerrados.
            </p>
            <div className="flex flex-wrap items-center gap-4">
              <p className="text-sm text-muted">
                Verificado às <span className="font-mono text-ink">{formatClock(audit.checked_at)}</span>
              </p>
              <button type="button" disabled={isChecking} onClick={() => setVersion((current) => current + 1)}
                className="h-10 rounded-md border border-line px-4 font-semibold hover:bg-paper disabled:cursor-not-allowed disabled:opacity-60">
                {isChecking ? "Verificando…" : "Verificar novamente"}
              </button>
            </div>
          </div>
        </>
      )}

      {failure === "tooMany" && (
        <p role="alert" className="rounded-md border border-red bg-red-soft px-4 py-3">
          Muitas verificações em pouco tempo. Espere um minuto e tente de novo.
        </p>
      )}

      {failure === "other" && (
        <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-red bg-red-soft px-4 py-3">
          <p>Não foi possível verificar o histórico. Confira a sua conexão e tente de novo.</p>
          <button type="button" onClick={() => setVersion((current) => current + 1)}
            className="h-10 rounded-md border border-line bg-surface px-4 font-semibold">
            Tentar de novo
          </button>
        </div>
      )}

      {/* Fica sempre na página: o leitor de tela anuncia o que mudar aqui dentro. */}
      <div role="status" aria-live="polite" aria-atomic="true">
        {audit ? (
          <>
            <AuditVerdict audit={audit} />
            <span className="sr-only">Verificado às {formatClock(audit.checked_at)}.</span>
          </>
        ) : (
          failure === null && (
            <p className="rounded-md border border-line bg-surface px-6 py-10 text-center text-muted">
              Verificando o histórico…
            </p>
          )
        )}
      </div>

      {audit && (
        <>
          <div className="flex flex-wrap items-start gap-6">
            <AuditChecks checks={audit.checks} />
            <AuditMethod />
          </div>
          <AuditBidsTable bids={audit.bids} />
        </>
      )}
    </div>
  );
}
