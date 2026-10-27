import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";

import { CopyLinkButton } from "../../components/CopyLinkButton";
import { LotCover } from "../../components/LotCover";
import { ApiError } from "../../services/api";
import { fetchReceipt } from "../../services/receipts";
import type { Receipt } from "../../types/receipt";
import { formatDateTime } from "../../utils/dates";
import { bookByline } from "../../utils/lots";
import { formatCents } from "../../utils/money";
import { receiptUrl } from "../../utils/receipts";
import { AuditSeal } from "./AuditSeal";

type Loaded = { version: number; receipt: Receipt };
type Failed = { version: number; notFound: boolean };

/** A rota pública /comprovante/:token. A chave recomeça do zero quando o token muda. */
export function ReceiptPage() {
  const { token = "" } = useParams();
  return <ReceiptView key={token} token={token} />;
}

function ReceiptView({ token }: { token: string }) {
  const [version, setVersion] = useState(0);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [failed, setFailed] = useState<Failed | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchReceipt(token, controller.signal)
      .then((receipt) => {
        if (!controller.signal.aborted) setLoaded({ version, receipt });
      })
      .catch((error) => {
        if (controller.signal.aborted) return;
        setFailed({ version, notFound: error instanceof ApiError && error.status === 404 });
      });
    return () => controller.abort();
  }, [token, version]);

  const hasFailed = failed?.version === version;

  if (hasFailed && failed.notFound) {
    return (
      <section className="mx-auto flex max-w-190 flex-col items-start gap-3">
        <h1 className="font-serif text-4xl font-bold">Comprovante não encontrado.</h1>
        <p className="text-muted">Confira se o link foi copiado inteiro.</p>
        <Link to="/" className="font-semibold text-gold-dark hover:text-ink">Ir para a vitrine</Link>
      </section>
    );
  }

  if (hasFailed) {
    return (
      <div role="alert" className="mx-auto flex max-w-190 flex-wrap items-center justify-between gap-3 rounded-md border border-red bg-red-soft px-4 py-3">
        <p>Não foi possível carregar o comprovante. Confira a sua conexão e tente de novo.</p>
        <button type="button" onClick={() => setVersion((current) => current + 1)}
          className="h-10 rounded-md border border-line bg-surface px-4 font-semibold">
          Tentar de novo
        </button>
      </div>
    );
  }

  const receipt = loaded?.receipt;
  if (!receipt) {
    return (
      <p className="mx-auto max-w-190 rounded-md border border-line bg-surface px-6 py-10 text-center text-muted">
        Carregando o comprovante…
      </p>
    );
  }

  const facts = [
    { label: "Arrematante", value: receipt.winner_alias, className: "font-semibold" },
    { label: "Valor", value: formatCents(receipt.amount), className: "font-mono text-[26px] font-medium" },
    { label: "Encerrado em", value: formatDateTime(receipt.closed_at) },
    { label: "Lances no lote", value: receipt.bid_count, className: "font-mono" },
    { label: "Leiloeiro", value: receipt.auctioneer_name },
    { label: "Emitido em", value: formatDateTime(receipt.issued_at) },
  ];

  return (
    <div className="mx-auto flex max-w-190 flex-col gap-5">
      <article className="rounded-md border border-line bg-surface shadow-card">
        <header className="flex flex-wrap items-start justify-between gap-4 border-b border-line px-5 py-6 sm:px-8">
          <div className="min-w-0">
            <p className="text-xs font-semibold tracking-[0.14em] text-muted uppercase">Comprovante de arremate</p>
            <h1 className="mt-2 font-serif text-[36px] leading-tight font-bold">{receipt.title}</h1>
            <p className="mt-1 text-muted">{bookByline({ ...receipt, edition_count: null })}</p>
          </div>
          <AuditSeal lotId={receipt.lot_id} />
        </header>

        <div className="flex flex-col gap-6 px-5 py-6 sm:flex-row sm:px-8">
          {/* A API do comprovante não traz a imagem da capa: o LotCover desenha o livro. */}
          <div className="flex justify-center sm:block">
            <LotCover title={receipt.title} authors={receipt.authors} coverUrl={null} />
          </div>

          <div className="flex min-w-0 flex-1 flex-col gap-5">
            <dl className="grid grid-cols-1 gap-x-8 gap-y-4 sm:grid-cols-2">
              {facts.map((fact) => (
                <div key={fact.label} className="flex flex-col gap-0.5">
                  <dt className="text-[13px] text-muted">{fact.label}</dt>
                  <dd className={fact.className}>{fact.value}</dd>
                </div>
              ))}
            </dl>

            <div className="flex flex-col gap-1.5 rounded-md border border-line bg-paper px-4 py-3.5">
              <p className="text-[13px] text-muted">
                Hash do último lance (liga este comprovante à cadeia auditável)
              </p>
              <p className="font-mono text-sm break-all">{receipt.last_bid_hash}</p>
            </div>
          </div>
        </div>

        <footer className="flex flex-wrap gap-3 border-t border-line px-5 py-5 sm:px-8">
          <CopyLinkButton url={receiptUrl(receipt.token)}
            className="h-11 rounded-md bg-gold-dark px-5 text-[15px] font-semibold text-paper hover:opacity-90" />
          <Link to={`/auditoria/${receipt.lot_id}`}
            className="flex h-11 items-center rounded-md border border-line px-5 text-[15px] font-semibold hover:bg-paper">
            Verificar na auditoria
          </Link>
        </footer>
      </article>

      <p className="flex items-start gap-2 text-sm text-muted">
        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
          strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 size-4 shrink-0">
          <rect x="5" y="11" width="14" height="10" rx="2" />
          <path d="M8 11V7a4 4 0 0 1 8 0v4" />
        </svg>
        Este comprovante não mostra nome nem e-mail. O arrematante aparece pelo pseudônimo, o mesmo usado no
        histórico público do lote.
      </p>
    </div>
  );
}
